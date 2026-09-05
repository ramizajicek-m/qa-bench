"""The kit is not believed until each stage has gone red for the right reason.

Every test below plants ONE defect in the fake app (an env flag) and asserts the
stage names it — not merely that the exit code is non-zero.
"""
from __future__ import annotations

import json

import pytest

from qabench import __main__ as cli
from qabench import core, nightly


def _ledger(shots, name):
    return json.loads((shots / f"{name}.json").read_text())


# ── smoke ────────────────────────────────────────────────────────────────────

def test_smoke_is_green_on_a_healthy_app_and_records_the_swept_sha(bench_env, server_factory):
    server_factory()
    assert cli.main(["stage", "smoke"]) == 0
    led = _ledger(bench_env, "smoke")
    assert led["swept_sha"] == "abc123def456"
    assert led["failed"] == [] and led["not_run"] == []


def test_smoke_names_the_dead_secret_and_exits_3(bench_env, server_factory, monkeypatch):
    server_factory()
    monkeypatch.delenv("QA_STAFF_PASSWORD")
    assert cli.main(["stage", "smoke"]) == 3
    led = _ledger(bench_env, "smoke")
    assert any("QA_STAFF_PASSWORD" in why for _, why in led["not_run"])


def test_smoke_refuses_a_build_other_than_the_one_asked_about(bench_env, server_factory, monkeypatch):
    server_factory()
    monkeypatch.setenv("QA_EXPECT_SHA", "deadbeef0000")
    assert cli.main(["stage", "smoke"]) == 1
    led = _ledger(bench_env, "smoke")
    assert any("SHA this run was asked about" in label for label, _ in led["failed"])


def test_smoke_signs_in_through_a_csrf_protected_form(bench_env, server_factory, tmp_path, monkeypatch):
    """A protected form refuses a bare POST with 403 — indistinguishable from a
    wrong password. With `login.csrf_field` set the kit fetches the pair first."""
    server_factory(FAKE_CSRF="1")
    m = tmp_path / "qa" / "manifest.yml"
    m.parent.mkdir()
    m.write_text(open("qa/manifest.yml").read().replace("csrf_cookie: csrf_token", "csrf_cookie: csrf_token\n    csrf_field: _csrf"))
    monkeypatch.syspath_prepend(str(bench_env.parent.parent.parent / "fixture_repo")) if False else None
    assert cli.main(["stage", "smoke", "--manifest", str(m)]) == 0
    led = _ledger(bench_env, "smoke")
    assert led["failed"] == [] and led["not_run"] == []


def test_smoke_reports_a_csrf_form_it_was_not_told_about(bench_env, server_factory):
    """The same server, the manifest WITHOUT csrf_field: every login fails 403.
    The stage must go red (not skip) — a form the manifest describes wrongly is
    a finding about the manifest, and the ledger says 403."""
    server_factory(FAKE_CSRF="1")
    assert cli.main(["stage", "smoke"]) == 1
    led = _ledger(bench_env, "smoke")
    assert any("signs in" in label and "403" in detail for label, detail in led["failed"]), led["failed"]


def test_smoke_waits_out_a_login_throttle_instead_of_calling_it_a_dead_credential(bench_env, server_factory, tmp_path):
    server_factory(FAKE_THROTTLE="1")
    m = tmp_path / "qa" / "manifest.yml"
    m.parent.mkdir()
    m.write_text(open("qa/manifest.yml").read().replace("csrf_cookie: csrf_token", "csrf_cookie: csrf_token\n    throttle_wait_s: 0.2"))
    assert cli.main(["stage", "smoke", "--manifest", str(m)]) in (0, 3)
    led = _ledger(bench_env, "smoke")
    assert not led["failed"], led["failed"]
    assert all("signs in" not in label for label, _ in led["not_run"]), "a 429 must never read as a dead credential"


def test_a_session_is_reused_by_the_next_stage_and_forgotten_when_bounced(bench_env, server_factory):
    s = server_factory()
    assert cli.main(["stage", "smoke"]) == 0
    assert (bench_env / "sessions" / "owner.json").exists()
    s.stop()                                            # the server is gone; a cached login must not need it
    from qabench import manifest as mf
    cfg = mf.load(bench_env.parent.parent.parent / "fixture_repo") if False else mf.load()
    sess = core.login(cfg, "owner")
    assert sess.email == "owner@example.test"
    core.forget_session(cfg, "owner")
    with pytest.raises(SystemExit):
        core.login(cfg, "owner")                        # nothing cached, nothing to reach


# ── pages_by_role ────────────────────────────────────────────────────────────

def test_pages_by_role_is_green_and_decides_every_cell(bench_env, server_factory):
    server_factory()
    assert cli.main(["stage", "pages_by_role"]) == 0
    led = _ledger(bench_env, "pages_by_role")
    # 5 page routes × 2 roles × 2 viewports; the ids provider fills {item_id}
    assert led["cells"] == 20 and led["routes"] == 5
    assert led["not_run"] == []


