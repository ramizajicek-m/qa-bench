"""readcensus — in a real browser, what each response CARRIED against what the page READ.

The static census (qabench/census.py) failed its acceptance bar on ana-log —
2 of 8 past defects caught, ~150 unexplained reds — because a server that
re-shapes a descriptor into its own API makes "the key is named in the source"
and "the screen uses it" different questions. This asks the second one where it
is decided: at the server→client boundary, per endpoint, at runtime.

HOW. An init script patches `Response.prototype.json` (every fetch in the page,
including the app's own client) to return the parsed body wrapped in a
recursive Proxy. Every key path the body CARRIED is recorded, and every key path
the page's code READ through the proxy. After a journey, per endpoint:

  served, never read   the generatedPassword / fieldsNote / onValueChange shape:
                       the server did its half and nothing on the screen used it
  read, never served   the `applied`/`message` shape: the client reads a key the
                       server does not send, and gets undefined without an error

Paths are normalised: array positions collapse to `[]`, ids and digits in the
URL to `{id}`, the query string is dropped.

WHAT IT CANNOT TELL APART, stated:
  * ENUMERATION. `{...body}`, `Object.keys(body)`, `JSON.stringify(body)` touch
    every key without meaning to use any. A proxy sees the `ownKeys` call, and
    every key of an enumerated object is recorded as `passed` — neither read
    nor unread. A body copied that way before it is used hides its keys; the
    report prints how many keys were passed so the blind area is visible.
  * A KEY READ BY A BRANCH THAT DID NOT RUN is unread tonight. The census is
    only as wide as the journeys that drive it; it reports per endpoint visited.
  * VALUES. It sees that `displayType` was read, not that the `link` case exists.
"""
from __future__ import annotations

import json
import re

INIT_SCRIPT = r"""
(() => {
  if (window.__qaCensus) return;
  const census = window.__qaCensus = {};
  // Keys the runtime asks of any object (React, promises, JSON, devtools) — not the app reading a field.
  const SKIP = new Set(['then', 'toJSON', '$$typeof', 'constructor', 'toString', 'valueOf', 'nodeType', '@@iterator', 'asymmetricMatch', '_reactFragment']);         // endpoint -> {served:{}, read:{}, passed:{}}
  const norm = (u) => {
    try { u = new URL(u, location.href); } catch (e) { return String(u); }
    return u.pathname.split('/').map(s => /^\d+$|^[0-9a-f-]{16,}$/i.test(s) ? '{id}' : s).join('/');
  };
  const bucket = (ep, method) => {
    const k = method + ' ' + ep;
    return census[k] || (census[k] = {served: {}, read: {}, passed: {}});
  };
  const walk = (node, path, b) => {
    if (node === null || typeof node !== 'object') return;
    if (Array.isArray(node)) { node.forEach(v => walk(v, path + '[]', b)); return; }
    for (const k of Object.keys(node)) { const p = path ? path + '.' + k : k; b.served[p] = 1; walk(node[k], p, b); }
  };
  // ONE proxy per object, forever. The first version made a new proxy on every
  // read, so the same row read twice was two different objects: `===`,
  // indexOf, Set membership and React's memo comparisons all broke, and two of
  // ana-log's browser tests failed ONLY with the census attached (2026-09-19).
  // A recorder that changes what it records is not a recorder.
  const proxies = new WeakMap();
  const targets = new WeakMap();                 // proxy -> the plain object behind it
  // The structured-clone algorithm refuses a Proxy (DataCloneError). history
  // state, structuredClone and postMessage clone what the app hands them, so
  // a proxied row passed to navigate(url, {state}) made the navigation fail —
  // ana-log's «הוספה» landed on the card instead of the form, with the census
  // attached only. Unwrap before anything clones.
  const unwrap = (v, seen = new Map()) => {
    if (v === null || typeof v !== 'object') return v;
    const t = targets.get(v) || v;
    if (seen.has(t)) return seen.get(t);
    if (!targets.has(v) && !Array.isArray(t) && Object.getPrototypeOf(t) !== Object.prototype) return v;
    const out = Array.isArray(t) ? [] : {};
    seen.set(t, out);
    for (const k of Object.keys(t)) out[k] = unwrap(t[k], seen);
    return out;
  };
  for (const name of ['pushState', 'replaceState']) {
    const orig = History.prototype[name];
    History.prototype[name] = function (state, ...rest) { return orig.call(this, unwrap(state), ...rest); };
  }
  if (window.structuredClone) {
    const sc = window.structuredClone;
    window.structuredClone = (v, o) => sc(unwrap(v), o);
  }
  const wrap = (node, path, b) => {
    if (node === null || typeof node !== 'object') return node;
    const known = proxies.get(node);
    if (known) return known;
    const made = new Proxy(node, {
      get(t, k, r) {
        const v = Reflect.get(t, k, r);
        if (typeof k !== 'string') return v;
        if (Array.isArray(t)) {
          if (/^\d+$/.test(k)) return wrap(v, path + '[]', b);
          return typeof v === 'function' ? v.bind(r) : v;   // map/filter/length act on the proxy, elements wrap above
        }
        if (SKIP.has(k)) return v;
        const p = path ? path + '.' + k : k;
        b.read[p] = (b.read[p] || 0) + 1;
        return wrap(v, p, b);
      },
      has(t, k) {
        if (typeof k === 'string' && !Array.isArray(t)) { const p = path ? path + '.' + k : k; b.read[p] = (b.read[p] || 0) + 1; }
        return Reflect.has(t, k);
      },
      ownKeys(t) {
        if (!Array.isArray(t)) for (const k of Object.keys(t)) { const p = path ? path + '.' + k : k; b.passed[p] = 1; }
        return Reflect.ownKeys(t);
      },
    });
    proxies.set(node, made);
    targets.set(made, node);
    return made;
  };
  const original = Response.prototype.json;
  Response.prototype.json = async function () {
    const body = await original.call(this);
    try {
      const method = (this.__qaMethod || 'GET').toUpperCase();
      const b = bucket(norm(this.url), method);
      walk(body, '', b);
      return wrap(body, '', b);
    } catch (e) { return body; }
  };
  // Flush to the harness when it listens: a document's census dies with the
  // document, and a suite navigates by clicking as much as by goto.
  if (window.__qaCensusSink) {
    const flush = () => { try { window.__qaCensusSink(JSON.stringify(census)); } catch (e) {} };
    setInterval(flush, 1000);
    addEventListener('pagehide', flush);
  }
  const f = window.fetch;
  window.fetch = async function (input, init) {
    const r = await f.apply(this, arguments);
    try { r.__qaMethod = (init && init.method) || (input && input.method) || 'GET'; } catch (e) {}
    return r;
  };
})();
"""


