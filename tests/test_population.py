"""`qabench population` — judged on the five escapes it was built from.

Every case here is one of 2026-09-20's defects reduced to its mechanics: the
corpus keyed on a name (ACT-11), the detector that matched nothing (FRM-10), the
rule credited to every template alike (FRM-01), the class excluded by the
selector (FRM-12), and a corpus quietly narrowed back afterwards.

The two commands are real subprocesses on purpose. A fake `run` would test the
comparison and not the reading, and "the enumeration printed nothing" is the
verdict this module exists to refuse.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest
import yaml

from qabench import population

TODAY = dt.date(2026, 9, 20)


MEMBERS = Path()          # set per test by the `repo` fixture


def emit(*members: str) -> str:
    """A real command that prints these members, one per line.

    A file plus `cat` rather than a `python -c`: the point of running the two
    sides as subprocesses is that the reading is exercised, and a member with a
    space in it (`templates/proposal sign.html`) must survive both the argv
    split and the line split.
    """
    global _seq
    _seq += 1
    f = MEMBERS / f"m{_seq}.txt"
    f.write_text("\n".join(members) + ("\n" if members else ""), encoding="utf-8")
    return f"/bin/cat {f}"


_seq = 0


def nothing() -> str:
    return "/usr/bin/true"


@pytest.fixture
def repo(tmp_path):
    global MEMBERS
    MEMBERS = tmp_path / "members"
    MEMBERS.mkdir()
    (tmp_path / "qa").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ledger.md").write_text("evidence", encoding="utf-8")

    def write(guards, checks=None):
        (tmp_path / "qa" / "manifest.yml").write_text(
            yaml.safe_dump({"population": {"register": "qa/guards.yml"}, "checks": checks or {}}), encoding="utf-8")
        (tmp_path / "qa" / "guards.yml").write_text(
            yaml.safe_dump({"version": 1, "guards": guards}), encoding="utf-8"),
        return tmp_path
    return write


def guard(**over) -> dict:
    g = {
        "id": "act11-count-reporting-routes",
        "check": "C6",
        "claims": "a route that iterates a collection and reports a count reports its failures too",
        "population": {"derived_from": "ast", "cmd": emit("a", "b", "c"), "count": 3},
        "subject": {"cmd": emit("a", "b", "c")},
    }
    for k, v in over.items():
        g[k] = {**g[k], **v} if isinstance(v, dict) and isinstance(g.get(k), dict) else v
    return g


def judged(repo, **over):
    root = repo([guard(**over)])
    return population.run_population(root, {"register": "qa/guards.yml"}, today=TODAY)["rows"][0]


def test_a_guard_that_sweeps_its_whole_population_is_clean(repo):
    row = judged(repo)
    assert row["problems"] == []
    assert (row["population"], row["subject"]) == (3, 3)


def test_the_gap_is_named_member_by_member(repo):
    """FRM-01: three standalone documents the markup sweep credited the rule to."""
    row = judged(repo, subject={"cmd": emit("a")})
    assert row["missing"] == ["b", "c"]
    assert "never examined" in row["problems"][0] and "b, c" in row["problems"][0]


def test_a_subject_of_nothing_is_red_not_clean(repo):
    """FRM-10: `\\bcan_\\b` matched nothing and read exactly like a clean tree."""
    row = judged(repo, subject={"cmd": nothing()})
    assert row["subject"] == 0
    assert any("indistinguishable from a clean tree" in p for p in row["problems"])


def test_a_population_of_nothing_is_did_not_run(repo):
    """A guard cannot pass by enumerating an empty world."""
    root = repo([guard(population={"cmd": nothing(), "count": 0})])
    out = population.run_population(root, {"register": "qa/guards.yml"}, today=TODAY)
    assert out["unrunnable"] and "enumerated NOTHING" in out["rows"][0]["problems"][-1]
    assert population.run(["--repo", str(root)], today=TODAY) == 3


def test_a_population_derived_from_names_is_refused(repo):
    """ACT-11: the corpus was routes whose PATH contained batch|bulk."""
    row = judged(repo, population={"derived_from": "names"})
    assert any("refused" in p and "ACT-11" in p for p in row["problems"])


def test_an_unknown_derivation_is_refused(repo):
    row = judged(repo, population={"derived_from": "vibes"})
    assert any("derived_from must be one of" in p for p in row["problems"])


def test_a_member_the_guard_examines_outside_its_population_is_red(repo):
    """The population expression narrower than the guard: the pin would then
    ratchet on the wrong number, and the gap would read as zero."""
    row = judged(repo, subject={"cmd": emit("a", "b", "c", "d")})
    assert row["stray"] == ["d"]
    assert any("narrower than the guard" in p for p in row["problems"])


def test_a_population_that_falls_without_a_reason_is_red(repo):
    """The meta-test: a corpus re-keyed back onto a naming heuristic."""
    row = judged(repo, population={"cmd": emit("a"), "count": 3}, subject={"cmd": emit("a")})
    assert any("FELL 3 → 1" in p for p in row["problems"])


def test_a_population_that_falls_with_evidence_asks_for_the_pin(repo):
    row = judged(repo, population={"cmd": emit("a"), "count": 3, "shrunk": {
        "reason": "two routes deleted in the 09-18 cutover", "evidence": "docs/ledger.md", "date": "2026-09-18"}},
        subject={"cmd": emit("a")})
    assert row["problems"] == ["the population fell 3 → 1 and `shrunk:` explains it — set population.count to 1"]


def test_a_population_that_grows_must_raise_the_pin_in_the_same_commit(repo):
    row = judged(repo, population={"cmd": emit("a", "b", "c", "d"), "count": 3},
                 subject={"cmd": emit("a", "b", "c", "d")})
    assert any("grew 3 → 4" in p for p in row["problems"])


def test_an_unpinned_population_is_red(repo):
    row = judged(repo, population={"count": None})
    assert any("pin it" in p for p in row["problems"])


def test_an_exemption_with_evidence_and_a_date_excuses_one_member(repo):
    """FRM-12: modals a selector has to exclude — named, dated, and counted."""
    row = judged(repo, subject={"cmd": emit("a")}, exemptions=[
        {"member": "b", "reason": "a closed dialog has no options to count",
         "evidence": "docs/ledger.md", "review_by": "2026-10-15"},
        {"member": "c", "reason": "same", "evidence": "docs/ledger.md", "review_by": "2026-10-15"}])
    assert row["missing"] == [] and row["exempted"] == 2 and row["problems"] == []


def test_an_expired_exemption_is_red(repo):
    row = judged(repo, subject={"cmd": emit("a", "c")}, exemptions=[
        {"member": "b", "reason": "x", "evidence": "docs/ledger.md", "review_by": "2026-09-01"}])
    assert any("expired 2026-09-01" in p for p in row["problems"])


def test_an_exemption_whose_evidence_does_not_exist_is_red(repo):
    row = judged(repo, subject={"cmd": emit("a", "c")}, exemptions=[
        {"member": "b", "reason": "x", "evidence": "docs/nope.md", "review_by": "2026-10-15"}])
    assert any("evidence does not exist" in p for p in row["problems"])


def test_an_exemption_the_guard_now_examines_is_stale(repo):
    row = judged(repo, exemptions=[
        {"member": "b", "reason": "x", "evidence": "docs/ledger.md", "review_by": "2026-10-15"}])
    assert any("is stale" in p for p in row["problems"])


def test_a_command_that_cannot_run_is_three_never_zero(repo):
    root = repo([guard(subject={"cmd": "/bin/sh -c exit2"})])
    out = population.run_population(root, {"register": "qa/guards.yml"}, today=TODAY)
    assert out["unrunnable"]


def test_an_implemented_check_with_no_guard_is_named(repo):
    root = repo([guard()], checks={"C6": {"status": "implemented"}, "C4": {"status": "implemented"},
                                   "C5": {"status": "absent"}})
    out = population.run_population(root, {"register": "qa/guards.yml"}, today=TODAY)
    assert out["unregistered"] == ["C4"]


def test_the_cli_exits_one_on_a_gap_three_on_did_not_run_zero_when_swept(repo, capsys):
    root = repo([guard()])
    assert population.run(["--repo", str(root)], today=TODAY) == 0
    repo([guard(subject={"cmd": emit("a")})])
    assert population.run(["--repo", str(root)], today=TODAY) == 1
    repo([guard(subject={"cmd": "/bin/sh -c exit2"})])
    assert population.run(["--repo", str(root)], today=TODAY) == 3
    (root / "qa" / "guards.yml").unlink()
    assert population.run(["--repo", str(root)], today=TODAY) == 3


def test_no_register_is_three(tmp_path):
    (tmp_path / "qa").mkdir()
    (tmp_path / "qa" / "manifest.yml").write_text("checks: {}\n", encoding="utf-8")
    assert population.run(["--repo", str(tmp_path)], today=TODAY) == 3


def test_a_member_containing_a_space_stays_one_member(repo):
    row = judged(repo, population={"cmd": emit("templates/proposal sign.html", "b", "c"), "count": 3},
                 subject={"cmd": emit("b", "c")})
    assert row["missing"] == ["templates/proposal sign.html"]


def test_a_population_read_from_requirement_prose_is_a_derivation(repo):
    """GEN-03: an aggregate requirement's parts list is a denominator, and this
    one was written by example — it did not name ACT-11, which is the row the
    silent failure actually was. Prose the project maintains grows by itself
    when a row is added; the hand-written tuple could not. The refusal is on
    deriving from what the CODE is called, not on reading the spec."""
    row = judged(repo, population={"derived_from": "requirement_text",
                                   "cmd": emit("ACT-05", "ACT-11", "FRM-13", "MSG-04"), "count": 4},
                 subject={"cmd": emit("ACT-05", "MSG-04")},
                 exemptions=[{"member": "FRM-13", "reason": "SEC-04-style: a different question",
                              "evidence": "docs/ledger.md", "review_by": "2026-10-15"}])
    assert row["missing"] == ["ACT-11"] and row["exempted"] == 1
    assert row["problems"] == ["1 of 4 never examined: ACT-11"]   # the derivation itself is not a problem
