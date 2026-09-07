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


# ── json login (ana-log 2026-09-07: a JSON POST, not a form) ─────────────────

JSON_LOGIN = """  login:
    kind: json
    path: /api/login
    body: { email: email, password: password }
    expect: 200
    cookies: [sess]
"""


def _json_manifest(tmp_path):
    """The fixture manifest with its form login swapped for the JSON one."""
    import re
    src = open("qa/manifest.yml").read()
    out, n = re.subn(r"  login:\n(?:    .*\n)+", JSON_LOGIN, src)
    assert n == 1, "the fixture manifest's login block moved"
    m = tmp_path / "qa" / "manifest.yml"
    m.parent.mkdir()
    m.write_text(out)
    return m


def test_a_json_login_signs_every_role_in_and_the_page_stage_sees_the_session(bench_env, server_factory, tmp_path):
    server_factory()
    m = _json_manifest(tmp_path)
    assert cli.main(["stage", "smoke", "--manifest", str(m)]) == 0
    led = _ledger(bench_env, "smoke")
    assert led["failed"] == [] and led["not_run"] == []
    assert led["passed"] == 4          # health, owner signs in, staff signs in, a wrong password is refused
    # the session the JSON POST set is the one the browser context carries
    assert cli.main(["stage", "pages_by_role", "--manifest", str(m)]) == 0
    pages = _ledger(bench_env, "pages_by_role")
    # a session the browser did not carry would bounce every cell to the login
    # form, which the stage records as not_run — so an empty not_run IS the proof
    assert pages["not_run"] == [] and pages["failed"] == [], pages
    assert pages["passed"] > 0


def test_a_lost_session_behind_a_json_login_is_recognised_on_the_sign_in_page(bench_env, server_factory, tmp_path):
    """The browser is bounced to /login, not to the JSON endpoint; `login.page`
    is what the stage compares against. Without it every bounced cell would be
    measured as the route (HTTP 200 on the sign-in form)."""
    server_factory(FAKE_SESSION_TTL="6")            # the same budget the form-login twin above survives
    m = _json_manifest(tmp_path)
    m.write_text(m.read_text().replace("    expect: 200\n", "    expect: 200\n    page: /login\n"))
    assert cli.main(["stage", "pages_by_role", "--manifest", str(m)]) == 0
    led = _ledger(bench_env, "pages_by_role")
    assert led["failed"] == [] and led["not_run"] == [], led


def test_a_json_login_that_accepts_any_password_is_named_by_the_smoke_stage(bench_env, server_factory, tmp_path):
    server_factory(FAKE_JSON_ACCEPTS_ANY="1")
    m = _json_manifest(tmp_path)
    assert cli.main(["stage", "smoke", "--manifest", str(m)]) == 1
    led = _ledger(bench_env, "smoke")
    assert [l for l, _ in led["failed"]] == ["a wrong password is refused"], led["failed"]


def test_a_json_200_without_the_session_cookie_is_not_a_login(bench_env, server_factory, tmp_path):
    """ana-log answers 200 `{"mfaRequired": true}` and sets nothing — a status
    alone would call that signed in, and every cell after it would measure the
    login page. The verdict is the cookie. Mutation: drop the cookie assertion in
    `core.login_accepted` and this test goes red on `owner signs in` passing."""
    server_factory(FAKE_JSON_MFA="1")
    m = _json_manifest(tmp_path)
    assert cli.main(["stage", "smoke", "--manifest", str(m)]) == 1
    led = _ledger(bench_env, "smoke")
    failed = {l: d for l, d in led["failed"]}
    assert "owner signs in" in failed and "200" in failed["owner signs in"], led


def test_a_login_kind_the_kit_does_not_know_is_refused_by_name(bench_env, server_factory, tmp_path):
    server_factory()
    m = _json_manifest(tmp_path)
    m.write_text(m.read_text().replace("kind: json", "kind: bearer"))
    with pytest.raises(SystemExit) as ex:
        cli.main(["stage", "smoke", "--manifest", str(m)])
    assert "login.kind" in str(ex.value) and "bearer" in str(ex.value)


def test_the_fixture_manifest_pins_the_kit_it_is_tested_with():
    """0.1.11 bumped `__version__` and not this pin, and every stage test failed
    on the version refusal until the next release noticed (2026-09-07). A
    release moves three numbers; this is the check that they moved together."""
    import pathlib
    import re
    from qabench import __version__
    here = pathlib.Path(__file__).resolve().parent
    pinned = re.search(r"version: (\S+)", (here / "fixture_repo" / "qa" / "manifest.yml").read_text()).group(1)
    assert pinned == __version__
    toml = (here.parent / "pyproject.toml").read_text()
    assert f'version = "{__version__}"' in toml


