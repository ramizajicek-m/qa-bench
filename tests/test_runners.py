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
