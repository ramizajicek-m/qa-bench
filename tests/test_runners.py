"""runners: what the shared machine is running, from every project at once."""
import datetime as dt

from qabench import report, runners

NOW = dt.datetime(2026, 9, 21, 10, 0, tzinfo=dt.timezone.utc)


def fake(table):
    def fetch(path):
        for k, v in table.items():
            if path.startswith(k):
                return v
        return report.UNREADABLE
    return fetch


def test_the_other_repositorys_job_is_named_with_its_runner_and_age():
    """ana-log waited an hour on a runner busy with another repo's work, and could not see it."""
    table = {
        "repos/a/ana/actions/runs?status=in_progress": {"workflow_runs": []},
        "repos/a/ana/actions/runs?status=queued": {"workflow_runs": [
            {"name": "tests", "head_sha": "abc", "created_at": "2026-09-21T09:00:00Z"}]},
        "repos/t/tha/actions/runs?status=in_progress": {"workflow_runs": [
            {"id": 7, "name": "CI", "head_sha": "def", "run_started_at": "2026-09-21T09:40:00Z"}]},
        "repos/t/tha/actions/runs/7/jobs": {"jobs": [
            {"status": "in_progress", "name": "unit", "runner_name": "mac-1", "started_at": "2026-09-21T09:45:00Z"}]},
        "repos/t/tha/actions/runs?status=queued": {"workflow_runs": []},
    }
    out = runners.survey([{"repo": "a/ana"}, {"repo": "t/tha"}], fetch=fake(table), now=NOW)
    assert out["running"] == [{"repo": "t/tha", "workflow": "CI", "sha": "def", "branch": "", "job": "unit",
                               "runner": "mac-1", "for": "15m"}]
    assert out["queued"][0]["waiting"] == "1h00m"


def test_a_repository_it_cannot_read_is_unreadable_not_empty():
    out = runners.survey([{"repo": "x/y"}], fetch=fake({}), now=NOW)
    assert out["running"] == [] and len(out["unreadable"]) == 2


def test_exit_three_when_nothing_could_be_read(tmp_path):
    est = tmp_path / "e.yml"
    est.write_text("projects:\n  - repo: x/y\n")
    assert runners.run(["--estate", str(est)], echo=lambda *_: None, fetch=fake({})) == 3
    ok = fake({"repos/x/y/actions/runs": {"workflow_runs": []}})
    assert runners.run(["--estate", str(est)], echo=lambda *_: None, fetch=ok) == 0


def test_a_staging_behind_its_newest_green_commit_is_named():
    """tharros 2026-09-21: six pushes, every deploy SKIPPED, staging on one commit all morning, nothing said so."""
    table = {"repos/t/tha/commits?sha=main": [{"sha": "ff8d68e0e1"}],
             "repos/t/tha/actions/runs?head_sha=ff8d68e0e1": {"workflow_runs": [
                 {"updated_at": "2026-09-21T09:00:00Z", "conclusion": "success"}]},
             "repos/t/tha/compare/b74ae81...ff8d68e0e1": {"status": "ahead"},
             "repos/t/tha/compare/1234567...ff8d68e0e1": {"status": "behind"}}
    rows = runners.served([{"repo": "t/tha", "staging": "https://s/health", "main": "main"}],
                          fetch=fake(table), health=lambda url: "b74ae81", now=NOW)
    assert rows[0]["state"] == "BEHIND" and rows[0]["green_for"] == "1h00m"
    ok = runners.served([{"repo": "t/tha", "staging": "https://s/health", "main": "main"}],
                        fetch=fake(table), health=lambda url: "ff8d68e0e1", now=NOW)
    assert ok[0]["state"] == "ok"
    gone = runners.served([{"repo": "t/tha", "staging": "https://s/health", "main": "main"}],
                          fetch=fake(table), health=lambda url: None, now=NOW)
    assert gone[0]["state"] == "UNREADABLE"


def test_a_staging_serving_a_descendant_of_green_is_not_behind():
    """The first version compared strings and called ana-log's staging behind while it served a newer commit."""
    table = {"repos/t/tha/commits?sha=main": [{"sha": "ff8d68e0e1"}],
             "repos/t/tha/actions/runs?head_sha=ff8d68e0e1": {"workflow_runs": [
                 {"updated_at": "2026-09-21T09:00:00Z", "conclusion": "success"}]},
             "repos/t/tha/compare/1234567...ff8d68e0e1": {"status": "behind"}}
    rows = runners.served([{"repo": "t/tha", "staging": "https://s/health", "main": "main"}],
                          fetch=fake(table), health=lambda url: "1234567", now=NOW)
    assert rows[0]["state"] == "ahead of green"


def test_served_exits_one_when_a_staging_is_behind(tmp_path):
    est = tmp_path / "e.yml"
    est.write_text("projects:\n  - repo: t/tha\n    staging: https://s/health\n    main: main\n")
    table = {"repos/t/tha/actions/runs?status": {"workflow_runs": []},
             "repos/t/tha/commits?sha=main": [{"sha": "ff8d68e0e1"}],
             "repos/t/tha/actions/runs?head_sha=ff8d68e0e1": {"workflow_runs": [
                 {"updated_at": "2026-09-21T09:00:00Z", "conclusion": "success"}]},
             "repos/t/tha/compare/b74ae81...ff8d68e0e1": {"status": "ahead"}}
    assert runners.run(["--estate", str(est), "--served"], echo=lambda *_: None, fetch=fake(table),
                       health=lambda url: "b74ae81") == 1
    assert runners.run(["--estate", str(est)], echo=lambda *_: None, fetch=fake(table),
                       health=lambda url: "b74ae81") == 0


