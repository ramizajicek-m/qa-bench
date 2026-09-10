"""C8: ready work is explicit; clean alone does not mean ready or shipped."""
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from qabench.acceptance import Invalid
from qabench.delivery import evaluate

NOW = datetime(2026, 9, 9, 18, tzinfo=timezone.utc)


@pytest.fixture
def records():
    snapshot = {"version": 1, "base_sha": "b" * 40, "observed_at": "2026-09-09T18:00:00Z",
                "worktrees": [{"worktree": "/owned/change", "head": "a" * 40, "dirty": False,
                               "ahead": 3, "behind": 0, "observation": "local_git"}]}
    ledger = {"version": 1, "items": [{"worktree": "/owned/change", "owner": "implementer",
               "candidate": "a" * 40, "ready_at": "2026-09-09T13:00:00Z"}]}
    return snapshot, ledger


def review(records):
    return evaluate(*records, now=NOW)


def test_ready_unmerged_work_is_overdue_and_escalated(records):
    row = review(records)["worktrees"][0]
    assert row["ready_age_hours"] == 5
    assert len(row["findings"]) == 2
    assert row["remote_state"] == "not_observed"


@pytest.mark.parametrize("dirty", [False, True])
def test_undeclared_work_is_reported_without_judging_it(records, dirty):
    records[1]["items"].clear()
    records[0]["worktrees"][0]["dirty"] = dirty
    row = review(records)["worktrees"][0]
    assert not row["findings"] and row["notes"]


def test_blocker_does_not_reset_ready_clock(records):
    records[1]["items"][0]["blocker"] = "waiting for an available runner"
    result = review(records)
    assert result["status"] == "failed"
    assert result["worktrees"][0]["ready_age_hours"] == 5


def test_park_requires_reason_and_expiry_then_expired_work_escalates(records):
    item = records[1]["items"][0]
    item["parked"] = {"until": "2026-09-10T18:00:00Z"}
    with pytest.raises(Invalid, match="reason"):
        review(records)
    item["parked"]["reason"] = "user explicitly paused verification"
    assert review(records)["status"] == "observed"
    item["parked"]["until"] = "2026-09-09T17:00:00Z"
    assert "parking expired" in review(records)["worktrees"][0]["findings"]


@pytest.mark.parametrize("field,value", [("dirty", True), ("head", "c" * 40)])
def test_old_readiness_cannot_authorize_changed_work(records, field, value):
    records[0]["worktrees"][0][field] = value
    assert "readiness no longer matches" in review(records)["worktrees"][0]["findings"][0]


def test_local_integration_does_not_claim_remote_deployment(records):
    records[0]["worktrees"][0]["ahead"] = 0
    result = review(records)
    assert result["status"] == "observed"
    assert result["worktrees"][0]["remote_state"] == "not_observed"


def test_missing_ready_worktree_remains_a_finding(records):
    records[0]["worktrees"][0]["worktree"] = "/another/worktree"
    assert review(records)["worktrees"][-1]["findings"] == ["declared ready worktree is missing from inventory"]


def test_stale_inventory_is_not_a_healthy_observation(records):
    records[0]["observed_at"] = "2026-09-09T17:00:00Z"
    with pytest.raises(Invalid, match="stale"):
        review(records)


def test_duplicate_readiness_declarations_are_rejected(records):
    records[1]["items"].append(deepcopy(records[1]["items"][0]))
    with pytest.raises(Invalid, match="duplicate"):
        review(records)
