"""A green enclosing workflow or an old successful attempt is not proof.

Exercise the same gate CLI/workflow code will call, with GitHub's read-only
boundary replaced by recorded-shaped responses. No deploy/provider writes.
"""
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from qabench.release_gate import Refused, Unavailable, check

SHA = "a" * 40
NOW = datetime(2026, 9, 9, 18, tzinfo=timezone.utc)
PREFIX = "repos/o/r/actions"


def job(name, id=1, **overrides):
    return {"id": id, "name": name, "run_id": 20, "head_sha": SHA, "run_attempt": 2,
            "status": "completed", "conclusion": "success",
            "completed_at": "2026-09-09T17:30:00Z", **overrides}


class API:
    def __init__(self):
        self.run = {"id": 20, "workflow_id": 10, "repository": {"full_name": "o/r"},
                    "head_sha": SHA, "head_branch": "main", "event": "schedule",
                    "run_attempt": 2, "status": "in_progress", "conclusion": None,
                    "run_started_at": "2026-09-09T17:00:00Z"}
        self.jobs = [job("unit"), job("browser", 2), job("promote", 3,
                     status="in_progress", conclusion=None, completed_at=None)]
        self.latest = 20
        self.calls = []
        self.page_size = 100

    def __call__(self, path):
        self.calls.append(path)
        if path == PREFIX + "/workflows/qa-nightly.yml":
            return {"id": 10, "path": ".github/workflows/qa-nightly.yml"}
        if path.startswith(PREFIX + "/workflows/10/runs?"):
            assert f"head_sha={SHA}" in path
            assert "branch=main" in path
            assert "event=" in path
            assert "status=success" not in path
            return {"workflow_runs": [{"id": self.latest}]}
        if path == PREFIX + "/runs/20":
            return deepcopy(self.run)
        if path.startswith(PREFIX + "/runs/20/attempts/2/jobs?"):
            page = int(path.rsplit("page=", 1)[1])
            start = (page - 1) * self.page_size
            return {"total_count": len(self.jobs), "jobs": deepcopy(self.jobs[start:start+self.page_size])}
        raise AssertionError(f"unexpected API request {path}")


def evaluate(api=None, **overrides):
    args = dict(repo="o/r", sha=SHA, workflow="qa-nightly.yml", branch="main",
                required=["unit", "browser"], events=["schedule", "workflow_dispatch"],
                now=NOW, fetch=api or API())
    return check(**(args | overrides))


def test_completed_prerequisites_pass_while_parent_is_dispatching():
    result = evaluate()
    assert result["status"] == "accepted"
    assert result["attempt"] == 2
    assert [j["name"] for j in result["required_jobs"]] == ["unit", "browser"]


def test_friday_push_proof_can_accompany_fresh_monday_night():
    api = API()
    api.run.update(event="push", run_started_at="2026-09-04T17:00:00Z")
    for item in api.jobs[:2]:
        item["completed_at"] = "2026-09-04T17:30:00Z"
    with pytest.raises(Refused, match="stale"):
        evaluate(api, events=["push"])
    assert evaluate(api, events=["push"], immutable_push_evidence=True)["status"] == "accepted"
    assert evaluate()["status"] == "accepted"  # Fresh deployed proof is still required independently.
    api.jobs[0]["conclusion"] = "failure"
    with pytest.raises(Refused, match="unit"):
        evaluate(api, events=["push"], immutable_push_evidence=True)


def test_deployed_evidence_cannot_disable_freshness():
    with pytest.raises(Refused, match="only for push"):
        evaluate(immutable_push_evidence=True)


def test_text_false_cannot_enable_immutable_evidence():
    with pytest.raises(Refused, match="must be a boolean"):
        evaluate(events=["push"], immutable_push_evidence="false")


@pytest.mark.parametrize("field,value", [("head_sha", "b" * 40), ("head_branch", "feature/x"),
    ("workflow_id", 99), ("event", "pull_request"), ("repository", {"full_name": "other/repo"})])
def test_wrong_run_identity_refuses(field, value):
    api = API()
    api.run[field] = value
    with pytest.raises(Refused, match="identity"):
        evaluate(api)


@pytest.mark.parametrize("status,conclusion", [("completed", "skipped"), ("completed", "failure"),
    ("completed", "cancelled"), ("queued", None), ("in_progress", None)])
def test_each_required_job_must_finish_successfully(status, conclusion):
    api = API()
    api.jobs[1].update(status=status, conclusion=conclusion)
    with pytest.raises(Refused, match="browser"):
        evaluate(api)


