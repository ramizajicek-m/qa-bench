"""probe — the security baseline, observed from outside, against a deployed build.

    python -m qabench probe                         # every environment in qa/manifest.yml, passive checks
    python -m qabench probe --env staging --active  # plus the checks that send hostile traffic
    python -m qabench probe --json

WHY. A diff review reads the lines that changed. Public API docs, a missing
header, a rate limit keyed on a header the client writes: none of those is in
a diff, and all of them depend on how the app is DEPLOYED — the edge, the
proxy, the env vars — which no reading of the code settles. On 2026-09-29 the
code of four projects keyed their rate limit on the leftmost X-Forwarded-For
entry, and on one of them the edge overwrote the header, so the live answer
was «safe». Only a request to the real deployment can say which.

Each check is a row of qabench/security/catalogue.yml (`how: probe`, `probe:`
names the function here). Exit contract, as `scans`: 0 clean · 1 findings ·
3 a check could not run (never read as clean).

PASSIVE checks read what any visitor can read and run on production.
ACTIVE checks (--active) send forged headers, unsigned webhooks and oversized
bodies; they refuse to run against an environment called production.

Manifest (all optional; defaults shown):

    security:
      environments: [staging, production]   # which of `environments:` to probe
      admin_paths: [/admin]                  # must refuse an anonymous visitor
      webhooks:                               # active: must refuse an unsigned POST
        - {path: /webhooks/whatsapp, method: POST}
      rate_limited: {path: <bench.login.path>, requests: 30}   # active
      body_limit_bytes: 10485760             # active: limit + 1 MiB must get 413
      body_path: /                           # where the oversized body is POSTed
      exempt:                                # a known gap, owned and dated — never a silent pass
        headers: {why: "...", owner: "...", until: 2026-10-31}
"""
from __future__ import annotations

import datetime as _dt
import json
import random
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import yaml

UA = "qabench-probe (+security baseline; contact the estate owner)"
DOC_PATHS = ("/docs", "/redoc", "/openapi.json", "/api/docs", "/api/redoc", "/api/openapi.json")
SENSITIVE = {"/.git/HEAD": ("ref:",), "/.git/config": ("[core]",), "/.env": ("=",)}
REQUIRED_HEADERS = ("strict-transport-security", "content-security-policy", "x-content-type-options", "referrer-policy")
SESSIONISH = ("session", "auth", "token", "refresh", "sid")
EVIL_ORIGIN = "https://qabench-probe.invalid"
# Every header an app has been seen to read a client IP from. eliad keyed its
# login lockout on CF-Connecting-IP (2026-09-29): forging only X-Forwarded-For
# left that limiter intact, and the check said ok while a forged CF header per
# attempt walked past it.
CLIENT_IP_HEADERS = ("X-Forwarded-For", "CF-Connecting-IP", "X-Real-IP", "True-Client-IP", "Forwarded-For")
CATALOGUE = Path(__file__).resolve().parent / "security" / "catalogue.yml"
TRANSPORT: httpx.BaseTransport | None = None   # tests swap in a MockTransport


def catalogue_ids() -> dict[str, list[str]]:
    """{probe name: the catalogue rows it verifies} — so a red check names the requirement."""
    rows = (yaml.safe_load(CATALOGUE.read_text(encoding="utf-8")) or {}).get("rows", [])
    out: dict[str, list[str]] = {}
    for r in rows:
        if r.get("how") == "probe" and r.get("probe"):
            out.setdefault(r["probe"], []).append(str(r["id"]))
    return out


@dataclass
class Result:
    check: str
    env: str
    ran: bool = True
    findings: list[str] = field(default_factory=list)
    why: str = ""          # why it did not run
    exempt: dict | None = None
    requirements: list[str] = field(default_factory=list)


def _client(**kw) -> httpx.Client:
    if TRANSPORT is not None:
        kw.setdefault("transport", TRANSPORT)
    return httpx.Client(timeout=20, headers={"User-Agent": UA}, follow_redirects=False, **kw)


def _get(c: httpx.Client, url: str, **kw) -> httpx.Response:
    return c.get(url, **kw)


