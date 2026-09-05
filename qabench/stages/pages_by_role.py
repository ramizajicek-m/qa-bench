"""pages_by_role — every page, as every role, in a real browser, at every width.

For each (role, page, viewport) cell:
  * the HTTP status matches the declared guard: 200 where `admits[role]`, a
    deny status where not. A redirect that lands on the login form is NOT the
    page — the cell is a SKIP and the role fails once, loudly, because a run of
    such skips reads green (anat 2026-08-31, 46 phantom findings);
  * the page raised ZERO console errors and ZERO failed requests while it
    settled — the class a server-side check cannot see: a script that dies
    after render leaves everything it was going to wire up undone (tharros
    /finder shipped with its headings at opacity 0 for weeks);
  * at a phone-width viewport the document does not scroll sideways;
  * a screenshot per cell, for the gallery.

Routes come from the project's own `routes:` provider — never a hand-kept list.
"""
from __future__ import annotations

import re

from .. import core
from ..manifest import Bench


def _page_routes(cfg: Bench, rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        path = row["path"]
        if "GET" not in row.get("methods", ["GET"]):
            continue
        if not any(path.startswith(p) for p in cfg.pages.include_prefixes):
            continue
        if any(path.startswith(p) for p in cfg.pages.exclude_prefixes):
            continue
        if any(path.startswith(p) for p in cfg.api.include_prefixes):
            continue
        out.append(row)
    return sorted(out, key=lambda r: r["path"])


def _admits(row: dict, role: str) -> bool:
    a = row.get("admits")
    if isinstance(a, dict):
        return bool(a.get(role))
    if isinstance(a, (list, tuple, set)):
        return role in a
    return True     # no declaration: every authenticated role may open it


def main(cfg: Bench, argv: list[str]) -> int:
    from playwright.sync_api import sync_playwright

    if not cfg.routes:
        raise SystemExit("bench.routes is unset — name the provider that lists this project's routes")
    L = core.Ledger("pages_by_role", cfg.shots, cfg.origin)
    core.banner(f"pages × roles × viewports on {cfg.origin}")
    only_roles = argv[argv.index("--roles") + 1].split(",") if "--roles" in argv else None
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    rows = _page_routes(cfg, list(cfg.provider(cfg.routes)()))
    if not rows:
        L.check("the route provider yields pages", False, "zero page routes matched pages.include_prefixes — a sweep over nothing")
        L.write()
        return L.exit_code()
    print(f"  {len(rows)} page routes from {cfg.routes}", flush=True)
    ignore = [re.compile(p) for p in cfg.ignore_console]

    # ids for `{param}` pages, resolved through the app as the first role
    ids: dict = {}
    if cfg.ids:
        try:
            with core.login(cfg, cfg.roles[0]).client() as h:
                ids = dict(cfg.provider(cfg.ids)(h) or {})
        except SystemExit as ex:
            L.skip("resolve path ids", str(ex)[:160])
    cells_total = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for role in cfg.roles:
            if only_roles and role not in only_roles:
                continue
            try:
                sess = core.login(cfg, role)
            except SystemExit as ex:
                L.skip(f"{role}: all pages", str(ex)[:200])
                continue
            for (w, h_) in cfg.viewports:
                label = f"{w}x{h_}"
                print(f"  → {role} / {label} ({len(rows)} pages)", flush=True)
                ctx = browser.new_context(viewport={"width": w, "height": h_})
                ctx.set_default_timeout(30_000)
                ctx.set_default_navigation_timeout(45_000)
                ctx.add_cookies(sess.cookies)
                page = ctx.new_page()
                console: list[str] = []
                failed: list[str] = []
                bounced: list[str] = []
                page.on("console", lambda m: console.append(f"{m.type}: {m.text}") if m.type == "error" else None)
                page.on("pageerror", lambda e: console.append(f"pageerror: {e}"))
                page.on("response", lambda r: failed.append(f"{r.status} {r.request.method} {r.url}") if r.status >= 400 else None)
                for row in rows:
                    tmpl = row["path"]
                    if only and tmpl != only:
                        continue
                    path = core.fill(tmpl, ids)
                    cell = f"{role} {label} {tmpl}"
                    if not path:
                        L.skip(cell, "no id for a path parameter (bench.ids)")
                        continue
                    console.clear(); failed.clear()
                    try:
                        resp = page.goto(cfg.origin + path, wait_until="load")
                        page.wait_for_timeout(1500)
                    except Exception as ex:  # noqa: BLE001
                        L.check(cell, False, f"navigation failed: {type(ex).__name__}: {str(ex)[:120]}")
                        continue
                    if core.bounced_to_login(cfg, page.url):
                        bounced.append(tmpl)
                        L.skip(cell, "navigation ended on the login form — the session was lost, so this cell measured the sign-in page and not the route")
                        continue
                    status = resp.status if resp else 0
                    want_open = _admits(row, role)
                    landed = page.url.split("?", 1)[0].rstrip("/")
                    redirected = not landed.endswith(path.rstrip("/"))
                    if redirected and status < 400 and want_open:
                        status = 200                   # a redirect to a default page is the page
                    errs = [c for c in console if not any(rx.search(c) for rx in ignore)]
                    bad = [f for f in failed if not any(rx.search(f) for rx in ignore)]
                    if not want_open:
                        errs = [c for c in errs if "status of 40" not in c]
                        bad = [f for f in bad if not f.startswith(f"{status} GET {cfg.origin}{path}")]
                    ok_status = (status == 200) if want_open else (status in cfg.pages.deny_statuses)
                    sideways = False
                    if want_open and status == 200:
                        try:
                            sideways = bool(page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1"))
                        except Exception:  # noqa: BLE001
                            sideways = False
                    detail = f"HTTP {status} (want {'200' if want_open else '/'.join(map(str, cfg.pages.deny_statuses))})"
                    if errs:
                        detail += f"; console: {errs[0][:140]}" + (f" (+{len(errs) - 1})" if len(errs) > 1 else "")
                    if bad and want_open:
                        detail += f"; failed: {bad[0][:120]}" + (f" (+{len(bad) - 1})" if len(bad) > 1 else "")
                    allowed_reason = cfg.pages.sideways_allow.get(tmpl)
                    if sideways and allowed_reason:
                        # KNOWN offender: recorded, not failed — the ratchet's grandfather list
                        L.skip(f"{cell} scrolls sideways at {w}px", f"known — {allowed_reason}")
                        sideways = False
                    elif not sideways and allowed_reason and want_open and status == 200:
                        # The debt was paid; the list must shrink or it is a pardon
                        L.skip(f"{cell} no longer scrolls sideways", "remove it from bench.pages.sideways_allow")
                    if sideways:
                        detail += f"; the page scrolls sideways at {w}px"
                    ok = ok_status and not errs and not (want_open and bad) and not sideways
                    L.check(cell, ok, detail)
                    cells_total += 1
                    core.shot(page, cfg.shots, f"{role}__{label}__{tmpl.strip('/').replace('/', '_').replace('{', '').replace('}', '')}")
                if bounced:
                    core.forget_session(cfg, role)
                    L.check(f"{role} {label}: the session survived the sweep", False,
                            f"{len(bounced)} of {len(rows)} cells ended on the login form (first: {bounced[0]}) — those cells decided nothing")
                ctx.close()
        browser.close()
    L.extra["cells"] = cells_total
    L.extra["routes"] = len(rows)
    print(f"  decided {cells_total} cells over {len(rows)} routes × {len(cfg.viewports)} viewports", flush=True)
    L.write()
    return L.exit_code()
