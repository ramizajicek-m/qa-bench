"""`qabench.warrant` — the one contract for a justification that has to earn its keep.

The staleness half is opt-in and has NO default, on purpose: the window is a
number, this kit's rule is that a threshold is measured rather than chosen, and
the measurement (how many of a real tracker's partial/absent reasons are stale)
was still being taken when this was written.
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


def test_staleness_is_off_unless_a_window_is_declared(root):
    """No default. A caller that wants the rule declares the number."""
    assert warrant.judge(w(), root, TODAY) == ""
    assert warrant.judge(w(verified="2020-01-01"), root, TODAY) == ""


def test_a_declared_window_makes_an_undated_reason_red(root):
    problem = warrant.judge(w(), root, TODAY, stale_after_days=30)
    assert "carries no `verified:` date" in problem and "an undated re-read is not a re-read" in problem


def test_a_reason_older_than_the_window_is_prose_pretending_to_be_evidence(root):
    """SEC-02: a row asserting a gap that was already half closed, with a target
    date anyone planning work would have planned against."""
    problem = warrant.judge(w(verified="2026-07-01"), root, TODAY, stale_after_days=30)
    assert "81 days ago" in problem and "prose pretending to be evidence" in problem


def test_a_reason_inside_the_window_stands(root):
    assert warrant.judge(w(verified="2026-09-10"), root, TODAY, stale_after_days=30) == ""
