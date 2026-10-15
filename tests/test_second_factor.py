"""A login with a second factor: the kit answers the TOTP step itself.

tharros (2026-10-15) put a TOTP code between the password and the session. A
bench that posts only the password then holds no session and every role reads
as a dead credential — the whole night red for a reason that is not a finding.

Mutations: drop the `answer_second_factor` call in `login()` -> the flow test is
red; SHA256 in `totp` -> the RFC test is red.
"""
import time

import httpx
import pytest

from qabench import core
from qabench.manifest import Bench, Credentials, Login

RFC_SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"


@pytest.mark.parametrize("t, expected", [(59, "287082"), (1111111109, "081804"), (1234567890, "005924")])
def test_totp_matches_the_rfc_6238_vectors(t, expected):
    # RFC 6238 Appendix B publishes 8 digits; the 6-digit code is its last six.
    assert core.totp(RFC_SECRET, t // 30) == expected


def _app(handler):
    real = httpx.Client

    class Mocked(real):
        def __init__(self, *a, **kw):
            kw["transport"] = httpx.MockTransport(handler)
            super().__init__(*a, **kw)
    return Mocked


def _cfg():
    cfg = Bench.__new__(Bench)
    cfg.origin = "https://staging.example"
    cfg.login = Login(path="/login", cookies=["sess"], csrf_cookie="csrf", csrf_field="_csrf",
                      second_factor_path="/login/verify")
    cfg.credentials = Credentials()
    return cfg


def test_the_kit_posts_the_current_code_and_keeps_the_session(monkeypatch, tmp_path):
    seen = {}

    def handler(req: httpx.Request):
        if req.method == "GET":
            return httpx.Response(200, headers={"set-cookie": "csrf=tok; Path=/"})
        body = dict(x.split("=", 1) for x in req.content.decode().split("&"))
        if req.url.path == "/login":
            return httpx.Response(303, headers={"location": "/login/verify",
                                                "set-cookie": "pending=p1; Path=/"})
        seen.update(body, cookie=req.headers.get("cookie", ""))
        ok = body.get("code") == core.totp(RFC_SECRET, int(time.time() // 30))
        return httpx.Response(303, headers={"location": "/admin", "set-cookie": "sess=s1; Path=/"}) \
            if ok else httpx.Response(401)

    monkeypatch.setattr(core.httpx, "Client", _app(handler))
    monkeypatch.setenv("QA_OWNER_TOTP", RFC_SECRET)
    cfg = _cfg()
    r = core.post_login(cfg, "o@x", "pw")
    assert r.status_code == 303 and not core.login_accepted(cfg, r), "the password alone must not pass"
    r = core.answer_second_factor(cfg, "owner", r)
    assert core.login_accepted(cfg, r)
    assert seen["_csrf"] == "tok" and "pending=p1" in seen["cookie"]

    # and login() itself takes that step — the wiring, not just the helper
    monkeypatch.setenv("QA_OWNER_EMAIL", "o@x")
    monkeypatch.setenv("QA_OWNER_PASSWORD", "pw")
    monkeypatch.setenv("QA_SESSION_DIR", str(tmp_path))
    time.sleep(31 - time.time() % 30)                 # the code above is spent
    sess = core.login(cfg, "owner", fresh=True)
    assert any(c["name"] == "sess" and c["value"] == "s1" for c in sess.cookies)


def test_a_missing_secret_names_the_variable(monkeypatch):
    monkeypatch.delenv("QA_SALES_TOTP", raising=False)
    r = httpx.Response(303, headers={"location": "/login/verify"})
    with pytest.raises(SystemExit, match="QA_SALES_TOTP"):
        core.answer_second_factor(_cfg(), "sales", r)


def test_a_login_without_a_second_factor_passes_through():
    r = httpx.Response(303, headers={"location": "/admin"})
    assert core.answer_second_factor(_cfg(), "owner", r) is r
