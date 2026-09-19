"""A signed-in Playwright page for the nightly explorer — and the write fence.

The explorer session writes its own Playwright scripts; this is the one import
they need:

    from qabench.explore_page import signed_in_page
    with signed_in_page("client", 390, 844) as page:
        page.goto("/orders")

WHY THE FENCE IS HERE AND NOT IN THE BRIEF. A sentence in a prompt saying
"never write to production" is a rule in a file, and a rule in a file is not a
guard (kit rule 05). Every page this module hands out routes every request
through `_fence`, which ABORTS any POST/PUT/PATCH/DELETE to a production host or
to a host the manifest lists under `explore.forbid_writes_to`, and records the
refusal — so an explorer that tries is visible in the ledger rather than
successful on a live system. ana-log's legacy server is the case in point: its
action endpoint carries readers and writers in one category.

The origin, the role's credentials and the viewport come from the same
manifest and the same `core.login` every other stage uses; nothing here reads a
password itself.
"""
from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from . import core, manifest

WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def fenced_hosts(cfg: manifest.Bench) -> set[str]:
    return {h for h in (*cfg.production_hosts, *cfg.explore.forbid_writes_to) if h}


def refused(method: str, url: str, fenced: set[str]) -> bool:
    return method.upper() in WRITE_METHODS and (urlparse(url).hostname or "") in fenced


def _fence(fenced: set[str], log: Path):
    def handler(route, request):
        if refused(request.method, request.url, fenced):
            with log.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"method": request.method, "url": request.url}) + "\n")
            return route.abort("blockedbyclient")
        return route.continue_()
    return handler


@contextlib.contextmanager
def signed_in_page(role: str, width: int = 390, height: int = 844, *, engine: str = "chromium",
                   repo: str | None = None):
    """Yield a page signed in as `role` on the manifest's origin, fenced."""
    from playwright.sync_api import sync_playwright

    cfg = manifest.load(Path(repo or os.environ.get("QA_REPO") or ".").resolve())
    core.refuse_prod(cfg, "the explorer")
    sess = core.login(cfg, role)
    log = cfg.shots / "explore" / "refused-writes.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = getattr(p, engine).launch(headless=True)
        try:
            ctx = browser.new_context(viewport={"width": width, "height": height}, base_url=cfg.origin,
                                      locale="he-IL", has_touch=width < 600, is_mobile=width < 600)
            ctx.add_cookies(sess.cookies)
            ctx.set_extra_http_headers(sess.browser_headers(cfg))
            ctx.route("**/*", _fence(fenced_hosts(cfg), log))
            yield ctx.new_page()
            if cfg.login.rotates:
                _keep_rotated(cfg, role, sess, ctx.cookies())
        finally:
            browser.close()


def _keep_rotated(cfg, role: str, sess, cookies: list[dict]) -> None:
    """Write the context's CURRENT cookies back to the session cache.

    An app that rotates its refresh token (ana-log) revokes the token a page
    used; the cache still held it, so the explorer's second page opened signed
    out — the explorer reported exactly that as its own seventh finding on its
    first night (2026-09-19). Writing the rotated cookie back keeps the session
    alive without handing the session a password (the stage signs in, the
    session never can)."""
    names = {c["name"] for c in sess.cookies}
    fresh = [{"name": c["name"], "value": c["value"], "domain": c.get("domain", ""), "path": c.get("path", "/"),
              "secure": c.get("secure", True)} for c in cookies if c["name"] in names]
    if not fresh:
        return
    path = core._session_path(cfg, role)
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return
    data["cookies"] = fresh
    path.write_text(json.dumps(data))
