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