def test_pages_by_role_goes_red_when_a_guard_is_removed(bench_env, server_factory):
    """THE MUTATION. Delete the guard: staff now opens /admin/owner-only with 200
    where the declared guard says 403 — the stage must name that cell."""
    server_factory(FAKE_UNGUARDED="1")
    assert cli.main(["stage", "pages_by_role"]) == 1
    led = _ledger(bench_env, "pages_by_role")
    bad = [label for label, _ in led["failed"]]
    assert any(l.startswith("staff") and l.endswith("/admin/owner-only") for l in bad), bad
    assert not any(l.startswith("owner") for l in bad), "the owner cells are healthy and must stay green"


def test_pages_by_role_sees_a_script_that_dies_after_render(bench_env, server_factory):
    server_factory(FAKE_BROKEN="1")
    assert cli.main(["stage", "pages_by_role"]) == 1
    led = _ledger(bench_env, "pages_by_role")
    broken = [(l, d) for l, d in led["failed"] if l.endswith("/admin/broken")]
    assert broken and all("pageerror" in d and "boom" in d for _, d in broken), led["failed"]
    assert len(broken) == 4   # both roles × both viewports; the page returns 200 for both


def test_pages_by_role_sees_sideways_scroll_only_at_phone_width(bench_env, server_factory):
    server_factory(FAKE_WIDE="1")
    assert cli.main(["stage", "pages_by_role"]) == 1
    led = _ledger(bench_env, "pages_by_role")
    wide = [(l, d) for l, d in led["failed"] if l.endswith("/admin/wide")]
    assert wide and all("390x844" in l and "scrolls sideways at 390px" in d for l, d in wide), led["failed"]


# ── endpoints_by_role ────────────────────────────────────────────────────────

def test_endpoints_by_role_is_green_on_a_healthy_app(bench_env, server_factory):
    server_factory()
    assert cli.main(["stage", "endpoints_by_role"]) == 0
    led = _ledger(bench_env, "endpoints_by_role")
    assert led["probed"] == 6 and led["decidable"] == 6      # 3 routes × 2 roles, all declared


def test_endpoints_by_role_sees_a_500_and_a_gate_that_is_not_real(bench_env, server_factory):
    server_factory(FAKE_500="1", FAKE_UNGUARDED="1")
    assert cli.main(["stage", "endpoints_by_role"]) == 1
    led = _ledger(bench_env, "endpoints_by_role")
    text = json.dumps(led["failed"])
    assert "/api/boom -> 500" in text
    assert "staff GET /api/secret -> 200 though the guard does not admit this role" in text


# ── the orchestrator's verdict ───────────────────────────────────────────────

def _result(**kw):
    base = {"name": "x", "exit": 0, "seconds": 1, "completed": True, "passed": 3, "failed": [], "not_run": [], "decided": 3}
    base.update(kw)
    return base


def test_verdict_is_red_when_a_stage_left_no_ledger_or_decided_nothing():
    assert nightly.verdict([_result()], floor=1)[0] is True
    assert nightly.verdict([_result(completed=False)], floor=1)[0] is False, "no ledger is NOT RUN, not a pass"
    assert nightly.verdict([_result(exit=3, passed=0, decided=0, not_run=[("a", "b")])], floor=1)[0] is False, "a stage that decided nothing is not evidence"
    assert nightly.verdict([_result(exit=0, failed=[("a", "b")], decided=1)], floor=1)[0] is False


def test_nightly_runs_the_shared_stages_and_writes_the_swept_sha(bench_env, server_factory):
    server_factory()
    assert cli.main(["nightly"]) == 0
    out = json.loads((bench_env / "nightly.json").read_text())
    assert out["ok"] is True and out["swept_sha"] == "abc123def456"
    assert [r["name"] for r in out["results"]] == ["smoke", "pages_by_role", "endpoints_by_role"]
    assert all(r["completed"] and r["decided"] >= 1 for r in out["results"])


# ── the kit's own hygiene ────────────────────────────────────────────────────

def test_redact_masks_values_but_not_booleans():
    s = core.redact('{"ok": true, "temp_password": "hunter22hunter", "url": "/s/hunter22hunter", "password_generated": false}')
    assert "hunter22hunter" not in s and '"password_generated": false' in s


def test_a_version_pin_that_disagrees_with_the_installed_kit_refuses(bench_env, server_factory, tmp_path, monkeypatch):
    server_factory()
    m = tmp_path / "qa" / "manifest.yml"
    m.parent.mkdir()
    m.write_text(open("qa/manifest.yml").read().replace("version: 0.1.3", "version: 9.9.9"))
    with pytest.raises(SystemExit) as ex:
        cli.main(["stage", "smoke", "--manifest", str(m)])
    assert "pins bench.version 9.9.9" in str(ex.value)


def test_keychain_lookup_builds_a_command_security_accepts(monkeypatch):
    """The argument ORDER is the test: `-a account` must precede `-s service`.
    Stubbed, because CI has no keychain — the real one refused every lookup on
    the first live run and the stage read it as six dead credentials."""
    seen = {}

    class R:
        returncode = 0
        stdout = "s3cret\n"
    monkeypatch.setattr(core.subprocess, "run", lambda cmd, **kw: seen.setdefault("cmd", cmd) and R())
    assert core._keychain_password("tharros-qa-owner", "tharros") == "s3cret"
    assert seen["cmd"] == ["security", "find-generic-password", "-a", "tharros", "-s", "tharros-qa-owner", "-w"]
    assert core._keychain_password("x", None)
    assert seen["cmd"][:2] == ["security", "find-generic-password"]
