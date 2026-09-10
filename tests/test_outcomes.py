from copy import deepcopy

import pytest

from qabench.acceptance import Invalid
from qabench.outcomes import compare


@pytest.fixture
def data():
    return {"version": 1, "observed_at": "2026-09-08T00:00:00Z", "projects": ["anat", "ana-log"],
            "baseline": {"start": "2026-08-01T00:00:00Z", "end": "2026-08-29T00:00:00Z",
                         "observed_projects": ["anat"], "releases": {"anat": 10}},
            "followup": {"start": "2026-08-29T00:00:00Z", "end": "2026-09-08T00:00:00Z",
                         "observed_projects": ["anat"], "releases": {"anat": 20}},
            "incidents": [{"defect_id": "one", "episode_id": "one-original", "occurrence": "new", "project": "anat", "source": "user", "escaped": True,
                           "severity": "medium", "source_reference": "ticket:one", "reported_at": "2026-08-10T12:00:00Z"},
                          {"defect_id": "two", "episode_id": "two-original", "occurrence": "new", "project": "anat", "source": "staff", "escaped": True,
                           "severity": "high", "source_reference": "ticket:two", "reported_at": "2026-09-02T12:00:00Z"}]}


def test_rate_and_severity_are_separate_and_do_not_claim_causality(data):
    result = compare(data)
    row = result["projects"][0]
    assert row["rate_reduction_percent"] == 50
    assert row["severe_increase"] is True
    assert result["causal_reduction_proven"] is False


def test_missing_channel_coverage_is_unknown_not_zero(data):
    row = compare(data)["projects"][1]
    assert row["baseline"]["reported_escapes"] is None
    assert row["comparison"] == "insufficient_evidence"


def test_harness_and_review_findings_do_not_inflate_customer_escapes(data):
    finding = deepcopy(data["incidents"][0])
    finding.update(defect_id="harness", episode_id="harness-one", source="harness", escaped=False)
    data["incidents"].append(finding)
    baseline = compare(data)["projects"][0]["baseline"]
    assert baseline["reported_escapes"] == 1 and baseline["reports_by_source"]["harness"] == 1


def test_duplicate_reports_require_canonical_deduplication(data):
    data["incidents"].append(deepcopy(data["incidents"][0]))
    with pytest.raises(Invalid, match="duplicate"):
        compare(data)


def test_zero_exposure_cannot_claim_a_rate_improvement(data):
    data["followup"]["releases"]["anat"] = 0
    row = compare(data)["projects"][0]
    assert row["rate_reduction_percent"] is None


def test_comparison_periods_must_not_overlap(data):
    data["followup"]["start"] = "2026-08-28T00:00:00Z"
    with pytest.raises(Invalid, match="overlap"):
        compare(data)


def test_future_followup_cannot_report_improvement(data):
    data["followup"]["end"] = "2026-10-08T00:00:00Z"
    with pytest.raises(Invalid, match="completely observed"):
        compare(data)


def test_observed_zero_baseline_can_report_an_increase(data):
    data["incidents"] = data["incidents"][1:]
    row = compare(data)["projects"][0]
    assert row["comparison"] == "descriptive_only"
    assert row["rate_reduction_percent"] is None
    assert row["rate_change_per_100_releases"] == 5


def test_reopened_defect_is_a_new_episode_not_a_duplicate_report(data):
    data["incidents"][1].update(defect_id="one", episode_id="one-reopened", occurrence="reopened")
    row = compare(data)["projects"][0]
    assert row["baseline"]["escapes_by_occurrence"] == {"new": 1, "reopened": 0}
    assert row["followup"]["escapes_by_occurrence"] == {"new": 0, "reopened": 1}