# ---------------------------------------------------------------- passive

def docs_exposed(c, base, cfg):
    out = []
    for p in DOC_PATHS:
        r = _get(c, base + p)
        if r.status_code != 200:
            continue
        body = r.text[:4000].lower()
        if '"openapi"' in body or "swagger-ui" in body or "redoc" in body:
            out.append(f"{p} answers 200 to an anonymous visitor (API schema public)")
    return out


def headers(c, base, cfg):
    r = _get(c, base + "/", follow_redirects=True)
    h = {k.lower(): v for k, v in r.headers.items()}
    out = [f"missing {name}" for name in REQUIRED_HEADERS if name not in h]
    csp = h.get("content-security-policy", "")
    if "x-frame-options" not in h and "frame-ancestors" not in csp:
        out.append("missing clickjacking defence (neither X-Frame-Options nor CSP frame-ancestors)")
    if csp and "frame-ancestors" in csp and "default-src" not in csp and "script-src" not in csp:
        out.append("CSP sets only frame-ancestors — no script-src/default-src, so it does not restrict scripts")
    if h.get("x-content-type-options", "nosniff").lower() != "nosniff":
        out.append(f"X-Content-Type-Options is {h['x-content-type-options']!r}, not nosniff")
    return [f"{x} on {r.url.path or '/'}" for x in out]


def cookies(c, base, cfg):
    out, seen = [], set()
    for path in {"/", cfg.get("_login_path") or "/login"}:
        r = _get(c, base + path, follow_redirects=True)
        for raw in r.headers.get_list("set-cookie"):
            name = raw.split("=", 1)[0].strip()
            if name in seen:
                continue
            seen.add(name)
            attrs = raw.lower()
            if "secure" not in attrs:
                out.append(f"cookie {name} set without Secure")
            if "samesite" not in attrs:
                out.append(f"cookie {name} set without SameSite")
            if any(s in name.lower() for s in SESSIONISH) and "httponly" not in attrs:
                out.append(f"cookie {name} looks like a session cookie and is readable by script (no HttpOnly)")
    return out


def cors(c, base, cfg):
    out = []
    for path in ("/", "/api/", cfg.get("_login_path") or "/login"):
        r = c.options(base + path, headers={"Origin": EVIL_ORIGIN, "Access-Control-Request-Method": "POST"})
        g = _get(c, base + path, headers={"Origin": EVIL_ORIGIN})
        for resp in (r, g):
            acao = resp.headers.get("access-control-allow-origin", "")
            creds = resp.headers.get("access-control-allow-credentials", "").lower() == "true"
            if acao == EVIL_ORIGIN and creds:
                out.append(f"{path} reflects an arbitrary Origin with credentials allowed")
            elif acao == "*" and creds:
                out.append(f"{path} allows Origin * with credentials")
    return sorted(set(out))


def sensitive_paths(c, base, cfg):
    out = []
    for p, markers in SENSITIVE.items():
        r = _get(c, base + p)
        if r.status_code == 200 and any(m in r.text[:2000] for m in markers) and "<html" not in r.text[:500].lower():
            out.append(f"{p} is served")
    return out


def server_banner(c, base, cfg):
    r = _get(c, base + "/", follow_redirects=True)
    out = []
    for name in ("server", "x-powered-by", "x-aspnet-version"):
        v = r.headers.get(name, "")
        if any(ch.isdigit() for ch in v):
            out.append(f"{name}: {v} discloses a version")
    return out


def admin_unauth(c, base, cfg):
    # A single-page app answers 200 with the same shell for EVERY path, the
    # admin one included; that shell holds no data and is not an exposure. So a
    # 200 counts only when it differs from what a path that cannot exist gets.
    shell = _get(c, base + f"/qabench-probe-{random.randint(10**6, 10**7)}").text
    out = []
    for p in cfg.get("admin_paths") or ["/admin"]:
        r = _get(c, base + p)
        if r.status_code == 200 and r.text != shell:
            out.append(f"{p} answers 200 to an anonymous visitor")
    return out