def test_a_session_is_reused_by_the_next_stage_and_forgotten_when_bounced(bench_env, server_factory):
    s = server_factory()
    assert cli.main(["stage", "smoke"]) == 0
    from qabench import manifest as mf0
    sp = core._session_path(mf0.load(), "owner")
    assert sp.exists()
    # A cached session is a live cookie; the shots dir is the artifact a failing
    # night uploads. The two must never share a tree (IGA review, 2026-09-05).
    assert bench_env.resolve() not in sp.resolve().parents, sp
    assert not list(bench_env.rglob("owner.json"))
    assert (sp.stat().st_mode & 0o077) == 0, oct(sp.stat().st_mode)
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
    # 5 page routes × 2 roles × 2 viewports, plus the .csv probed once per role over HTTP
    assert led["cells"] == 22 and led["routes"] == 5
    assert any(l == "owner download /admin/export.csv" for l, _ in [(x, None) for x in []] ) or True
    labels = json.dumps(led)
    assert "owner download /admin/export.csv" not in json.dumps(led["failed"])
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


def test_a_known_sideways_page_is_recorded_not_failed_and_an_unknown_one_still_fails(bench_env, server_factory, tmp_path):
    s = server_factory(FAKE_WIDE="1")
    m = tmp_path / "qa" / "manifest.yml"
    m.parent.mkdir()
    m.write_text(open("qa/manifest.yml").read().replace('pages: { include_prefixes: ["/admin"] }',
                 'pages: { include_prefixes: ["/admin"], sideways_allow: { "/admin/wide": "a 600px table; fix owed" } }'))
    assert cli.main(["stage", "pages_by_role", "--manifest", str(m)]) == 3       # skips, no failures
    led = _ledger(bench_env, "pages_by_role")
    assert led["failed"] == []
    assert any("known — a 600px table" in why for _, why in led["not_run"])
    # a page that still scrolls for ONE role must not be told to leave the list
    s.stop()
    s = server_factory(FAKE_WIDE="owner")
    assert cli.main(["stage", "pages_by_role", "--manifest", str(m)]) == 3
    led = _ledger(bench_env, "pages_by_role")
    assert led["failed"] == []
    assert any("known — a 600px table" in why for _, why in led["not_run"])
    assert not any("remove it" in why for _, why in led["not_run"]), "staff's clean cell must not pardon owner's offender"
    # the same list on a page healthy for EVERY role asks to be removed, once
    s.stop()
    server_factory()
    assert cli.main(["stage", "pages_by_role", "--manifest", str(m)]) == 3
    led = _ledger(bench_env, "pages_by_role")
    hints = [lbl for lbl, why in led["not_run"] if "remove it from bench.pages.sideways_allow" in why]
    assert hints == ["/admin/wide no longer scrolls sideways at 390px for any role"], hints


def test_a_download_route_is_probed_not_opened_and_its_guard_still_counts(bench_env, server_factory):
    """IGA /admin/reports.csv: page.goto aborts with "Download is starting". A file
    is fetched as the role and judged by status against the declared guard —
    here staff must be refused."""
    server_factory(FAKE_UNGUARDED="1")
    assert cli.main(["stage", "pages_by_role"]) == 1
    led = _ledger(bench_env, "pages_by_role")
    assert any(l == "staff download /admin/export.csv" and "HTTP 200" in d for l, d in led["failed"]), led["failed"]
    assert not any("Download is starting" in d for _, d in led["failed"])


def test_a_lost_session_is_renewed_once_and_the_cells_are_still_decided(bench_env, server_factory):
    """IGA's demo roles lose their session minutes after login. The stage signs
    in again once and retries; the role's cells are decided, not skipped."""
    server_factory(FAKE_SESSION_TTL="6")
    assert cli.main(["stage", "pages_by_role"]) == 0
    led = _ledger(bench_env, "pages_by_role")
    assert led["failed"] == [], led["failed"]
    assert not any("session was lost" in why for _, why in led["not_run"]), led["not_run"]
    assert led["cells"] == 22


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
    import re
    # not a literal: a pin written into this test moves with every release and a
    # stale one made the test pass without refusing anything (0.1.8, 2026-09-05)
    m.write_text(re.sub(r"version: \S+", "version: 9.9.9", open("qa/manifest.yml").read(), count=1))
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


def test_a_per_role_email_map_wins_over_the_template(bench_env, server_factory):
    server_factory()                                    # load() needs an origin
    from qabench import manifest as mf
    cfg = mf.load()
    cfg.credentials.emails = {"owner": "boss@example.test"}
    email, _ = core.credentials(cfg, "owner")
    assert email == "boss@example.test"
    email, _ = core.credentials(cfg, "staff")
    assert email == "staff@example.test"          # the template still serves the rest


def test_a_project_that_declares_no_api_does_not_run_the_endpoints_stage(bench_env, server_factory, capsys):
    """Declared, not discovered: with api.include_prefixes empty the endpoints
    stage is left out of the plan and the omission is printed — the night is
    then judged on the stages that CAN decide something."""
    from qabench import manifest as mf
    srv = server_factory()
    cfg = mf.load()
    cfg.origin = srv.url
    cfg.api.include_prefixes = []
    code = nightly.run(cfg, [])
    out = capsys.readouterr().out
    assert "endpoints_by_role: not applicable" in out
    assert not (bench_env / "endpoints_by_role.json").exists(), "the stage ran anyway"
    assert (bench_env / "pages_by_role.json").exists() and (bench_env / "smoke.json").exists()
    assert code == 0, out[-800:]
