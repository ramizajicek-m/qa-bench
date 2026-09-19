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
  4. Every `bench.probes` entry VOTES: a freshness lag under its ceiling, a PDF
     the deployed build can actually render, a count above its floor. A probe
     that reads a value with no threshold is red — measured-and-silent is how a
     staging two days stale read green (ana-log, 2026-09-15) — and a value the
     answer does not carry is red, never a pass.
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

    # 4. environment probes that vote
    for probe in cfg.probes:
        L.check(f"probe: {probe.name}", *run_probe(cfg, probe))

    L.write()
    return L.exit_code()


def _dig(node, dotted: str):
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(dotted)
        node = node[part]
    return node


def run_probe(cfg: Bench, probe) -> tuple[bool, str]:
    """(passed, why) — why always names the measured value or the reason there is none."""
    if probe.json and probe.max is None and probe.min is None and probe.equals is None:
        return False, f"reads {probe.json} with no max/min/equals — a measurement with no threshold does not vote"
    try:
        client = core.login(cfg, probe.role).client() if probe.role else httpx.Client(
            base_url=cfg.origin, follow_redirects=False, timeout=httpx.Timeout(30.0, connect=45.0))
        with client:
            r = client.get(probe.path)
    except SystemExit as ex:
        return False, f"could not sign in as {probe.role}: {str(ex)[:120]}"
    except Exception as ex:  # noqa: BLE001
        return False, f"{type(ex).__name__}: {str(ex)[:120]} — a network or host failure, not a finding about the code"
    if r.status_code != probe.expect:
        return False, f"HTTP {r.status_code}, expected {probe.expect}"
    if probe.content_type and not r.headers.get("content-type", "").startswith(probe.content_type):
        return False, f"content-type {r.headers.get('content-type', 'none')!r}, expected {probe.content_type}"
    if not probe.json:
        return True, f"HTTP {r.status_code}" + (f", {probe.content_type}, {len(r.content)} bytes" if probe.content_type else "")
    try:
        value = _dig(r.json(), probe.json)
    except (ValueError, KeyError):
        return False, f"the answer carries no {probe.json} — cannot read it, which is not a pass"
    if probe.equals is not None:
        return value == probe.equals, f"{probe.json} = {value!r}, expected {probe.equals!r}"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return False, f"{probe.json} = {value!r} is not a number"
    ok = (probe.max is None or num <= probe.max) and (probe.min is None or num >= probe.min)
    bound = " and ".join(x for x in (f"≤ {probe.max}" if probe.max is not None else "",
                                      f"≥ {probe.min}" if probe.min is not None else "") if x)
    return ok, f"{probe.json} = {num:g}, must be {bound}"