def https_redirect(c, base, cfg):
    if not base.startswith("https://"):
        return [f"{base} is not served over https"]
    r = _get(c, "http://" + base[len("https://"):] + "/")
    loc = r.headers.get("location", "")
    if r.status_code not in (301, 302, 307, 308) or not loc.startswith("https://"):
        return [f"http:// answers {r.status_code} instead of redirecting to https"]
    return []


# ---------------------------------------------------------------- active (never production)

def xff_spoof(c, base, cfg):
    rl = cfg.get("rate_limited") or {}
    path, n = rl.get("path") or cfg.get("_login_path") or "/login", int(rl.get("requests", 30))
    data = {"email": "qabench-probe@invalid.example", "username": "qabench-probe", "password": "not-a-password"}
    login = cfg.get("_login") or {}
    # A CSRF-protected form answers 403 before any limiter counts the attempt
    # (tharros, 2026-09-29: 60 × 403, so the check measured the CSRF guard).
    # Fill it the way core.login does: GET the form, echo the cookie in the field.
    if login.get("csrf_field") and path == login.get("path"):
        c.get(base + path)
        token = c.cookies.get(login.get("csrf_cookie") or "")
        if not token:
            raise _NotRun(f"{path} set no {login.get('csrf_cookie')!r} cookie, so the CSRF field cannot be filled")
        data[login["csrf_field"]] = token

    def burst(spoof: bool) -> list[int]:
        # A new identity on every attempt: a per-ACCOUNT throttle trips on the
        # same email whatever the IP, and read as «the IP limit held» (tharros,
        # 2026-09-29 — the probe said ok while uvicorn handed the app hosts[0]).
        codes = []
        for i in range(n):
            forged = f"203.0.113.{random.randint(1, 254)}"
            h = {name: forged for name in CLIENT_IP_HEADERS} if spoof else {}
            who = f"qabench-probe-{random.randint(10**8, 10**9)}"
            body = {**data, "email": f"{who}@invalid.example", "username": who}
            codes.append(c.post(base + path, data=body, headers=h).status_code)
        return codes

    spoofed = burst(True)
    if 429 in spoofed:
        return []                      # limited despite a new forged IP on every request
    plain = burst(False)
    if 429 in plain:
        return [f"{path}: {n} requests with forged client-IP headers ({', '.join(CLIENT_IP_HEADERS)}) were never limited; "
                f"the same {n} without them were — the limiter trusts a header the client writes"]
    raise _NotRun(f"{path}: no 429 in {2 * n} requests with or without forged IPs (status {sorted(set(plain))}) — "
                  "no limit observable here; set security.rate_limited to a limited path")


def webhook_unsigned(c, base, cfg):
    hooks = cfg.get("webhooks")
    if not hooks:
        raise _NotRun("no security.webhooks declared (declare [] if the app has none)") if hooks is None else _Skip()
    out = []
    for h in hooks:
        r = c.request(h.get("method", "POST"), base + h["path"], json={"probe": "unsigned"},
                      headers={"X-Hub-Signature-256": "sha256=" + "0" * 64})
        if r.status_code == 404:
            raise _NotRun(f"{h['path']} answers 404 — the declared webhook path is wrong")
        if r.status_code < 400:
            out.append(f"{h['path']} accepted an unsigned/wrongly-signed POST ({r.status_code})")
        elif r.status_code >= 500:
            out.append(f"{h['path']} crashed on an unsigned POST ({r.status_code}) instead of refusing it")
    return out


def body_limit(c, base, cfg):
    limit = int(cfg.get("body_limit_bytes", 10 * 1024 * 1024))
    size = limit + 1024 * 1024
    path = cfg.get("body_path", "/")
    try:
        r = c.post(base + path, content=b"a" * size, headers={"Content-Type": "application/octet-stream"})
    except httpx.HTTPError:
        return []                      # the server cut the upload off — refused
    if r.status_code != 413:
        return [f"POST {path} with {size} bytes answered {r.status_code}, not 413 — no request-size limit at {limit} bytes"]
    return []


class _NotRun(Exception):
    pass


class _Skip(Exception):
    pass