def test_behind_names_the_mechanism_it_can_see():
    """Three causes on 2026-09-21, three responses: a failing `drift` check, a stuck platform status, neither."""
    base = {"repos/t/tha/commits?sha=main": [{"sha": "ff8d68e0e1"}],
            "repos/t/tha/actions/runs?head_sha=ff8d68e0e1": {"workflow_runs": [
                {"updated_at": "2026-09-21T09:00:00Z", "conclusion": "success"}]},
            "repos/t/tha/compare/b74ae81...ff8d68e0e1": {"status": "ahead"}}
    proj = [{"repo": "t/tha", "staging": "https://s/health", "main": "main"}]
    drift = {**base, "repos/t/tha/commits/ff8d68e0e1/check-runs": {"check_runs": [
        {"name": "unit", "conclusion": "success"}, {"name": "drift", "conclusion": "failure"}]}}
    assert "drift" in runners.served(proj, fetch=fake(drift), health=lambda u: "b74ae81", now=NOW)[0]["why"]
    stuck = {**base, "repos/t/tha/commits/ff8d68e0e1/check-runs": {"check_runs": []},
             "repos/t/tha/commits/ff8d68e0e1/status": {"statuses": [
                 {"context": "railway", "state": "pending", "description": "Railway is deploying"}]}}
    assert "PENDING" in runners.served(proj, fetch=fake(stuck), health=lambda u: "b74ae81", now=NOW)[0]["why"]
    neither = {**base, "repos/t/tha/commits/ff8d68e0e1/check-runs": {"check_runs": []},
               "repos/t/tha/commits/ff8d68e0e1/status": {"statuses": []}}
    assert "platform refusal" in runners.served(proj, fetch=fake(neither), health=lambda u: "b74ae81", now=NOW)[0]["why"]


def test_the_newest_green_is_the_first_commit_in_history_whose_pushes_all_passed():
    """A red newest commit is skipped; a cancelled (superseded) one is not green either."""
    table = {"repos/t/tha/commits?sha=main": [{"sha": "aaaaaaa000"}, {"sha": "bbbbbbb000"}, {"sha": "ff8d68e0e1"}],
             "repos/t/tha/actions/runs?head_sha=aaaaaaa000": {"workflow_runs": [{"conclusion": "failure"}]},
             "repos/t/tha/actions/runs?head_sha=bbbbbbb000": {"workflow_runs": [{"conclusion": "cancelled"}]},
             "repos/t/tha/actions/runs?head_sha=ff8d68e0e1": {"workflow_runs": [
                 {"conclusion": "success", "updated_at": "2026-09-21T09:50:00Z"}]}}
    rows = runners.served([{"repo": "t/tha", "staging": "https://s/health", "main": "main"}],
                          fetch=fake(table), health=lambda u: "ff8d68e0e1", now=NOW)
    assert rows[0]["newest_green"] == "ff8d68e0e" and rows[0]["state"] == "ok"


def test_a_commit_with_one_red_push_run_is_not_green_and_the_first_green_wins():
    table = {"repos/t/tha/commits?sha=main": [{"sha": "aaaaaaa000"}, {"sha": "ccccccc000"}, {"sha": "ff8d68e0e1"}],
             "repos/t/tha/actions/runs?head_sha=aaaaaaa000": {"workflow_runs": [
                 {"conclusion": "success"}, {"conclusion": "failure"}]},
             "repos/t/tha/actions/runs?head_sha=ccccccc000": {"workflow_runs": [
                 {"conclusion": "success", "updated_at": "2026-09-21T09:55:00Z"}]},
             "repos/t/tha/actions/runs?head_sha=ff8d68e0e1": {"workflow_runs": [
                 {"conclusion": "success", "updated_at": "2026-09-21T09:50:00Z"}]}}
    rows = runners.served([{"repo": "t/tha", "staging": "https://s/health", "main": "main"}],
                          fetch=fake(table), health=lambda u: "ccccccc000", now=NOW)
    assert rows[0]["newest_green"] == "ccccccc00" and rows[0]["state"] == "ok"


def test_every_mechanism_is_named_not_the_first():
    """tharros ff8d68e: a failed drift check AND green 2 h 15 m after the push — past Railway's 2 h limit."""
    table = {"repos/t/tha/commits?sha=main": [{"sha": "ff8d68e0e1"}],
             "repos/t/tha/actions/runs?head_sha=ff8d68e0e1": {"workflow_runs": [
                 {"conclusion": "success", "created_at": "2026-09-21T09:49:00Z", "updated_at": "2026-09-21T12:04:00Z"}]},
             "repos/t/tha/compare/b74ae81...ff8d68e0e1": {"status": "ahead"},
             "repos/t/tha/commits/ff8d68e0e1/check-runs": {"check_runs": [{"name": "drift", "conclusion": "failure"}]},
             "repos/t/tha/commits/ff8d68e0e1/status": {"statuses": []}}
    why = runners.served([{"repo": "t/tha", "staging": "https://s/health", "main": "main"}],
                         fetch=fake(table), health=lambda u: "b74ae81", now=NOW)[0]["why"]
    assert "drift" in why and "2 h" in why and "AND" in why
