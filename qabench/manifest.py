"""Read the `bench:` block of a project's qa/manifest.yml into a typed config.

Nothing is inferred. A missing fact is an error naming the key, not a default
chosen in a session — the one place a default IS chosen (viewports, the login
field names) it is the estate-wide convention and stated here.
"""
from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml


@dataclass
class Credentials:
    email_env: str = "QA_{ROLE}_EMAIL"
    password_env: str = "QA_{ROLE}_PASSWORD"
    email_template: str | None = None          # e.g. "qa-{role}@example.com"
    emails: dict[str, str] = field(default_factory=dict)   # per-role emails when no template fits (IGA: demo accounts)
    keychain_service: str | None = None        # e.g. "anat-qa-{role}" (laptop only)
    keychain_account: str | None = None


@dataclass
class Login:
    #: `form` — ONE form-encoded POST to `path` (anat, tharros, IGA, eliad, my8200).
    #: `json` — a JSON body to `path` with the role's credentials under the keys
    #: in `body`, answered with `expect` and the session in Set-Cookie (ana-log
    #: 2026-09-07: `{"email","password"}` → 200 + `analog_refresh`). Both kinds
    #: prove the SAME thing — the named cookies were set — and a wrong password
    #: is refused the same way, so the smoke stage does not know which it drove.
    kind: str = "form"
    path: str = "/login"
    fields: dict[str, str] = field(default_factory=lambda: {"email": "email", "password": "password"})
    #: json only: JSON key → credential. `{email: email, password: password}`
    #: means the body is `{"email": <email>, "password": <password>}`.
    body: dict[str, str] = field(default_factory=lambda: {"email": "email", "password": "password"})
    #: json only: the status a successful login answers. A form login answers
    #: whatever its redirect is, so it is not asserted there.
    expect: int = 200
    #: The PAGE a signed-out browser is sent to. A form login's path is that
    #: page; a JSON login's path is an endpoint the browser never lands on, so a
    #: lost session would go unrecognised and read as the route. Default: `path`.
    page: str | None = None
    cookies: list[str] = field(default_factory=list)   # first one is the session; empty = any Set-Cookie
    csrf_cookie: str | None = None
    #: A login form protected by a CSRF pair: the kit GETs `path` first, takes
    #: `csrf_cookie` from the response, and posts it back in this form field
    #: (tharros: cookie tharros_csrf, field _csrf). None = the form has no CSRF.
    csrf_field: str | None = None
    #: A login throttle (tharros: 5 per minute per IP) answers 429. The kit waits
    #: this long and retries, up to three times; a 429 is never a verdict.
    throttle_wait_s: float = 65.0
    #: Sessions are cached under <shots>/sessions/<role>.json and reused by the
    #: next stage in the same run, so six roles × three stages is six logins, not
    #: eighteen — the throttle above is exactly what eighteen would trip.
    session_ttl_s: float = 3300.0

    def __post_init__(self):
        if self.kind not in ("form", "json"):
            raise SystemExit(f"bench.login.kind must be `form` or `json`, not {self.kind!r}")
        if self.kind == "json" and self.csrf_field:
            raise SystemExit("bench.login.csrf_field is a form-login setting; a `json` login has no form to fetch a token from")
        for key in ("email", "password"):
            if key not in self.body:
                raise SystemExit(f"bench.login.body must map `{key}` to the JSON key the login reads it from")


@dataclass
class Pages:
    include_prefixes: list[str] = field(default_factory=lambda: ["/admin"])
    exclude_prefixes: list[str] = field(default_factory=list)
    deny_statuses: list[int] = field(default_factory=lambda: [401, 403])
    #: Pages KNOWN to scroll sideways at a phone width, each with a reason — a
    #: ratchet, not a pardon: a listed page still prints as a SKIP with its
    #: reason, a listed page that no longer scrolls asks to be removed, and any
    #: page NOT listed that scrolls fails. Tharros' first live sweep found 13
    #: (2026-09-05); a night red on day one is switched off within a week.
    sideways_allow: dict[str, str] = field(default_factory=dict)
    #: A route whose path ends like a FILE is a download, not a page: page.goto
    #: aborts with "Download is starting" (IGA /admin/reports.csv, 2026-09-05) and
    #: a screenshot of it means nothing. Such routes are probed as the role over
    #: HTTP — status against the declared guard — and never opened in the browser.
    download_suffixes: list[str] = field(default_factory=lambda: [".csv", ".pdf", ".xlsx", ".xls", ".json", ".sqlite", ".zip", ".ics", ".txt"])