def attach(context, sink: dict | None = None) -> None:
    """Install the recorder on a Playwright BrowserContext, before any page opens.
    With `sink`, every document flushes its census into it (merged), so a
    journey that navigates by clicking loses nothing."""
    if sink is not None:
        def receive(_source, payload):
            try:
                raw = json.loads(payload)
                merge(sink, {ep: {k: sorted(v) for k, v in b.items()} for ep, b in raw.items()})
            except (ValueError, AttributeError):
                pass
        context.expose_binding("__qaCensusSink", receive)
    context.add_init_script(INIT_SCRIPT)


def collect(page) -> dict:
    """The page's census so far: {endpoint: {served: [...], read: [...], passed: [...]}}."""
    raw = page.evaluate("() => JSON.stringify(window.__qaCensus || {})")
    return {ep: {k: sorted(v) for k, v in b.items()} for ep, b in json.loads(raw).items()}


def merge(into: dict, more: dict) -> dict:
    for ep, b in more.items():
        t = into.setdefault(ep, {"served": [], "read": [], "passed": []})
        for k in ("served", "read", "passed"):
            t[k] = sorted(set(t[k]) | set(b.get(k, [])))
    return into


def _covers(parent_paths: set[str], p: str) -> bool:
    """A path counts as read if it, or a path under it, was read — reading
    `row.fields[].label` uses `row.fields`."""
    return p in parent_paths or any(q.startswith(p + ".") or q.startswith(p + "[]") for q in parent_paths)


def diff(census: dict, ignore: list[str] | None = None) -> dict:
    """Per endpoint: served-never-read (leaf paths only), read-never-served, and the passed count."""
    ignore_re = [re.compile(x) for x in (ignore or [])]
    out = {}
    for ep, b in sorted(census.items()):
        served, read, passed = set(b["served"]), set(b["read"]), set(b["passed"])
        leaves = {p for p in served if not any(q.startswith(p + ".") or q.startswith(p + "[]") for q in served)}
        unread = sorted(p for p in leaves if not _covers(read, p) and p not in passed
                        and not any(r.search(f"{ep} {p}") for r in ignore_re))
        # A key read from an object the server DID send with other keys, and that
        # object never carried it. A read under a container that arrived empty
        # (an empty list, an empty map) says nothing and is not reported.
        def parent(q: str) -> str:
            return q[:q.rfind(".")] if "." in q else ""
        populated = {parent(s_) for s_ in served}
        phantom = sorted(p for p in read if p not in served and parent(p) in populated
                         and not any(s.startswith(p + ".") or s.startswith(p + "[]") for s in served)
                         and not any(r.search(f"{ep} {p}") for r in ignore_re))
        out[ep] = {"served_leaves": len(leaves), "unread": unread, "read_not_served": phantom,
                   "passed": len(passed & leaves)}
    return out


def summary(d: dict) -> dict:
    return {"endpoints": len(d), "served_leaves": sum(x["served_leaves"] for x in d.values()),
            "unread": sum(len(x["unread"]) for x in d.values()),
            "read_not_served": sum(len(x["read_not_served"]) for x in d.values()),
            "passed": sum(x["passed"] for x in d.values())}
