"""The bench core: environment, credentials, login, ledger, exit contract, redaction.

Every rule in here was paid for once in a project (dates in the docstrings). The
contract every stage honours:

  exit 0  every check decided and passed
  exit 1  a check failed, or the stage died — the ledger says which
  exit 3  nothing failed but something did not run (a skip); never reported as 0

A stage ALWAYS leaves `<shots>/<name>.json` behind (run_stage guarantees it), so
the orchestrator can tell "did not start" from "ran and decided nothing".
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .manifest import Bench


def env(key: str, default: str | None = None) -> str | None:
    v = os.environ.get(key)
    return default if v in (None, "") else v


# ----------------------------------------------------------------- ledger ---
_LIVE: list["Ledger"] = []


@dataclass
class Ledger:
    name: str
    shots: Path
    base_url: str = ""
    passed: int = 0
    failed: list[tuple[str, str]] = field(default_factory=list)
    not_run: list[tuple[str, str]] = field(default_factory=list)
    extra: dict = field(default_factory=dict)
    started: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        _LIVE.append(self)
        self._pre_abort: tuple[bool, int] | None = None

    @property
    def decided(self) -> int:
        """Checks that came to a verdict. Skips are excluded BY CONSTRUCTION."""
        return self.passed + len(self.failed)

    @property
    def did_start(self) -> bool:
        return bool(self.passed or self.failed or self.not_run)

    def check(self, label: str, ok: bool, detail: str = "", full: str = "") -> bool:
        """`detail` is what a person reads; `full` is what the ledger records.
        Never trim the record (anat 2026-08-23: a printed six of thirty-two
        constant columns hid a live defect for ten weeks)."""
        detail, full = redact(detail), redact(full)
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""), flush=True)
        if ok:
            self.passed += 1
        else:
            self.failed.append((label, full or detail))
        return ok

    def skip(self, label: str, why: str) -> None:
        why = redact(why)
        print(f"  [SKIP] {label} — {why}", flush=True)
        self.not_run.append((label, why))

    def exit_code(self) -> int:
        if self.failed:
            return 1
        return 3 if self.not_run else 0

    def write(self) -> Path:
        self.shots.mkdir(parents=True, exist_ok=True)
        out = self.shots / f"{self.name}.json"
        out.write_text(json.dumps({
            "name": self.name, "base_url": self.base_url,
            "finished": datetime.now(timezone.utc).isoformat(),
            "seconds": round(time.time() - self.started, 1),
            "passed": self.passed, "failed": self.failed, "not_run": self.not_run,
            "decided": self._pre_abort[1] if self._pre_abort else self.decided,
            "did_start": self._pre_abort[0] if self._pre_abort else self.did_start,
            **self.extra,
        }, indent=1))
        print(f"\n{self.name}: {self.passed} passed, {len(self.failed)} failed, "
              f"{len(self.not_run)} not run → {out}", flush=True)
        return out


def run_stage(name: str, main_fn, cfg: Bench, argv: list[str]) -> int:
    """Run a stage so that it ALWAYS leaves a ledger behind (anat 2026-08-31:
    six stages died in login before any try block and the night reported
    "NOT RUN" for four nights while eleven commits shipped)."""
    reason = ""
    try:
        return main_fn(cfg, argv)
    except SystemExit as ex:
        code = ex.code
        if isinstance(code, int) and code in (0, 3):
            return code
        reason = str(code) if code is not None else "SystemExit"
        return 1
    except BaseException as ex:  # noqa: BLE001 — the point is to record ANY death
        reason = f"{type(ex).__name__}: {ex}"
        raise
    finally:
        led = next((l for l in _LIVE if l.name == name), None)
        if led is None:
            led = _LIVE[-1] if _LIVE else Ledger(name, cfg.shots, cfg.origin)
        if not (cfg.shots / f"{led.name}.json").exists():
            led._pre_abort = (led.did_start, led.decided)
            led.failed.append((
                f"{led.name} did not start" if not led._pre_abort[0]
                else f"{led.name} aborted after {led._pre_abort[1]} decided, {len(led.not_run)} skipped",
                reason or "exited without writing a ledger"))
            led.write()


# ---------------------------------------------------------------- secrets ---
def _keychain_password(service: str, account: str | None) -> str | None:
    # `-a account` before `-s service`: the first version spliced it between -s
    # and its value, so every keychain lookup failed and the six tharros logins
    # read as "no credentials" on the very first live run (2026-09-05).
    cmd = ["security", "find-generic-password", *(["-a", account] if account else []), "-s", service, "-w"]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def credentials(cfg: Bench, role: str) -> tuple[str, str]:
    """A role's login: the environment first (a runner has no keychain), the
    laptop keychain second, and a failure that NAMES the two places to look."""
    c = cfg.credentials
    upper, lower = role.upper(), role.lower()
    email = env(c.email_env.format(ROLE=upper, role=lower))
    password = env(c.password_env.format(ROLE=upper, role=lower))
    if not email and c.emails.get(role):
        email = c.emails[role]
    if not email and c.email_template:
        email = c.email_template.format(role=lower, ROLE=upper)
    if password is None and c.keychain_service:
        password = _keychain_password(c.keychain_service.format(role=lower, ROLE=upper), c.keychain_account)
    if email and password:
        return email.strip().lower(), password
    raise SystemExit(
        f"no credentials for role {role!r}: set {c.password_env.format(ROLE=upper, role=lower)}"
        + (f" (and {c.email_env.format(ROLE=upper, role=lower)})" if not email else "")
        + (f", or keychain item {c.keychain_service.format(role=lower, ROLE=upper)!r}" if c.keychain_service else ""))


# ------------------------------------------------------------------ redact ---
_WORDS = r"password|passwd|pwd|secret|api[-_]?key|token|credential|authorization"
_CH = r"[A-Za-z0-9_.-]"
_KEY = rf"(?:{_CH}*(?:{_WORDS}){_CH}*|{_CH}*[-_]key|key)"
_Q = r"[\"']"
_MIN_SWEEPABLE = 8
_SECRET_KEY = re.compile(rf"({_Q})({_KEY})\1(\s*:\s*)({_Q})((?:(?!\4)[^\\]|\\.)*)\4", re.IGNORECASE)
_SECRET_TAIL = re.compile(rf"({_Q})({_KEY})\1(\s*:\s*)({_Q})(?:(?!\4).)*$", re.IGNORECASE)
_SECRET_FORM = re.compile(rf"\b({_KEY})=([^&\s]+)", re.IGNORECASE)


def redact(text: str) -> str:
    """Remove credential VALUES from a string about to be printed or recorded.
    Regex, not json.loads: details are built from truncated bodies. Lifted from
    anat (2026-09-01, when a seeder printed eight QA passwords)."""
    if not text:
        return text
    found = {m.group(5) for m in _SECRET_KEY.finditer(text)}
    found |= {m.group(2) for m in _SECRET_FORM.finditer(text)}
    text = _SECRET_KEY.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(1)}{m.group(3)}{m.group(4)}***{m.group(4)}", text)
    text = _SECRET_TAIL.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(1)}{m.group(3)}{m.group(4)}***", text)
    text = _SECRET_FORM.sub(lambda m: f"{m.group(1)}=***", text)
    for value in sorted(found, key=len, reverse=True):
        if len(value) >= _MIN_SWEEPABLE:
            text = text.replace(value, "***")
    return text


# ------------------------------------------------------------------ login ---
@dataclass
class Session:
    role: str
    email: str
    cookies: list[dict]
    csrf: str
    base_url: str
    #: The bearer token a `login.bearer` login answered; "" for a cookie session.
    bearer: str = ""

    def client(self, **kw) -> httpx.Client:
        jar = {c["name"]: c["value"] for c in self.cookies}
        headers = {"X-CSRF-Token": self.csrf} if self.csrf else {}
        if self.bearer:
            headers["Authorization"] = f"Bearer {self.bearer}"
        return httpx.Client(base_url=self.base_url, cookies=jar, follow_redirects=False,
                            headers=headers, timeout=kw.pop("timeout", 30), **kw)

    def browser_headers(self, cfg: Bench) -> dict[str, str]:
        """What the page stages install on the browser context: the bearer, and
        only when the manifest says the browser signs in with it (`header`).
        Under `cookie` the app's own script mints its token from the planted
        cookie, and a context header would override the fetches it makes."""
        if self.bearer and cfg.login.bearer_browser == "header":
            return {"Authorization": f"Bearer {self.bearer}"}
        return {}


def bearer_token(cfg: Bench, r: httpx.Response) -> str:
    """The token under `login.bearer` (dotted path) in the response body, or ""."""
    key = cfg.login.bearer
    if not key:
        return ""
    try:
        node = r.json()
    except ValueError:
        return ""
    for part in key.split("."):
        if not isinstance(node, dict):
            return ""
        node = node.get(part)
    return node.strip() if isinstance(node, str) else ""


def post_login(cfg: Bench, email: str, password: str) -> httpx.Response:
    """ONE POST to the login path — form-encoded (`login.kind: form`, with the
    CSRF pair when the form has one) or a JSON body (`login.kind: json`).

    A CSRF-protected form (tharros: `_csrf` field must equal the `tharros_csrf`
    cookie) refuses a bare POST with 403, which reads exactly like a wrong
    password. So when `login.csrf_field` is set the kit GETs the form first,
    carries the cookie jar, and posts the token back. The response keeps the
    cookies the server set on the POST merged with the ones from the GET.

    The cookies come back on the response either way; `login()` plants them in
    the browser context the page stages drive, so a JSON login's session lands
    exactly where a form login's does.
    """
    L = cfg.login
    with httpx.Client(base_url=cfg.origin, follow_redirects=False,
                      timeout=httpx.Timeout(30.0, connect=45.0)) as h:
        if L.kind == "json":
            return h.post(L.path, json={L.body["email"]: email, L.body["password"]: password})
        data = {L.fields["email"]: email, L.fields["password"]: password}
        if L.csrf_field:
            h.get(L.path)                                   # the server sets the CSRF cookie here
            token = h.cookies.get(L.csrf_cookie or "") if L.csrf_cookie else None
            if not token:
                raise SystemExit(f"login form at {L.path} set no {L.csrf_cookie!r} cookie, so the CSRF field cannot be filled")
            data[L.csrf_field] = token
        r = h.post(L.path, data=data)
        # merge: cookies set by the GET (csrf) plus the POST (session)
        for name, value in h.cookies.items():
            if name not in r.cookies:
                r.cookies.set(name, value)
        return r


def login_accepted(cfg: Bench, r: httpx.Response) -> bool:
    """Did this login response grant a session? ONE decision for both login
    kinds and both directions: `login()` fails a role on False, and the smoke
    stage's wrong-password probe fails on True. Two copies of this rule would
    be two chances to accept a role the app refused, or to call an accepted
    wrong password a refusal.

    The verdict is the SESSION COOKIE, not the status: a JSON login can answer
    200 with no session (ana-log's `{"mfaRequired": true}`), and a form login's
    302 says only where it went. When the manifest names no cookie the status
    is all there is — `expect` for json, a redirect for form.

    With `login.bearer` the TOKEN is part of the verdict too: ana-log answers
    the refresh cookie AND `accessToken`, and a session with the cookie alone
    reads every page as signed out (2026-09-07). Both must be present where
    both are declared.
    """
    L = cfg.login
    if L.kind == "json" and r.status_code != L.expect:
        return False
    if L.bearer and not bearer_token(cfg, r):
        return False
    primary = L.cookies[0] if L.cookies else None
    if primary:
        return bool(r.cookies.get(primary))
    return r.status_code in (302, 303) if L.kind == "form" else True


def _session_path(cfg: Bench, role: str) -> Path:
    """NEVER under cfg.shots. The shots directory is the evidence a workflow
    uploads as an artifact on failure, and a cached session is a live cookie —
    for 14 days anyone who could read the artifact could be staging's admin
    (IGA security review, 2026-09-05). Sessions live beside the OS temp dir,
    keyed by origin, readable by this user only."""
    import hashlib
    import tempfile
    key = hashlib.sha256(cfg.origin.encode()).hexdigest()[:12]
    return Path(os.environ.get("QA_SESSION_DIR") or tempfile.gettempdir()) / "qabench-sessions" / key / f"{role}.json"


def _cached_session(cfg: Bench, role: str) -> Session | None:
    p = _session_path(cfg, role)
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
    except (OSError, ValueError):
        return None
    if d.get("origin") != cfg.origin or time.time() - d.get("at", 0) > cfg.login.session_ttl_s:
        return None
    return Session(role, d["email"], d["cookies"], d.get("csrf", ""), cfg.origin, d.get("bearer", ""))


def forget_session(cfg: Bench, role: str) -> None:
    """A stage that saw its session bounced to the login form calls this so the
    next login is real, not the cache again."""
    p = _session_path(cfg, role)
    if p.exists():
        p.unlink()


def login(cfg: Bench, role: str, *, fresh: bool = False) -> Session:
    """Sign in with a form POST, surviving the cold connect every stage meets
    at its first request (measured 9.6 s then 0.1 s; anat 2026-08-27), and the
    app's own login throttle (tharros answers 429 after five logins a minute —
    on the first live run `staff` was refused and the stage read it as a dead
    credential). Sessions are cached per run so the stages share six logins."""
    if not fresh:
        cached = _cached_session(cfg, role)
        if cached:
            return cached
    email, password = credentials(cfg, role)
    L = cfg.login
    last: Exception | None = None
    r = None
    for attempt in range(3):
        try:
            r = post_login(cfg, email, password)
            if r.status_code == 429:
                if attempt < 2:
                    print(f"  (login as {role} throttled by the app — waiting {L.throttle_wait_s:.0f}s)", flush=True)
                    time.sleep(L.throttle_wait_s)
                    continue
                raise SystemExit(f"login as {role}: the app's login throttle answered 429 three times "
                                 f"({L.throttle_wait_s:.0f}s apart). Not a finding about the code; space the stages out.")
            break
        except (httpx.ConnectTimeout, httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as ex:
            last = ex
            if attempt < 2:
                wait = 2 ** attempt
                print(f"  ({cfg.origin} unreachable on login, retry {attempt + 1}/2 in {wait}s: {type(ex).__name__})", flush=True)
                time.sleep(wait)
    else:
        raise SystemExit(f"login as {role}: {cfg.origin} unreachable after 3 tries "
                         f"({type(last).__name__}). This is a network or host failure, NOT a finding about the code.")
    assert r is not None
    if not login_accepted(cfg, r):
        raise SystemExit(f"login as {role} ({email}) failed: {r.status_code} {redact(r.text[:160])}")
    jar = {name: r.cookies.get(name, "") for name in L.cookies}
    # Plant each cookie at the PATH the server set it on. ana-log scopes
    # `analog_refresh` to /api and rotates it on every refresh; a copy planted at
    # "/" would sit beside the rotated one, the browser sends both, and the
    # server reads the revoked one (2026-09-07).
    paths = {c.name: c.path for c in r.cookies.jar if c.path}
    host = urlparse(cfg.origin).hostname or ""
    secure = cfg.origin.startswith("https://")
    cookies = [{"name": n, "value": v, "domain": host, "path": paths.get(n) or "/", "secure": secure}
               for n, v in jar.items() if v]
    csrf = jar.get(L.csrf_cookie, "") if L.csrf_cookie else ""
    bearer = bearer_token(cfg, r)
    sess = Session(role, email, cookies, csrf, cfg.origin, bearer)
    sp = _session_path(cfg, role)
    sp.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    sp.write_text(json.dumps({"origin": cfg.origin, "email": email, "cookies": cookies, "csrf": csrf,
                              "bearer": bearer, "at": time.time()}))
    sp.chmod(0o600)
    return sess


# ---------------------------------------------------------------- helpers ---
def refuse_prod(cfg: Bench, reason: str) -> None:
    host = urlparse(cfg.origin).hostname or ""
    if host in cfg.production_hosts and env("QA_ALLOW_PROD") != "1":
        raise SystemExit(f"{reason}: refusing to run against production ({host}); set QA_ALLOW_PROD=1 if you really mean it")


def shot(page, shots: Path, name: str) -> Path:
    shots.mkdir(parents=True, exist_ok=True)
    p = shots / f"{name}.png"
    page.screenshot(path=str(p), full_page=True)
    return p


def banner(title: str) -> None:
    print("=" * 64, flush=True)
    print(title, flush=True)
    print("=" * 64, flush=True)


def fill(path: str, ids: dict[str, str]) -> str | None:
    """Substitute `{name}` placeholders; None when one has no id."""
    def sub(m):
        v = ids.get(m.group(1))
        return str(v) if v else m.group(0)
    out = re.sub(r"\{([a-zA-Z_]+)\}", sub, path)
    return None if "{" in out else out


def bounced_to_login(cfg: Bench, landed_url: str) -> bool:
    """page.goto FOLLOWS redirects, so an expired session lands on the login form
    with a 200 — indistinguishable from the page being served (anat 2026-08-31:
    46 phantom "HTTP 200 (want 403)" findings)."""
    page = cfg.login.page or cfg.login.path
    return (landed_url or "").split("?", 1)[0].rstrip("/").endswith(page.rstrip("/"))