def test_missing_job_cannot_be_replaced_by_similar_name():
    api = API()
    api.jobs[1]["name"] = "browser-summary"
    with pytest.raises(Refused, match="did not run"):
        evaluate(api)


def test_all_matrix_jobs_must_pass():
    api = API()
    api.jobs[1]["name"] = "browser (desktop)"
    api.jobs.append(job("browser (phone)", 4, conclusion="failure"))
    with pytest.raises(Refused, match="phone"):
        evaluate(api, required=["unit", "browser (desktop)", "browser (phone)"])
    api.jobs[-1]["conclusion"] = "success"
    assert evaluate(api, required=["unit", "browser (desktop)", "browser (phone)"])["status"] == "accepted"
    api.jobs.pop()
    with pytest.raises(Refused, match="phone"):
        evaluate(api, required=["unit", "browser (desktop)", "browser (phone)"])
    with pytest.raises(Refused, match="browser"):
        evaluate(api)  # A base name cannot count as the whole matrix.


def test_jobs_on_later_pages_are_measured():
    api = API()
    api.page_size = 1
    assert evaluate(api)["status"] == "accepted"
    assert any("page=3" in path for path in api.calls)
    api.jobs[1]["conclusion"] = "failure"
    with pytest.raises(Refused):
        evaluate(api)


def test_rerun_supersedes_the_requested_old_attempt():
    with pytest.raises(Refused, match="superseded"):
        evaluate(run_id=20, attempt=1)


def test_newer_run_prevents_falling_back_to_an_older_green_run():
    api = API()
    api.latest = 21
    with pytest.raises(Refused, match="latest"):
        evaluate(api, run_id=20, attempt=2)


def test_failed_new_attempt_is_not_replaced_with_previous_jobs():
    api = API()
    api.jobs[0]["conclusion"] = "failure"
    with pytest.raises(Refused, match="unit"):
        evaluate(api)
    assert all("attempts/1/" not in path for path in api.calls)


@pytest.mark.parametrize("when", ["2026-09-07T17:00:00Z", "2026-09-10T17:00:00Z"])
def test_stale_or_future_evidence_refuses(when):
    api = API()
    api.run["run_started_at"] = when
    with pytest.raises(Refused, match="stale or future"):
        evaluate(api)


def test_github_inherited_successful_jobs_remain_valid_same_sha_proof():
    api = API()
    api.jobs[0]["completed_at"] = "2026-09-09T16:00:00Z"
    api.jobs[0]["run_attempt"] = 1
    result = evaluate(api)
    assert result["required_jobs"][0]["attempt"] == 1
    api.jobs[0]["completed_at"] = "2026-09-07T16:00:00Z"
    with pytest.raises(Refused, match="stale"):
        evaluate(api)


def test_a_new_run_during_verification_supersedes_the_selected_run():
    api = API()
    def fetch(path):
        value = api(path)
        if "/jobs?" in path:
            api.latest = 21
        return value
    with pytest.raises(Refused, match="newer eligible"):
        evaluate(fetch=fetch)


@pytest.mark.parametrize("repository", [None, [], {"full_name": None}])
def test_malformed_nested_identity_is_unavailable(repository):
    api = API()
    api.run["repository"] = repository
    with pytest.raises(Unavailable, match="identity"):
        evaluate(api)


def test_future_job_attempt_refuses():
    api = API()
    api.jobs[0]["run_attempt"] = 3
    with pytest.raises(Refused, match="future attempt"):
        evaluate(api)


def test_rerun_during_pagination_refuses():
    api = API()
    def fetch(path):
        value = api(path)
        if path.endswith("/runs/20") and api.calls.count(path) == 2:
            value["run_attempt"] = 3
        return value
    with pytest.raises(Refused, match="changed"):
        evaluate(fetch=fetch)


def test_duplicate_jobs_are_incomplete_evidence():
    api = API()
    api.jobs.append(deepcopy(api.jobs[0]))
    with pytest.raises(Unavailable, match="duplicate"):
        evaluate(api)


def test_failed_read_is_unavailable_not_no_runs():
    def fetch(path):
        raise Unavailable("unreachable")
    with pytest.raises(Unavailable):
        evaluate(fetch=fetch)


@pytest.mark.parametrize("options", [{"sha": "a" * 7}, {"required": []}, {"attempt": 1},
    {"workflow": "../../night.yml"}, {"max_age_hours": 0}, {"events": []}])
def test_invalid_contract_cannot_obtain_a_verdict(options):
    api = API()
    with pytest.raises(Refused):
        evaluate(api, **options)
    assert api.calls == []
