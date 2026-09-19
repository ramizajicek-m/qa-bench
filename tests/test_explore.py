"""`qabench stage explore` — the nightly independent explorer.

The session itself is a fake binary here (a shell script standing in for
`claude -p`); what is under test is the stage's CONTRACT, which is what decides
whether a night of exploration is believed:

  1. off, or no persona, or no session binary      -> 3 (did not explore), never 0;
  2. a session that leaves no report or visits nothing -> 3, and says so;
  3. a well-formed report                          -> 0, findings in the ledger;
     with `explore.blocking` each finding           -> 1;
  4. a malformed report (a finding with no steps, a shape outside a–h) -> 1;
  5. a write the fence aborted                     -> 1, whatever the report says;
  6. the fence itself: a write to a production or forbidden host is refused,
     a read is not, a write to the origin is not;
  7. the brief carries the subjects of what changed and never a test path, and a
     persona naming a role the bench does not have is refused at load.

Mutation (watched 2026-09-19): `if not visited` removed -> claim 2's
"visits nothing" case reads 0; `refused` read as [] -> claim 5 reads 0.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

from qabench import explore_page, manifest
from qabench.stages import explore

GOOD = {"persona": "staff", "surfaces_visited": ["/orders", "/orders/7"], "heuristics_applied": ["twice"],
        "findings": [{"title": "double tap saves twice", "surface": "/orders/7", "steps": ["open", "tap twice"],
                      "expected": "one row", "actual": "two rows", "shape": "a"}],
        "not_covered": ["/labels on a phone"]}


def _repo(tmp_path: Path, explore_block: str) -> Path:
    repo = tmp_path / "repo"
    (repo / "qa").mkdir(parents=True)
    (repo / "qa" / "manifest.yml").write_text(f"""project: fake
