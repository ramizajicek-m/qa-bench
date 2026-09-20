"""`qabench.warrant` — the one contract for a justification that has to earn its keep.

It holds no staleness rule. One was written, opt-in and unpinned, pending the
measurement; the measurement arrived and refuted it (the oldest justification in
the tracker is three days, and both confirmed defects are in the youngest band),
so it was deleted rather than left switched off.
"""
from __future__ import annotations

import datetime as dt

import pytest

from qabench import warrant

TODAY = dt.date(2026, 9, 20)


@pytest.fixture
def root(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ledger.md").write_text("evidence", encoding="utf-8")
    return tmp_path


def w(**over):
    return {"member": "X", "reason": "a sentence a stranger would accept",
            "evidence": "docs/ledger.md", "review_by": "2026-12-01", **over}


def test_a_complete_warrant_stands(root):
    assert warrant.judge(w(), root, TODAY) == ""


@pytest.mark.parametrize("missing", ["reason", "evidence", "review_by"])
def test_every_required_field_is_required(root, missing):
    assert f"lacks {missing}" in warrant.judge(w(**{missing: None}), root, TODAY)


def test_evidence_that_has_gone_says_what_that_means(root):
    problem = warrant.judge(w(evidence="docs/gone.md"), root, TODAY)
    assert "does not exist" in problem and "nobody has read since it went" in problem


def test_an_expired_review_by_is_red(root):
    assert "expired 2026-09-01" in warrant.judge(w(review_by="2026-09-01"), root, TODAY)


def test_the_subject_field_is_the_callers(root):
    """`population` exempts a member; `distinct` exempts a pair."""
    assert warrant.judge({"pair": ["A", "B"], **{k: v for k, v in w().items() if k != "member"}},
                         root, TODAY, subject="pair") == ""
    assert "lacks pair" in warrant.judge(w(), root, TODAY, subject="pair")


def test_there_is_no_staleness_argument(root):
    """The measurement refuted it and it was deleted rather than left switched
    off. Every partial/absent reason in the tracker it was written for is
    0-7 days old; both confirmed defects are in the youngest band; an age-keyed
    window would have flagged neither at any threshold. Age is not the
    mechanism — these reasons were overtaken, not decayed."""
    import inspect
    assert "stale_after_days" not in inspect.signature(warrant.judge).parameters
    assert warrant.judge(w(verified="2020-01-01"), root, TODAY) == ""


STATUSES = {"STA-01": "implemented", "PRT-03": "implemented", "ACT-11": "absent"}


def test_a_row_justified_by_a_blocker_that_has_been_built_is_named():
    """PRF-06 says STA-01 is absent; STA-01 is implemented. The next person
    starts by building a loading indicator that already exists."""
    problems = warrant.judge_claims(
        [{"row": "PRF-06", "cites": "STA-01", "asserts": "absent"}], STATUSES, unresolved=5, unresolved_pin=5)
    assert len(problems) == 1
    assert "PRF-06 justifies itself" in problems[0] and "'implemented'" in problems[0]
    assert "plans around it" in problems[0]


def test_a_true_cross_reference_is_silent():
    assert warrant.judge_claims(
        [{"row": "X", "cites": "ACT-11", "asserts": "absent"}], STATUSES, unresolved=5, unresolved_pin=5) == []


def test_a_citation_outside_the_table_is_not_compared_to_nothing():
    problems = warrant.judge_claims(
        [{"row": "X", "cites": "TICKET-4", "asserts": "absent"}], STATUSES, unresolved=0, unresolved_pin=0)
    assert "does not hold" in problems[0] and "excluded by declaration" in problems[0]


def test_the_refusal_count_must_be_pinned():
    """An unresolved share that is not asserted is a share that can grow."""
    problems = warrant.judge_claims([], STATUSES, unresolved=5)
    assert "nothing pins that number" in problems[0]


def test_fewer_refusals_is_not_automatically_better():
    """Disabling the confidence filter collapses the count — which is exactly
    how the two withdrawn phantoms would have been attributed. The pin is what
    makes the refusal load-bearing rather than decoration."""
    problems = warrant.judge_claims([], STATUSES, unresolved=0, unresolved_pin=5)
    assert "Fewer refusals is not automatically better" in problems[0]


def test_a_malformed_claim_is_named_not_skipped():
    assert "lacks one of" in warrant.judge_claims([{"row": "X"}], STATUSES, unresolved=0, unresolved_pin=0)[0]


def test_a_line_coordinate_in_a_citation_is_refused(root):
    """Eleven rows cited clients/detail.html:12514 for a getUserMedia call. It
    now sits at 12847 — the code did not move, the file grew above it. A line
    number is a pointer that moves independently of the claim."""
    problem = warrant.judge(w(evidence="docs/ledger.md:12514"), root, TODAY)
    assert "LINE COORDINATE" in problem and "a search can find again" in problem


def test_a_member_citation_is_not_a_coordinate(root):
    """`::name` is the estate's convention for naming a member, which a search
    finds again after the file grows."""
    assert warrant.judge(w(evidence="docs/ledger.md::the voice test"), root, TODAY) == ""


def test_a_coordinate_anywhere_in_a_list_is_refused(root):
    assert "LINE COORDINATE" in warrant.judge(
        w(evidence=["docs/ledger.md", "docs/ledger.md:40"]), root, TODAY)


def test_a_row_reviewed_before_something_it_depends_on_is_stale_not_wrong():
    """GEN-03 rests on ACT-05; ACT-05 was re-reviewed the next day. Nobody has
    looked at GEN-03 since the ground moved — which is not the same as GEN-03
    being wrong, and conflating them makes people redo sound work."""
    out = warrant.judge_freshness([
        {"id": "GEN-03", "reviewed": "2026-09-20", "depends_on": ["ACT-05", "MSG-04"]},
        {"id": "ACT-05", "reviewed": "2026-09-21"},
        {"id": "MSG-04", "reviewed": "2026-09-19"}])
    assert out == ["GEN-03 is STALE: ACT-05 reviewed 2026-09-21, GEN-03 reviewed 2026-09-20 — not wrong, "
                   "but nobody has looked since the ground moved"]


def test_the_sentence_names_which_dependency_moved_and_when():
    """"GEN-03 is stale" is a chore; naming the dependency and the date is a lead."""
    out = warrant.judge_freshness([{"id": "A", "reviewed": "2026-09-01", "depends_on": ["B"]},
                                   {"id": "B", "reviewed": "2026-09-05"}])
    assert "B reviewed 2026-09-05" in out[0] and "A reviewed 2026-09-01" in out[0]


def test_a_row_reviewed_after_its_dependencies_is_fresh():
    assert warrant.judge_freshness([{"id": "A", "reviewed": "2026-09-10", "depends_on": ["B"]},
                                    {"id": "B", "reviewed": "2026-09-05"}]) == []


def test_an_undated_conclusion_is_named():
    out = warrant.judge_freshness([{"id": "A", "depends_on": ["B"]}, {"id": "B", "reviewed": "2026-09-05"}])
    assert "carries no `reviewed:` date" in out[0]


def test_a_dependency_outside_the_table_is_named():
    out = warrant.judge_freshness([{"id": "A", "reviewed": "2026-09-10", "depends_on": ["TICKET-9"]}])
    assert "which this table does not hold" in out[0]
