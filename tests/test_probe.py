"""probe: each check goes red on the gap it names and stays green on the fix.

Every check is exercised both ways against an in-process fake deployment, so a
check that can never fire (or always fires) is caught here, not in a night.
"""
from __future__ import annotations

import datetime as dt

import httpx
import pytest

from qabench import probe

SAFE_HEADERS = {
    "strict-transport-security": "max-age=31536000",
    "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
    "x-content-type-options": "nosniff",
    "referrer-policy": "same-origin",
}


def app(*, docs=False, headers=SAFE_HEADERS, cookie=None, cors_reflect=False, admin_open=False, spa=False,
        limiter="real", hook_ok=False, body_413=True, csrf=False):
    """A fake deployment; each keyword opens one gap."""
    hits = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        path, h = req.url.path, dict(headers)
        if req.url.scheme == "http":
            return httpx.Response(301, headers={"location": "https://" + req.url.host + path})
        if cors_reflect and "origin" in req.headers:
            h.update({"access-control-allow-origin": req.headers["origin"], "access-control-allow-credentials": "true"})
        if cookie:
            h["set-cookie"] = cookie
        if path == "/openapi.json" and docs:
            return httpx.Response(200, text='{"openapi": "3.1.0"}', headers=h)
        if path == "/admin":
            if admin_open:
                return httpx.Response(200, text="<h1>all customers</h1>", headers=h)
            return httpx.Response(200, text="<div id=root></div>", headers=h) if spa else httpx.Response(302, headers={"location": "/login"})
        if path == "/login" and req.method == "GET" and csrf:
            return httpx.Response(200, text="<form>", headers={**h, "set-cookie": "app_csrf=tok123; Secure; SameSite=Lax"})
        if path == "/login" and req.method == "POST":
            if csrf and ("_csrf=tok123" not in req.content.decode() or "app_csrf=tok123" not in req.headers.get("cookie", "")):
                return httpx.Response(403)
            hits["n"] += 1
            key = req.headers.get("x-forwarded-for") if limiter == "leftmost-xff" else "client"
            hits.setdefault(key, 0)
            hits[key] += 1
            if limiter != "none" and hits[key] > 10:
                return httpx.Response(429)
            return httpx.Response(400)
        if path == "/hooks/wa":
            return httpx.Response(200) if hook_ok else httpx.Response(403)
        if req.method == "POST" and path == "/":
            return httpx.Response(413) if body_413 else httpx.Response(405)
        if spa:
            return httpx.Response(200, text="<div id=root></div>", headers=h)
        return httpx.Response(200 if path in ("/", "/login") else 404, text="<html>page</html>", headers=h)

    return httpx.MockTransport(handler)


def run_checks(monkeypatch, transport, cfg=None, env="staging", active=False, today=None):
    monkeypatch.setattr(probe, "TRANSPORT", transport)
    cfg = {"_login_path": "/login", "webhooks": [{"path": "/hooks/wa"}], "body_limit_bytes": 1024, **(cfg or {})}
    return {r.check: r for r in probe.probe_env(env, "https://app.example", cfg, active, today)}


def test_a_hardened_deployment_is_clean(monkeypatch):
    res = run_checks(monkeypatch, app(), active=True)
    assert {k: (r.ran, r.findings) for k, r in res.items() if not r.ran or r.findings} == {}


@pytest.mark.parametrize("gap,check", [
    (dict(docs=True), "docs_exposed"),
    (dict(headers={}), "headers"),
    (dict(headers={**SAFE_HEADERS, "content-security-policy": "frame-ancestors 'self'"}), "headers"),
    (dict(cookie="app_session=x; Path=/"), "cookies"),
    (dict(cors_reflect=True), "cors"),
    (dict(admin_open=True), "admin_unauth"),
])
def test_each_passive_gap_is_red(monkeypatch, gap, check):
    res = run_checks(monkeypatch, app(**gap))
    assert res[check].findings, f"{check} did not see {gap}"


def test_a_spa_shell_on_admin_is_not_an_exposure(monkeypatch):
    assert run_checks(monkeypatch, app(spa=True))["admin_unauth"].findings == []


def test_a_limiter_keyed_on_a_forged_header_is_red(monkeypatch):
    res = run_checks(monkeypatch, app(limiter="leftmost-xff"), active=True)
    assert "forged X-Forwarded-For" in res["xff_spoof"].findings[0]


def test_a_csrf_protected_login_is_filled_so_the_limiter_is_what_is_measured(monkeypatch):
    login = {"path": "/login", "csrf_field": "_csrf", "csrf_cookie": "app_csrf"}
    res = run_checks(monkeypatch, app(limiter="leftmost-xff", csrf=True), {"_login": login}, active=True)
    assert res["xff_spoof"].ran and res["xff_spoof"].findings


def test_no_limit_at_all_did_not_run_rather_than_passed(monkeypatch):
    r = run_checks(monkeypatch, app(limiter="none"), active=True)["xff_spoof"]
    assert not r.ran and "no 429" in r.why


def test_an_unsigned_webhook_accepted_is_red(monkeypatch):
    assert run_checks(monkeypatch, app(hook_ok=True), active=True)["webhook_unsigned"].findings


def test_no_body_limit_is_red(monkeypatch):
    assert run_checks(monkeypatch, app(body_413=False), active=True)["body_limit"].findings


def test_active_refuses_production(monkeypatch):
    with pytest.raises(SystemExit):
        run_checks(monkeypatch, app(), env="production", active=True)


def test_an_owned_dated_exemption_holds_and_an_expired_one_is_red(monkeypatch):
    ex = {"exempt": {"docs_exposed": {"why": "fix in flight", "owner": "rami", "until": "2026-10-31"}}}
    held = run_checks(monkeypatch, app(docs=True), ex, today=dt.date(2026, 9, 29))["docs_exposed"]
    assert held.exempt and held.findings
    late = run_checks(monkeypatch, app(docs=True), ex, today=dt.date(2026, 11, 1))["docs_exposed"]
    assert not late.exempt and any("expired" in f for f in late.findings)


def test_every_probe_check_names_catalogue_rows():
    ids = probe.catalogue_ids()
    missing = [n for n in {**probe.PASSIVE, **probe.ACTIVE} if not ids.get(n)]
    assert missing == [], f"checks with no catalogue requirement: {missing}"