PASSIVE = {"docs_exposed": docs_exposed, "headers": headers, "cookies": cookies, "cors": cors,
           "sensitive_paths": sensitive_paths, "server_banner": server_banner, "admin_unauth": admin_unauth,
           "https_redirect": https_redirect}
ACTIVE = {"xff_spoof": xff_spoof, "webhook_unsigned": webhook_unsigned, "body_limit": body_limit}


def _exemption(cfg: dict, check: str, today: _dt.date) -> tuple[dict | None, str]:
    ex = (cfg.get("exempt") or {}).get(check)
    if not ex:
        return None, ""
    missing = [k for k in ("why", "owner", "until") if not ex.get(k)]
    if missing:
        return None, f"exemption for {check} lacks {', '.join(missing)} — an unowned, undated exemption is not one"
    until = ex["until"] if isinstance(ex["until"], _dt.date) else _dt.date.fromisoformat(str(ex["until"]))
    if until < today:
        return None, f"exemption for {check} expired {until} (owner {ex['owner']})"
    return ex, ""


def probe_env(env: str, base: str, cfg: dict, active: bool, today: _dt.date | None = None) -> list[Result]:
    today = today or _dt.date.today()
    base = base.rstrip("/")
    checks = dict(PASSIVE)
    if active:
        if env == "production":
            raise SystemExit("probe --active refuses production: it sends forged headers and oversized bodies")
        checks.update(ACTIVE)
    results, ids = [], catalogue_ids()
    with _client() as c:
        for name, fn in checks.items():
            res = Result(name, env, requirements=ids.get(name, []))
            try:
                res.findings = fn(c, base, cfg)
            except _Skip:
                continue
            except _NotRun as ex:
                res.ran, res.why = False, str(ex)
            except httpx.HTTPError as ex:
                res.ran, res.why = False, f"{type(ex).__name__}: {str(ex)[:160]}"
            ex, problem = _exemption(cfg, name, today)
            if problem:
                res.findings.append(problem)
            elif ex and res.findings:
                res.exempt = ex
            results.append(res)
    return results


def load(root: Path) -> tuple[dict, dict]:
    """(the security block with login path folded in, {env: url})."""
    doc = yaml.safe_load((root / "qa" / "manifest.yml").read_text(encoding="utf-8")) or {}
    sec = dict(doc.get("security") or {})
    sec["_login"] = ((doc.get("bench") or {}).get("login") or {})
    sec["_login_path"] = sec["_login"].get("path")
    envs = {k: (v or {}).get("url") for k, v in (doc.get("environments") or {}).items() if (v or {}).get("url")}
    wanted = sec.get("environments") or list(envs)
    return sec, {k: envs[k] for k in wanted if k in envs}


def run(argv: list[str]) -> int:
    root = Path(argv[argv.index("--repo") + 1] if "--repo" in argv else ".").resolve()
    sec, envs = load(root)
    if "--env" in argv:
        only = argv[argv.index("--env") + 1]
        envs = {k: v for k, v in envs.items() if k == only}
    if "--url" in argv:                      # an ad-hoc target, named for the report
        envs = {"adhoc": argv[argv.index("--url") + 1]}
    if not envs:
        print("probe: no environment to probe (qa/manifest.yml `environments:` has no url)")
        return 3
    active = "--active" in argv
    results = [r for env, url in envs.items() for r in probe_env(env, url, sec, active and env != "production")]
    failing = [r for r in results if r.ran and r.findings and not r.exempt]
    not_run = [r for r in results if not r.ran]
    if "--json" in argv:
        print(json.dumps([r.__dict__ for r in results], indent=1, default=str))
    else:
        for r in results:
            mark = "DID NOT RUN" if not r.ran else ("EXEMPT" if r.exempt else ("FAIL" if r.findings else "ok"))
            print(f"{r.env:10} {r.check:16} {mark}" + (f" — {r.why}" if r.why else "")
                  + (f" — owned by {r.exempt['owner']} until {r.exempt['until']}" if r.exempt else ""))
            for f in r.findings:
                print(f"    {f}")
            if r.findings and r.requirements:
                print(f"    requirement: {', '.join(r.requirements[:6])}")
    if failing:
        return 1
    return 3 if not_run else 0
