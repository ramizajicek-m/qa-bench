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


def _scrolls_sideways(page) -> bool:
    """Does the DOCUMENT overflow the viewport — measured after the page has
    settled, twice, and only when both samples agree.

    The first live sweeps flipped this verdict between two runs of the same
    build for several cells: a table still laying out, web fonts still loading,
    an RTL reflow — one sample 1.5 s after `load` catches the page mid-paint. A
    check that cannot tell the code is wrong from the page being slow is a coin
    (tharros, 2026-09-05). So: wait for fonts, sample, wait, sample again.
    """
    try:
        page.evaluate("document.fonts && document.fonts.ready")
        page.wait_for_timeout(400)
        first = bool(page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1"))
        if not first:
            return False
        page.wait_for_timeout(800)
        return bool(page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1"))
    except Exception:  # noqa: BLE001
        return False


def _is_download(cfg: Bench, path: str) -> bool:
    tail = path.rsplit("/", 1)[-1].lower()
    return any(tail.endswith(suffix) for suffix in cfg.pages.download_suffixes)


def _probe_downloads(cfg: Bench, L: core.Ledger, rows: list[dict], ids: dict, only_roles) -> int:
    """Files are fetched as the role, not opened: status equals the declared guard."""
    n = 0
    files = [r for r in rows if _is_download(cfg, r["path"])]
    for role in cfg.roles:
        if only_roles and role not in only_roles:
            continue
        try:
            sess = core.login(cfg, role)
        except SystemExit as ex:
            L.skip(f"{role}: all downloads", str(ex)[:200])
            continue
        with sess.client(timeout=60) as h:
            for row in files:
                path = core.fill(row["path"], ids)
                cell = f"{role} download {row['path']}"
                if not path:
                    L.skip(cell, "no id for a path parameter (bench.ids)")
                    continue
                try:
                    r = h.get(path)
                except Exception as ex:  # noqa: BLE001
                    L.check(cell, False, f"request failed: {type(ex).__name__}")
                    continue
                want_open = _admits(row, role)
                ok = (200 <= r.status_code < 300) if want_open else (r.status_code in cfg.pages.deny_statuses)
                L.check(cell, ok, f"HTTP {r.status_code} (want {'2xx' if want_open else '/'.join(map(str, cfg.pages.deny_statuses))}), {len(r.content)} bytes")
                n += 1
    return n


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
    downloads = [r for r in rows if _is_download(cfg, r["path"])]
    rows = [r for r in rows if not _is_download(cfg, r["path"])]
    if downloads:
        print(f"  {len(downloads)} download route(s) probed over HTTP, not opened: {', '.join(r['path'] for r in downloads)}", flush=True)
        cells_total += _probe_downloads(cfg, L, downloads, ids, only_roles)

    # sideways_allow bookkeeping at the narrowest viewport, PER PATH across roles:
    # a page that scrolls for one role and not another is still an offender, and
    # telling the reader to "remove it" per cell sent 34 wrong hints in one
    # tharros run (2026-09-05) — followed, they would have made the next night red.
    narrow_w = min(cfg.viewports)[0]
    paid: set[str] = set()          # listed paths measured at the narrowest width
    still: set[str] = set()         # …of which at least one role's cell still scrolled
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
            relogged: dict[tuple[str, str], bool] = {}
            for (w, h_) in cfg.viewports:
                label = f"{w}x{h_}"
                print(f"  → {role} / {label} ({len(rows)} pages)", flush=True)
                ctx = browser.new_context(viewport={"width": w, "height": h_})
                ctx.set_default_timeout(30_000)
                ctx.set_default_navigation_timeout(45_000)
                ctx.add_cookies(sess.cookies)
                # a bearer session (login.bearer_browser: header) rides on every
                # navigation and fetch the context makes — measured on Chromium
                ctx.set_extra_http_headers(sess.browser_headers(cfg))
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
                        # A SHORT SESSION IS NOT A FINDING ABOUT THE PAGE. IGA's demo
                        # roles lose their session minutes after login (2026-09-05:
                        # inspector, then manager, at whatever cell they had reached).
                        # Sign in again ONCE, refresh the context's cookies, retry the
                        # cell; only a second bounce is recorded as a lost session.
                        if not relogged.get((role, label)):        # once per role AND viewport: each context is a fresh budget
                            relogged[(role, label)] = True
                            core.forget_session(cfg, role)
                            try:
                                sess = core.login(cfg, role, fresh=True)
                                ctx.clear_cookies()
                                ctx.add_cookies(sess.cookies)
                                ctx.set_extra_http_headers(sess.browser_headers(cfg))
                                print(f"  ({role}: session lost at {tmpl}; signed in again and retrying)", flush=True)
                                resp = page.goto(cfg.origin + path, wait_until="load")
                                page.wait_for_timeout(1500)
                            except Exception as ex:  # noqa: BLE001
                                L.check(cell, False, f"re-login after a lost session failed: {type(ex).__name__}: {str(ex)[:120]}")
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
                        sideways = _scrolls_sideways(page)
                    detail = f"HTTP {status} (want {'200' if want_open else '/'.join(map(str, cfg.pages.deny_statuses))})"
                    if errs:
                        detail += f"; console: {errs[0][:140]}" + (f" (+{len(errs) - 1})" if len(errs) > 1 else "")
                    if bad and want_open:
                        detail += f"; failed: {bad[0][:120]}" + (f" (+{len(bad) - 1})" if len(bad) > 1 else "")
                    allowed_reason = cfg.pages.sideways_allow.get(tmpl)
                    if allowed_reason and want_open and status == 200 and w == narrow_w:
                        paid.add(tmpl)
                        if sideways:
                            still.add(tmpl)
                    if sideways and allowed_reason:
                        # KNOWN offender: recorded, not failed — the ratchet's grandfather list
                        L.skip(f"{cell} scrolls sideways at {w}px", f"known — {allowed_reason}")
                        sideways = False
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
    for tmpl in sorted(paid - still):
        # The debt was paid for EVERY role; the list must shrink or it is a pardon
        L.skip(f"{tmpl} no longer scrolls sideways at {narrow_w}px for any role", "remove it from bench.pages.sideways_allow")
    L.extra["cells"] = cells_total
    L.extra["routes"] = len(rows)
    print(f"  decided {cells_total} cells over {len(rows)} routes × {len(cfg.viewports)} viewports", flush=True)
    L.write()
    return L.exit_code()