sandbox_entity: "the demo tenant"
environments:
  production: {{ url: https://prod.example.test, branch: main }}
bench:
  version: 0
  roles: [owner, staff]
  shots: {tmp_path / 'shots'}
{explore_block}
""", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                    "--allow-empty", "-m", "Orders: a double tap no longer saves twice"], check=True)
    (repo / "app.py").write_text("x = 1\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_x(): pass\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                    "-m", "Picking: the camera closes after one read"], check=True)
    return repo


def _fake_session(tmp_path: Path, report: dict | str | None, refuse: bool = False) -> Path:
    """A stand-in for `claude -p`: finds the report path in its brief and writes it."""
    body = json.dumps(report) if isinstance(report, dict) else (report or "")
    script = tmp_path / "fake-claude"
    script.write_text(f"""#!/usr/bin/env python3
import re, sys, pathlib, json
brief = sys.argv[-1]
path = pathlib.Path(re.search(r"Write JSON to `([^`]+)`", brief).group(1))
body = {body!r}
if body:
    path.write_text(body)
if {refuse!r}:
    (path.parent / "refused-writes.jsonl").write_text(json.dumps({{"method": "POST", "url": "https://prod.example.test/api/x"}}) + "\\n")
""")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


@pytest.fixture(autouse=True)
def _no_real_login_or_network(monkeypatch):
    """The stage signs in and probes egress before it spawns; neither may leave the machine here."""
    monkeypatch.setattr(explore.core, "login", lambda cfg, role, **kw: None)
    monkeypatch.setattr(explore, "reachable", lambda host, *a, **kw: False)


def _cfg(tmp_path, monkeypatch, report=GOOD, blocking=False, refuse=False, enabled=True, claude=None, extra=""):
    monkeypatch.setenv("QA_BASE_URL", "https://staging.example.test")
    fake = claude or _fake_session(tmp_path, report, refuse)
    block = f"""  explore:
    enabled: {str(enabled).lower()}
    budget_min: 1
    blocking: {str(blocking).lower()}
    claude: {fake}
    since: "10 years ago"
{extra}    personas:
      - {{ role: staff, viewport: [390, 844], who: "a picker on the warehouse floor" }}"""
    return manifest.load(_repo(tmp_path, block))


def _ledger(cfg) -> dict:
    return json.loads((cfg.shots / "explore.json").read_text())


def test_off_is_did_not_run(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, monkeypatch, enabled=False)
    assert explore.main(cfg, []) == 3


def test_a_missing_session_binary_is_did_not_run(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, monkeypatch, claude="/nonexistent/claude")
    assert explore.main(cfg, []) == 3
    assert "not on PATH" in _ledger(cfg)["not_run"][0][1]


def test_no_report_is_did_not_run(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, monkeypatch, report=None)
    assert explore.main(cfg, []) == 3
    assert "no report" in _ledger(cfg)["not_run"][0][1]


def test_a_report_that_visited_nothing_is_did_not_run(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, monkeypatch, report={**GOOD, "surfaces_visited": []})
    assert explore.main(cfg, []) == 3


def test_a_good_report_passes_and_records_its_findings(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, monkeypatch)
    assert explore.main(cfg, []) == 0
    led = _ledger(cfg)
    assert led["findings"][0]["title"] == "double tap saves twice" and led["findings"][0]["persona"] == "staff"
    assert led["personas"]["staff"]["visited"] == 2 and led["passed"] == 2      # explored + no refused write


def test_blocking_makes_every_finding_red(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, monkeypatch, blocking=True)
    assert explore.main(cfg, []) == 1
    assert any("double tap saves twice" in label for label, _ in _ledger(cfg)["failed"])


@pytest.mark.parametrize("bad", [
    {**GOOD, "findings": [{"title": "vague", "surface": "/x", "shape": "a"}]},
    {**GOOD, "findings": [{**GOOD["findings"][0], "shape": "z"}]},
    {k: v for k, v in GOOD.items() if k != "not_covered"},
    "not json at all",
])
def test_a_malformed_report_is_red(tmp_path, monkeypatch, bad):
    cfg = _cfg(tmp_path, monkeypatch, report=bad)
    assert explore.main(cfg, []) == 1


def test_a_refused_write_is_red_whatever_the_report_says(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, monkeypatch, refuse=True)
    assert explore.main(cfg, []) == 1
    assert any("the fence refused no write" == label for label, _ in _ledger(cfg)["failed"])


def test_the_fence_refuses_writes_to_production_and_forbidden_hosts_only(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, monkeypatch)
    cfg.explore.forbid_writes_to = ["webapp.legacy.test"]
    fenced = explore_page.fenced_hosts(cfg)
    assert explore_page.refused("POST", "https://prod.example.test/api/x", fenced)
    assert explore_page.refused("delete", "https://webapp.legacy.test/api/actions/y", fenced)
    assert not explore_page.refused("GET", "https://prod.example.test/orders", fenced)
    assert not explore_page.refused("POST", "https://staging.example.test/api/x", fenced)


def test_the_brief_names_what_changed_and_withholds_the_tests(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path, monkeypatch)
    changes = explore.changed(cfg)
    text = explore.brief(cfg, cfg.explore.personas[0], cfg.shots / "r.json", changes)
    assert "Picking: the camera closes after one read" in text and "app.py" in text
    assert "test_app.py" not in text
    assert "a picker on the warehouse floor" in text and "the demo tenant" in text
    assert "GOLDILOCKS" not in text and "FEDEX TOUR" in text and "SFDIPOT" in text


def test_a_persona_with_an_unknown_role_is_refused_at_load(tmp_path, monkeypatch):
    monkeypatch.setenv("QA_BASE_URL", "https://staging.example.test")
    block = "  explore:\n    enabled: true\n    personas:\n      - { role: superadmin }"
    with pytest.raises(SystemExit, match="not in bench.roles"):
        manifest.load(_repo(tmp_path, block))


def test_the_session_inherits_no_secret_from_the_job(tmp_path, monkeypatch):
    monkeypatch.setenv("RAILWAY_TOKEN", "live-deploy-token-value")
    monkeypatch.setenv("QA_STAFF_PASSWORD", "role-password-value")
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "session-auth")
    cfg = _cfg(tmp_path, monkeypatch)
    env = explore.session_env(cfg)
    assert not {"RAILWAY_TOKEN", "QA_STAFF_PASSWORD", "DATABASE_URL"} & set(env)
    assert env["ANTHROPIC_API_KEY"] == "session-auth" and env["QA_BASE_URL"] == "https://staging.example.test"
    assert "QA_SESSION_DIR" in env


def test_a_reachable_fenced_host_refuses_the_night_unless_someone_accepted_it(tmp_path, monkeypatch):
    monkeypatch.setattr(explore, "reachable", lambda host, *a, **kw: host == "prod.example.test")
    cfg = _cfg(tmp_path, monkeypatch)
    assert explore.main(cfg, []) == 3
    assert "prod.example.test" in _ledger(cfg)["not_run"][0][1]
    (tmp_path / "b").mkdir()
    accepted = _cfg(tmp_path / "b", monkeypatch,
                    extra='    accept_open_egress: "Rami 2026-09-19: the session holds no production credential"\n')
    assert explore.main(accepted, []) == 0
    assert _ledger(accepted)["egress_decision"].startswith("Rami 2026-09-19")


def test_a_dead_credential_is_did_not_explore_and_names_it(tmp_path, monkeypatch):
    def dead(cfg, role, **kw):
        raise SystemExit("no credentials for role 'staff': set QA_STAFF_PASSWORD")
    monkeypatch.setattr(explore.core, "login", dead)
    cfg = _cfg(tmp_path, monkeypatch)
    assert explore.main(cfg, []) == 3
    assert "QA_STAFF_PASSWORD" in _ledger(cfg)["not_run"][0][1]


def test_findings_are_redacted_before_they_reach_the_ledger(tmp_path, monkeypatch):
    leaky = {**GOOD, "findings": [{**GOOD["findings"][0], "actual": 'the page printed "api_key": "not-a-real-key-0000"'}]}
    cfg = _cfg(tmp_path, monkeypatch, report=leaky)
    assert explore.main(cfg, []) == 0
    assert "not-a-real-key-0000" not in (cfg.shots / "explore.json").read_text()



def test_a_rotated_refresh_cookie_is_written_back_to_the_session_cache(tmp_path, monkeypatch):
    """ana-log rotates its refresh token: the explorer's second page opened signed
    out on its first night because the cache kept the spent one (it reported that
    itself). After a page, the context's current cookie replaces the cached one."""
    import json as _json
    from types import SimpleNamespace
    from qabench import core
    monkeypatch.setenv("QA_SESSION_DIR", str(tmp_path))
    cfg = SimpleNamespace(origin="https://staging.example.test", login=SimpleNamespace(rotates=True))
    path = core._session_path(cfg, "staff")
    path.parent.mkdir(parents=True)
    path.write_text(_json.dumps({"origin": cfg.origin, "email": "s@x", "at": 1,
                                 "cookies": [{"name": "refresh", "value": "spent", "domain": "staging.example.test", "path": "/api"}]}))
    sess = SimpleNamespace(cookies=[{"name": "refresh", "value": "spent"}])
    explore_page._keep_rotated(cfg, "staff", sess, [{"name": "refresh", "value": "next", "domain": "staging.example.test",
                                                     "path": "/api", "secure": True}, {"name": "other", "value": "x"}])
    cached = _json.loads(path.read_text())["cookies"]
    assert [c["value"] for c in cached] == ["next"] and cached[0]["path"] == "/api"
