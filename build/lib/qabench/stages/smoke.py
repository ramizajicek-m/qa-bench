"""smoke — is the deployment the one we think, and can every role sign in?

Three checks, in the order they would save the most time if they fail:

  1. `health` answers 200 with a `commit` field (C7: the running system says
     what it is). If QA_EXPECT_SHA is set the commit must be a prefix match —
     the sweep must not grade a build other than the one it was asked about.
     The commit is recorded as `swept_sha` for the promote step.
  2. Every role in bench.roles signs in. A dead credential exits 3 and NAMES
     the environment variable, so the morning's first item is "rotate X", not
     "read 400 red cells" (IGA 2026-08-30: a dead token behind every promotion).
  3. The login refusal is real: a wrong password is refused. A login that
     accepts anything makes every role check below it vacuous.
"""
from __future__ import annotations

import os

import httpx

from .. import core
from ..manifest import Bench


def main(cfg: Bench, argv: list[str]) -> int:
    L = core.Ledger("smoke", cfg.shots, cfg.origin)
    core.banner(f"smoke on {cfg.origin}")

    # 1. health + commit
    try:
        r = httpx.get(cfg.origin + cfg.health, timeout=httpx.Timeout(30.0, connect=45.0), follow_redirects=False)
        body = r.json() if r.status_code == 200 else {}
    except Exception as ex:  # noqa: BLE001
        L.check(f"{cfg.health} answers", False, f"{type(ex).__name__}: {str(ex)[:120]} — a network or host failure, not a finding about the code")
        L.write()
        return L.exit_code()
    commit = str((body or {}).get(cfg.commit_field) or "")
    L.check(f"{cfg.health} answers 200 with a commit", r.status_code == 200 and bool(commit),
            f"HTTP {r.status_code}, {cfg.commit_field}={commit[:12] or 'MISSING'}")
    expect = (os.environ.get("QA_EXPECT_SHA") or "").strip()
    if expect and commit:
        ok = commit.startswith(expect[: len(commit)]) or expect.startswith(commit)
        L.check("the deployment is the SHA this run was asked about", ok,
                f"serving {commit[:12]}, expected {expect[:12]}")
    L.extra["swept_sha"] = commit

    # 2. every role signs in
    for role in cfg.roles:
        try:
            core.login(cfg, role, fresh=True)          # smoke PROVES the credential; later stages reuse its session
            L.check(f"{role} signs in", True)
        except SystemExit as ex:
            msg = str(ex)
            if "no credentials" in msg:
                L.skip(f"{role} signs in", msg)          # exit 3: the secret is dead or unset
            else:
                L.check(f"{role} signs in", False, msg[:200])

    # 3. the refusal is real
    try:
        email, _ = core.credentials(cfg, cfg.roles[0])
        bad = core.post_login(cfg, email, "definitely-not-the-password-" + "x" * 8)
        if bad.status_code == 429:
            L.skip("a wrong password is refused", "the login throttle answered 429 — a throttle is not a refusal, so this proved nothing")
        else:
            primary = cfg.login.cookies[0] if cfg.login.cookies else None
            got_session = bool(bad.cookies.get(primary)) if primary else bad.status_code in (302, 303)
            L.check("a wrong password is refused", not got_session, f"HTTP {bad.status_code}")
    except SystemExit as ex:
        L.skip("a wrong password is refused", str(ex)[:160])

    L.write()
    return L.exit_code()