@dataclass
class Api:
    include_prefixes: list[str] = field(default_factory=lambda: ["/api/"])
    exclude_paths: list[str] = field(default_factory=list)      # streams, by design
    portal_roles: list[str] = field(default_factory=list)       # customer roles
    portal_prefixes: list[str] = field(default_factory=list)    # what a customer MAY reach
    open_prefixes: list[str] = field(default_factory=list)      # open to any session by design


@dataclass
class Heartbeat:
    key: str = "qa_nightly"
    cadence_h: float = 30.0
    stamp: str | None = None       # dotted "module:function(payload: dict)" provider


@dataclass
class Bench:
    repo: Path
    origin: str
    version: str
    health: str = "/health"
    commit_field: str = "commit"
    roles: list[str] = field(default_factory=list)
    credentials: Credentials = field(default_factory=Credentials)
    login: Login = field(default_factory=Login)
    viewports: list[tuple[int, int]] = field(default_factory=lambda: [(1440, 900), (390, 844)])
    pages: Pages = field(default_factory=Pages)
    api: Api = field(default_factory=Api)
    ignore_console: list[str] = field(default_factory=list)
    routes: str | None = None      # "module:function" -> [{path, methods, admits}]
    ids: str | None = None         # "module:function(owner_client) -> {name: id}"
    stages_extra: list[tuple[str, list[str]]] = field(default_factory=list)
    heartbeat: Heartbeat = field(default_factory=Heartbeat)
    production_hosts: list[str] = field(default_factory=list)
    shots: Path = field(default_factory=lambda: Path("/tmp/qabench"))
    floor: int = 1

    def provider(self, dotted: str) -> Callable[..., Any]:
        """Import `module:function` with the repo root first on sys.path."""
        module, _, attr = dotted.partition(":")
        if str(self.repo) not in sys.path:
            sys.path.insert(0, str(self.repo))
        return getattr(importlib.import_module(module), attr)


def _sub(cls, data: dict | None):
    return cls(**(data or {}))


def load(repo: Path | None = None, *, manifest: Path | None = None) -> Bench:
    repo = (repo or Path.cwd()).resolve()
    path = manifest or (repo / "qa" / "manifest.yml")
    if not path.exists():
        raise SystemExit(f"no manifest at {path} — the qa-framework skill says how to write one")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    b = doc.get("bench")
    if not isinstance(b, dict):
        raise SystemExit(f"{path} has no `bench:` block — see the qa-framework skill for its shape")
    origin_env = b.get("origin_env", "QA_BASE_URL")
    origin = (os.environ.get(origin_env) or "").strip().rstrip("/")
    if not origin:
        raise SystemExit(f"{origin_env} is unset — name the deployment to drive. There is deliberately "
                         "no default: a sweep that picks its own target verifies whatever it picked.")
    roles = b.get("roles")
    if not roles:
        raise SystemExit(f"{path}: bench.roles is empty — which logins should the sweep use?")
    envs = doc.get("environments") or {}
    prod_hosts = b.get("production_hosts") or [
        (envs.get("production") or {}).get("url", "").replace("https://", "").rstrip("/")]
    prod_hosts = [h for h in prod_hosts if h]
    viewports = [tuple(v) for v in (b.get("viewports") or [[1440, 900], [390, 844]])]
    extra = [(s[0], list(s[1])) for s in (b.get("stages_extra") or [])]
    shots = Path(os.environ.get("QA_SHOT_DIR") or b.get("shots") or f"/tmp/qabench-{doc.get('project', 'project')}")
    return Bench(
        repo=repo, origin=origin, version=str(b.get("version", "")),
        health=b.get("health", "/health"), commit_field=b.get("commit_field", "commit"),
        roles=list(roles), credentials=_sub(Credentials, b.get("credentials")),
        login=_sub(Login, b.get("login")), viewports=viewports,
        pages=_sub(Pages, b.get("pages")), api=_sub(Api, b.get("api")),
        ignore_console=list(b.get("ignore_console") or []),
        routes=b.get("routes"), ids=b.get("ids"), stages_extra=extra,
        heartbeat=_sub(Heartbeat, b.get("heartbeat")), production_hosts=prod_hosts,
        shots=shots, floor=int(b.get("floor", 1)),
    )
