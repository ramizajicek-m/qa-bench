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

from qabench.deployable import running_this_code
from .. import core
from ..manifest import Bench


# The label is a NAME, not prose typed at the call site. It was typed there,
# a commit reworded it, and tests/test_stages.py went on asserting the old
# wording -- so main was red for an hour and the failure said nothing about
# the cause. A check's identity must not be re-typed in two places.
RUNNING_THE_ASKED_CODE = "the deployment is running the code this run was asked about"

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
        # NOT string equality. A host that skips a deploy whose build input is
        # unchanged never serves a commit that touched only CI, docs or tests —
        # so demanding the exact SHA blocks the night on changes that cannot
        # affect what runs. Three projects hit that on 2026-09-10; see
        # qabench/deployable.py for the incident and what still refuses.
        ok, why = running_this_code(commit, expect)
        L.check(RUNNING_THE_ASKED_CODE, ok, why)
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
            # the same rule that let each role in above; a probe that decided
            # differently could refuse a password the roles' logins accepted
            L.check("a wrong password is refused", not core.login_accepted(cfg, bad), f"HTTP {bad.status_code}")
    except SystemExit as ex:
        L.skip("a wrong password is refused", str(ex)[:160])

    L.write()
    return L.exit_code()
