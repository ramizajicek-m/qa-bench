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
        "undecided": "routes that report no count at all",
        "claims_faculty": "what the route DOES at runtime",
        "unit": "one route handler",
        "population": {"derived_from": "ast", "faculty": "static parse", "cmd": emit("a", "b", "c"), "count": 3},
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
    assert len(row["problems"]) == 1
    assert row["problems"][0].startswith("the population fell 3 → 1 and `shrunk:` explains it")


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


def test_an_empty_live_corpus_is_allowed_only_when_the_detector_is_proven(repo):
    """A cross-reference check over a 109-row tracker found exactly one real
    defect; correct it and the scan resolves ZERO. A guard whose only comparison
    disappears the moment you fix what it found cannot fail afterwards, and an
    empty corpus reads exactly like a clean table. Capability and corpus are two
    claims."""
    bare = judged(repo, population={"cmd": nothing(), "count": 0}, subject={"cmd": nothing()})
    assert bare["unrunnable"] and "Declare a `capability:` self-test" in bare["problems"][-1]

    proven = judged(repo, capability=cap(), population={"cmd": nothing(), "count": 0},
                    subject={"cmd": nothing()})
    assert proven["problems"] == [] and proven["capability"] is True
    assert "live corpus is EMPTY" in proven["note"] and "proven elsewhere" in proven["note"]


def cap(**over) -> dict:
    """A capability that proves BOTH halves: it fires, and it stays silent on a
    REAL near-miss out of the tree."""
    c = {"plausible": "[1, 21]; a ratio of 1.0 on rendered text is unreachable",
         "fires": [{"cmd": emit("caught the stale citation"), "from": "docs/ledger.md",
                    "was": "PRF-06 justifies itself by STA-01 being absent"}],
         "silent": [{"cmd": emit("silent"), "from": "docs/ledger.md",
                     "was": "the one thing that was missing is now supplied by the PRT-03 work"}]}
    c.update(over)
    return c


def test_a_capability_with_no_negative_case_is_refused_by_name(repo):
    """An all-positives self-test proves a detector FIRES, never that it
    DISCRIMINATES — FRM-04's switch tested against the cases in the switch, and
    over an empty corpus indistinguishable from a detector that fires on
    everything."""
    row = judged(repo, capability={"fires": [{"cmd": emit("caught it"), "from": "docs/ledger.md",
                                              "was": "the known bypass"}]})
    assert any("no `silent:` — REFUSED by name" in p and "FIRES, never that it DISCRIMINATES" in p
               for p in row["problems"])


def test_a_near_miss_must_be_real(repo):
    """Out of the tree, not written to be easy to pass."""
    row = judged(repo, capability=cap(silent=[{"cmd": emit("silent"), "from": "docs/invented.md",
                                               "was": "a sentence nobody wrote"}]))
    assert any("does not exist" in p and "must be REAL, out of the tree" in p for p in row["problems"])


def test_a_near_miss_names_the_thing_it_stands_for(repo):
    row = judged(repo, capability=cap(silent=[{"cmd": emit("silent")}]))
    assert any("lacks from, was" in p for p in row["problems"])


def test_a_silent_case_that_fires_is_red(repo):
    """The near-miss command must pass; a detector that fires on it is not
    discriminating, whatever its positive case says."""
    row = judged(repo, capability=cap(silent=[{"cmd": "/bin/sh -c exit2", "from": "docs/ledger.md",
                                               "was": "the past-tense mention"}]))
    assert row["unrunnable"] and "capability self-test did not pass" in row["problems"][0]


def test_a_detector_whose_self_test_fails_is_red_whatever_its_scan_says(repo):
    """The converse of FRM-10: a detector that quietly stopped detecting over a
    NON-empty corpus. The capability runs on every invocation, not only when the
    corpus is empty."""
    row = judged(repo, capability=cap(fires=[{"cmd": "/bin/sh -c exit2", "from": "docs/ledger.md",
                                              "was": "the known bypass"}]))
    assert row["unrunnable"] and "capability self-test did not pass" in row["problems"][0]
    assert "is not proven, whatever its live scan reports" in row["problems"][0]


def test_a_proven_detector_over_a_full_corpus_still_compares(repo):
    row = judged(repo, capability=cap(), subject={"cmd": emit("a")})
    assert row["capability"] is True and row["missing"] == ["b", "c"]


def test_a_population_keyed_on_the_marker_the_fix_adds_is_refused(repo):
    """STA-02: `class="empty-state"` is what each conversion ADDED, so the
    population was the set of things already fixed and the ratchet's 75 → 38 → 0
    measured the conversion, not the surface. The screen that was never in the
    ratchet did not survive it — it was never in it."""
    row = judged(repo, population={"derived_from": "conversion_marker"})
    assert any("refused" in p and "measured the conversion, not the surface" in p for p in row["problems"])


def test_the_other_marker_derivations_are_refused_too(repo):
    for how in ("class_attribute", "marker"):
        row = judged(repo, population={"derived_from": how})
        assert any("refused" in p for p in row["problems"]), how


def test_the_union_of_two_honest_corpora_can_still_miss_the_requirement(repo):
    """STA-02: an AnatEmpty-call sweep and a hand-rolled-markup ratchet, both
    sound, and a list dropping a sentence into a plain table cell is neither —
    sanctioned so not hand-rolled, not AnatEmpty so never checked for why and
    action. Each corpus is a proper subset of the claim and so is their union."""
    row = judged(repo, population={"cmd": emit("a", "b", "c"), "count": 3},
                 subject={"cmd": None, "detectors": [{"name": "anat-empty-calls", "cmd": emit("a"), "proven_by": "tests/test_x.py::test_anat-empty-calls"},
                                                    {"name": "hand-rolled-markup", "cmd": emit("b"), "proven_by": "tests/test_x.py::test_hand-rolled-markup"}]})
    assert row["detectors"] == {"anat-empty-calls": 1, "hand-rolled-markup": 1}
    assert row["missing"] == ["c"]
    assert "no detector covers: c" in row["note"]
    assert "approves another way" in row["note"]


def test_detectors_that_together_cover_the_requirement_are_clean(repo):
    row = judged(repo, subject={"cmd": None, "detectors": [{"name": "one", "cmd": emit("a", "b"), "proven_by": "tests/test_x.py::test_one"},
                                                          {"name": "two", "cmd": emit("c"), "proven_by": "tests/test_x.py::test_two"}]})
    assert row["problems"] == [] and row["subject"] == 3


def test_a_subject_names_cmd_or_detectors_not_both(repo):
    row = judged(repo, subject={"cmd": emit("a"), "detectors": [{"name": "one", "cmd": emit("a"), "proven_by": "tests/test_x.py::test_one"}]})
    assert row["problems"] == ["a subject names `cmd` OR `detectors`, not both"]


def test_a_detector_that_cannot_run_is_did_not_run(repo):
    row = judged(repo, subject={"cmd": None, "detectors": [{"name": "one", "cmd": emit("a"), "proven_by": "tests/test_x.py::test_one"},
                                                          {"name": "two", "cmd": "/bin/sh -c exit2", "proven_by": "tests/test_x.py::test_two"}]})
    assert row["unrunnable"]


def test_a_reachability_population_is_a_derivation(repo):
    """ACT-07: 146 dialogs have an id, 133 delegate their close through the
    helper that prompts for unsaved changes, 12 close directly. The helper is
    correct and the corpus is the entire defect, so the population is not a set
    of files — it is everything whose path REACHES the mechanism, and the
    complement is the finding."""
    row = judged(repo, population={"derived_from": "reachability",
                                   "cmd": emit("add-modal", "customers", "vehicle"), "count": 3},
                 subject={"cmd": emit("customers", "vehicle")})
    assert row["missing"] == ["add-modal"]
    assert not any("refused" in p or "must be one of" in p for p in row["problems"])


def reachy(**over):
    """A reach guard: the population is every call site, the subject is those
    that go through the blessed helper. Paired by default with the property
    guard that moves the opposite way, since the module now requires it."""
    g = {"kind": "reach", "for": "property", "paired_with": "uses-the-result-without-testing-it",
         "population": {"derived_from": "ast", "cmd": emit("a", "b", "c", "d"), "count": 4},
         "subject": {"cmd": emit("a")}}
    g.update(over)
    return g


def test_a_reach_guard_without_a_complement_is_refused(repo):
    """20% reach would have started a rewrite. A reach number is a denominator,
    and a denominator with no coverage-by-other-means measurement is a verdict
    without a population."""
    row = judged(repo, **reachy())
    assert any("MUST declare `complement:`" in p and "109, not 783" in p for p in row["problems"])


def test_the_complement_is_partitioned_and_only_the_residue_is_a_finding(repo):
    """Bypassing a helper is not the same as being uncovered."""
    row = judged(repo, **reachy(complement=[{"name": "global wrappers", "cmd": emit("b"), "proven_by": "tests/test_x.py::test_global"},
                                            {"name": "checks status itself", "cmd": emit("c"), "proven_by": "tests/test_x.py::test_checks"}]))
    assert row["covered_by"] == {"global wrappers": 1, "checks status itself": 1}
    assert row["missing"] == ["d"]
    assert "leaving 1 covered by NOTHING, which is the actionable number" in row["note"]
    assert any("covered by neither the helper nor any declared layer: d" in p for p in row["problems"])


def test_a_fully_covered_complement_is_clean(repo):
    row = reach_judged(repo, complement=[{"name": "global wrappers", "cmd": emit("b", "c", "d"),
                                          "proven_by": "tests/test_x.py::test_global"}])
    assert row["problems"] == [] and row["missing"] == []
    assert "leaving 0 covered by NOTHING" in row["note"]


def test_a_layer_is_counted_once_in_the_order_declared(repo):
    """Overlapping layers must not double-count the same bypassing site."""
    row = judged(repo, **reachy(complement=[{"name": "first", "cmd": emit("b", "c"), "proven_by": "tests/test_x.py::test_first"},
                                            {"name": "second", "cmd": emit("b", "c", "d"), "proven_by": "tests/test_x.py::test_second"}]))
    assert row["covered_by"] == {"first": 2, "second": 1}


def test_a_sweep_guard_is_unaffected_by_the_reach_rules(repo):
    row = judged(repo, subject={"cmd": emit("a")})
    assert row["missing"] == ["b", "c"] and row["covered_by"] == {}


def test_a_complement_layer_that_cannot_run_is_did_not_run(repo):
    """A layer that failed to run would otherwise cover nothing and silently
    inflate the residue — a finding invented by a broken command."""
    row = judged(repo, **reachy(complement=[{"name": "wrappers", "cmd": "/bin/sh -c exit2", "proven_by": "tests/test_x.py::test_wrappers"}]))
    assert row["unrunnable"] and row["missing"] != ["d"]


def sized(n) -> str:
    return emit(str(n))


def test_a_transform_that_guts_the_corpus_is_red(repo):
    """Stripping comments with a DOTALL `/*.*?*/` blanked 58%, 73% and 76% of
    three real files, and two checks had already been watched going green over
    the gutted corpus and recorded as mutations passed. A destroyed corpus
    reports exactly like a clean one."""
    row = judged(repo, transform=[{"name": "strip comments", "before": sized(100000),
                                   "after": sized(42000), "keeps": 0.9}])
    assert any("kept 42%" in p and "reports EXACTLY like a clean tree" in p for p in row["problems"])
    assert "passing over nothing" in row["problems"][0]


def test_a_transform_inside_its_declared_shrink_passes(repo):
    row = judged(repo, transform=[{"name": "strip comments", "before": sized(100000),
                                   "after": sized(95000), "keeps": 0.9}])
    assert row["problems"] == []


def test_a_transform_must_declare_what_it_keeps(repo):
    row = judged(repo, transform=[{"name": "strip comments", "before": sized(100), "after": sized(50)}])
    assert "needs `before:`, `after:` and `keeps:`" in row["problems"][0]


def test_a_corpus_empty_before_the_transform_is_named(repo):
    row = judged(repo, transform=[{"name": "strip", "before": sized(0), "after": sized(0), "keeps": 0.9}])
    assert "there was nothing to transform" in row["problems"][0]


def test_a_transform_whose_measurement_cannot_run_is_did_not_run(repo):
    row = judged(repo, transform=[{"name": "strip", "before": "/bin/sh -c exit2",
                                   "after": sized(1), "keeps": 0.9}])
    assert row["unrunnable"]


def test_the_derivation_travels_with_the_numbers(repo):
    """Two sessions derived the same population and got 17 and 12, both
    sincerely, and neither number said which to trust."""
    assert judged(repo)["derived_from"] == "ast"
    assert judged(repo, population={"derived_from": "reachability"})["derived_from"] == "reachability"


def test_a_known_positive_must_be_a_real_case_not_a_bare_command(repo):
    """A detector is written from a MEMORY of the instance it was built for. A
    verifier reported 16 of 23 verified and had the one independently confirmed
    bypass in the CLEARED list; re-running found nothing, re-reading found
    nothing, and checking the case whose answer was already known found it."""
    row = judged(repo, capability=cap(fires=emit("caught it")))
    assert any("must be a list of REAL known-positives" in p and "MEMORY of the instance" in p
               for p in row["problems"])


def test_a_known_positive_names_where_it_comes_from(repo):
    row = judged(repo, capability=cap(fires=[{"cmd": emit("caught it"), "from": "docs/invented.md",
                                              "was": "a case nobody has"}]))
    assert any("must be REAL, out of the tree" in p for p in row["problems"])


def test_a_guard_must_say_what_it_does_not_judge(repo):
    """ACT-05 swept 146 dialogs honestly and its population WAS dialogs; saves
    fired from a page were never in it, and nothing in a correct, well-written
    row said so. A boundary nobody states is a boundary nobody can challenge."""
    row = judged(repo, undecided=None)
    assert any("no `undecided:`" in p and "cannot accidentally reproduce" in p for p in row["problems"])


def test_what_is_not_judged_travels_with_the_verdict(repo):
    row = judged(repo, undecided="page-level saves are not judged")
    assert row["undecided"] == "page-level saves are not judged" and row["problems"] == []


def test_a_corpus_found_by_the_claims_own_faculty_is_refused(repo):
    """ACC-04 tabs to find controls and compares each focused element's style.
    Its population is the controls already in the tab order, so a div with
    cursor:pointer and no tabindex cannot appear in it — the check cannot fail
    for the reason it exists. Widening does not help: any enumeration performed
    by the mechanism under test inherits its blind spot."""
    row = judged(repo, claims_faculty="tab order", population={"faculty": "tab order"})
    assert any("CANNOT CONTAIN A FAILING MEMBER" in p and "decorative" in p for p in row["problems"])
    assert any("Derive the population through a DIFFERENT faculty" in p for p in row["problems"])


def test_two_different_faculties_are_fine(repo):
    row = judged(repo, claims_faculty="tab order", population={"faculty": "responds to a click"})
    assert row["problems"] == []


def test_both_faculties_must_be_named(repo):
    assert any("the circular case is undetectable" in p
               for p in judged(repo, claims_faculty=None)["problems"])
    assert any("the circular case is undetectable" in p
               for p in judged(repo, population={"faculty": None})["problems"])


def test_a_detector_sharing_the_claims_faculty_is_refused(repo):
    """A complete union is necessary and not sufficient: two detectors from one
    faculty can cover each other perfectly and both be blind."""
    row = judged(repo, claims_faculty="tab order", population={"faculty": "responds to a click"},
                 subject={"cmd": None, "detectors": [{"name": "tabbing", "faculty": "tab order",
                                                      "cmd": emit("a", "b", "c")}]})
    assert any("found by the claim's own faculty" in p and "necessary and not sufficient" in p
               for p in row["problems"])


def test_a_verification_reading_only_what_the_row_cites_is_refused(repo):
    """LST-07 restated honestly, then verified against the row's own five paging
    tables. It read as passing; a browser found 15 unpaged per-client sub-lists.
    The vocabulary changed and the denominator did not."""
    row = judged(repo, cites=["qa/lists.yml", "docs/ledger.md"], subject={"reads": ["qa/lists.yml"]})
    assert any("paraphrase checked against its own source always agrees" in p for p in row["problems"])
    assert any("SURFACE a person touches" in p for p in row["problems"])


def test_a_verification_reading_a_new_source_is_fine(repo):
    row = judged(repo, cites=["qa/lists.yml"], subject={"reads": ["qa/lists.yml", "the rendered page"]})
    assert row["problems"] == []


def test_declaring_one_of_the_pair_requires_the_other(repo):
    assert any("declares both" in p for p in judged(repo, cites=["qa/lists.yml"])["problems"])
    assert any("declares both" in p for p in judged(repo, subject={"reads": ["x"]})["problems"])


def test_a_marker_population_with_a_declared_superset_reports_the_difference(repo):
    """LST-08: 146 tables exist, 130 carry class="data-table", and ten of the
    sixteen outside build their rows from a collection and so can grow and
    scroll. The marker is applied by the fix, so a denominator made of it can
    only ever measure the fix."""
    row = judged(repo, population={"derived_from": "class_attribute",
                                   "faculty": "static parse",
                                   "cmd": emit("a", "b", "c"), "count": 3,
                                   "superset": {"cmd": emit("a", "b", "c", "unmarked-table"),
                                                "describes": "<table> elements whose rows come from a collection"}})
    assert row["outside"] == ["unmarked-table"]
    assert any("OUTSIDE the declared population entirely" in p and "unmarked-table" in p
               for p in row["problems"])
    assert any("never entered the conversion" in p for p in row["problems"])
    assert not any("refused" in p for p in row["problems"])


def test_a_marker_population_without_a_superset_is_still_refused(repo):
    row = judged(repo, population={"derived_from": "class_attribute"})
    assert any("refused" in p for p in row["problems"])


def test_a_superset_that_adds_nothing_is_clean(repo):
    row = judged(repo, population={"derived_from": "marker", "faculty": "static parse",
                                   "cmd": emit("a", "b", "c"), "count": 3,
                                   "superset": {"cmd": emit("a", "b", "c"), "describes": "every table"}})
    assert row["outside"] == [] and row["problems"] == []


def test_a_superset_that_cannot_run_is_did_not_run(repo):
    row = judged(repo, population={"derived_from": "marker", "faculty": "static parse",
                                   "cmd": emit("a", "b", "c"), "count": 3,
                                   "superset": {"cmd": "/bin/sh -c exit2", "describes": "every table"}})
    assert row["unrunnable"]


def test_a_superset_must_say_what_it_describes(repo):
    """Without the sentence, the difference is a number nobody can act on: "ten
    outside" means nothing until somebody says ten of WHAT."""
    row = judged(repo, population={"derived_from": "marker", "faculty": "static parse",
                                   "cmd": emit("a"), "count": 1,
                                   "superset": {"cmd": emit("a", "b")}})
    assert any("refused" in p for p in row["problems"])


def test_an_observed_population_may_not_gate_on_a_count_it_did_not_create(repo):
    """A floor of three refusals, honestly derived and reviewed, was true of a
    laptop loaded from a customer extract and false of the seeded CI database
    whose ids start elsewhere. It went red having said nothing about the code."""
    row = judged(repo, population={"observed_from": "the live database"})
    assert any("environment-coupled" in p and "must be one the guard BUILDS" in p for p in row["problems"])


def test_an_observed_population_with_a_capability_reports_its_size_instead_of_gating(repo):
    """The discrimination comes from the constructed case; the found-count is
    information printed beside it."""
    row = judged(repo, capability=cap(), subject={"cmd": emit("a", "b")},
                 population={"observed_from": "the live database", "cmd": emit("a", "b"), "count": 99})
    assert row["problems"] == []          # the pin is NOT enforced
    assert "is INFORMATION, not a gate" in row["note"] and "the live database" in row["note"]


def test_a_constructed_population_still_pins_exactly(repo):
    row = judged(repo, subject={"cmd": emit("a", "b")}, population={"cmd": emit("a", "b"), "count": 99})
    assert any("FELL 99 → 2" in p for p in row["problems"])


SURFACES = ("admin shell", "contractor portal", "public token pages")


def surfaced(repo, guard_surfaces, **over):
    root = repo([guard(**over) | ({"surfaces": guard_surfaces} if guard_surfaces is not None else {})])
    return population.run_population(root, {"register": "qa/guards.yml", "surfaces": list(SURFACES)},
                                     today=TODAY)["rows"][0]


def test_a_guard_must_account_for_every_surface_the_project_has(repo):
    """FRM-01's sweep credited a style.css rule to every template alike; the six
    customer-facing token pages never load the sheet, so the required signature
    field on the proposal approval page had no mark at all."""
    row = surfaced(repo, {"admin shell": {"covered_by": "a"}})
    assert any("'contractor portal' is neither covered nor excluded" in p for p in row["problems"])
    assert any("'public token pages' is neither covered nor excluded" in p for p in row["problems"])
    assert any("where CUSTOMERS meet the product" in p for p in row["problems"])


def test_a_guard_with_no_surfaces_block_is_told_the_class(repo):
    row = surfaced(repo, None)
    assert any("THE DEFAULT POPULATION IS THE SURFACE THE AUTHOR WORKS IN" in p for p in row["problems"])
    assert any("admin shell, contractor portal, public token pages" in p for p in row["problems"])


def test_an_excluded_surface_needs_a_reason(repo):
    row = surfaced(repo, {"admin shell": {"covered_by": "a"}, "contractor portal": {"covered_by": "b"},
                          "public token pages": ""})
    assert any("must be {covered_by: <path prefix>} or {excluded: <reason>}" in p for p in row["problems"])
    assert any("A sentence is not evidence" in p for p in row["problems"])


def test_an_excluded_surface_with_a_reason_is_accepted(repo):
    row = surfaced(repo, {"admin shell": {"covered_by": "a"}, "contractor portal": {"covered_by": "b"},
                          "public token pages": {"excluded": "read-only receipts, checked under PRT-02"}})
    assert row["problems"] == []


def test_a_surface_the_project_does_not_declare_is_named(repo):
    row = surfaced(repo, {"admin shell": {"covered_by": "a"}, "contractor portal": {"covered_by": "b"},
                          "public token pages": {"covered_by": "c"}, "marketing site": {"covered_by": "d"}})
    assert any("'marketing site' is not one this project declares" in p for p in row["problems"])


def test_a_project_declaring_no_surfaces_is_unaffected(repo):
    assert judged(repo)["problems"] == []


def test_a_surface_claimed_covered_must_appear_in_the_population(repo):
    """The trial defect: a guard declared all four surfaces covered while its
    population command read templates/admin only, omitting nine required
    controls on the public and portal pages, and it PASSED. The declaration is
    a sentence; the command is the evidence."""
    row = surfaced(repo, {"admin shell": {"covered_by": "a"},
                          "contractor portal": {"covered_by": "templates/portal/"},
                          "public token pages": {"excluded": "read-only"}})
    assert any("'contractor portal' is declared covered by 'templates/portal/'" in p
               and "NO member under it" in p for p in row["problems"])
    assert any("they disagree" in p for p in row["problems"])


def test_an_exemption_for_a_member_outside_the_population_enforces_nothing(repo):
    """Two entries added in one edit, reading identically. One is real: delete
    it and the test goes red. The other's file never enters the candidate set,
    so deleting it leaves every test green — the shape of a considered decision
    and the force of a blank line."""
    row = judged(repo, subject={"cmd": emit("a")}, exemptions=[
        {"member": "b", "reason": "view state only", "evidence": "docs/ledger.md", "review_by": "2026-10-15"},
        {"member": "pages/WarehouseBoard.tsx", "reason": "view state only",
         "evidence": "docs/ledger.md", "review_by": "2026-10-15"}])
    assert row["missing"] == ["c"]        # b is genuinely excused
    assert any("'pages/WarehouseBoard.tsx' enforces NOTHING" in p and "force of a blank line" in p
               for p in row["problems"])
    assert not any("WarehouseBoard" in p and "now examines it" in p for p in row["problems"])


def test_the_two_dead_exemptions_are_different_findings(repo):
    """One means the honest record belongs upstream; the other means the case is
    fixed. Same symptom, different repair."""
    row = judged(repo, exemptions=[
        {"member": "b", "reason": "x", "evidence": "docs/ledger.md", "review_by": "2026-10-15"},
        {"member": "not-in-the-world", "reason": "x", "evidence": "docs/ledger.md", "review_by": "2026-10-15"}])
    assert any("'b' is stale: the guard now examines it" in p for p in row["problems"])
    assert any("'not-in-the-world' enforces NOTHING" in p for p in row["problems"])


def test_a_guard_must_say_what_one_member_is(repo):
    """A census asking whether each FILE containing a refusal also contained a
    focus call stayed green after two of three focus calls were deleted: the
    third still matched somewhere in the same file. One call vouched for three
    refusals, and the guard's unit was coarser than the requirement's."""
    row = judged(repo, unit=None)
    assert any("no `unit:`" in p and "invisible by construction" in p for p in row["problems"])
    assert any("still matched somewhere in the same file" in p for p in row["problems"])


def test_a_metric_must_be_shown_able_to_produce_a_failing_value(repo):
    """A thumb-reach guard scored a button at 199% — a third of a page below the
    fold — as comfortably in reach. Corpus complete, floors on both sides,
    ratchet at zero. The metric knew "too high" and could not express "not on
    the screen at all"."""
    row = judged(repo, metric="the primary action's centre as a % of viewport height",
                 measured_in="staging, 1440x900, seeded tenant", capability=cap())
    assert any("must be shown able to PRODUCE A FAILING VALUE" in p and "proves the arithmetic" in p
               for p in row["problems"])


def test_a_metric_with_a_product_mutation_and_a_movement_is_accepted(repo):
    row = judged(repo, metric="the primary action's centre as a % of viewport height",
                 measured_in="staging, 1440x900, seeded tenant",
                 capability=cap(fires=[{"cmd": emit("caught it"), "from": "docs/ledger.md",
                                        "was": "the settings save at 131%",
                                        "by_mutating": "the save bar from position:sticky to position:static",
                                        "moved": "0 -> 10 of 24 screens, between 142% and 199%"}]))
    assert row["problems"] == []


def test_a_guard_with_no_metric_is_unaffected(repo):
    assert judged(repo, capability=cap())["problems"] == []


def test_naming_the_mutation_without_the_number_it_moved_is_not_enough(repo):
    """`by_mutating:` says what was broken; `moved:` says what the number did.
    A mutation nobody watched the number under is a claim, not a measurement —
    the count staying at 0 IS the finding, and only the figure records it."""
    row = judged(repo, metric="the primary action's centre as a % of viewport height",
                 measured_in="staging, 1440x900, seeded tenant",
                 capability=cap(fires=[{"cmd": emit("caught it"), "from": "docs/ledger.md",
                                        "was": "the settings save at 131%",
                                        "by_mutating": "the save bar from sticky to static"}]))
    assert any("must be shown able to PRODUCE A FAILING VALUE" in p for p in row["problems"])


def test_a_complement_layer_must_prove_it_covers(repo):
    """538 call sites were filed as handling failure because they check res.ok.
    res.ok only exists if the promise RESOLVED; a network rejection throws
    before it, and the screen keeps the old rows and says nothing. The
    population was right and the bucket boundary was wrong."""
    row = judged(repo, **reachy(complement=[{"name": "checks res.ok", "cmd": emit("b")}]))
    assert any("has no `proven_by:`" in p and "BUCKET BOUNDARY was wrong" in p for p in row["problems"])


def test_a_proven_layer_is_accepted(repo):
    row = reach_judged(repo, complement=[
        {"name": "global wrappers", "cmd": emit("b", "c", "d"),
         "proven_by": "tests/test_wrappers.py::test_a_rejected_fetch_still_bounces"}])
    assert row["problems"] == [] and row["covered_by"] == {"global wrappers": 3}


def test_a_falling_population_names_the_migration_case(repo):
    """A guard keyed on the form being migrated AWAY from empties as the code
    improves, and the falling count reads as progress."""
    row = judged(repo, population={"cmd": emit("a"), "count": 3}, subject={"cmd": emit("a")})
    assert any("what a MIGRATION looks like" in p and "reads as progress" in p for p in row["problems"])


def test_an_explained_fall_still_asks_the_migration_question(repo):
    row = judged(repo, population={"cmd": emit("a"), "count": 3, "shrunk": {
        "reason": "two routes deleted", "evidence": "docs/ledger.md", "date": "2026-09-18"}},
        subject={"cmd": emit("a")})
    assert any("if the fall is a MIGRATION" in p and "shrinks to nothing" in p for p in row["problems"])


def reach_judged(repo, **over):
    """A reach guard AND the property guard it is paired with, since a coverage
    ratchet is not allowed to stand alone."""
    root = repo([guard(**reachy(**over)), guard(id="uses-the-result-without-testing-it")])
    return population.run_population(root, {"register": "qa/guards.yml"}, today=TODAY)["rows"][0]


def test_a_reach_guard_must_be_paired_with_a_property_guard(repo):
    # built without the pair the fixture supplies
    """A ratchet keyed on the shape of the old code empties as the fix lands,
    and an empty ratchet is green."""
    row = judged(repo, **reachy(paired_with=None, complement=[{"name": "wrappers", "cmd": emit("b", "c", "d"),
                                                               "proven_by": "tests/x.py::t"}]))
    assert any("WHAT DOES THIS COUNT WHEN THE WORK SUCCEEDS?" in p for p in row["problems"])
    assert any("EMPTY RATCHET IS GREEN" in p for p in row["problems"])


def test_a_reach_guard_paired_with_a_property_guard_is_accepted(repo):
    root = repo([guard(**reachy(paired_with="uses-the-result-without-testing-it",
                                complement=[{"name": "wrappers", "cmd": emit("b", "c", "d"),
                                             "proven_by": "tests/x.py::t"}])),
                 guard(id="uses-the-result-without-testing-it")])
    rows = population.run_population(root, {"register": "qa/guards.yml"}, today=TODAY)["rows"]
    assert rows[0]["problems"] == []


def test_two_coverage_ratchets_empty_together(repo):
    root = repo([guard(**reachy(paired_with="another-reach",
                                complement=[{"name": "w", "cmd": emit("b", "c", "d"),
                                             "proven_by": "tests/x.py::t"}])),
                 guard(id="another-reach", kind="reach")])
    rows = population.run_population(root, {"register": "qa/guards.yml"}, today=TODAY)["rows"]
    assert any("two coverage ratchets empty together" in p for p in rows[0]["problems"])


def test_a_helper_contract_guard_must_name_its_reach(repo):
    """A tracker read 66 rows implemented and every one was TRUE OF THE HELPER.
    apiFetch reports every failure by default and 198 of 870 sites call it."""
    row = judged(repo, proves_helper="apiFetch")
    assert any("MOST EXPENSIVE KIND OF GREEN" in p and "TRUE OF THE HELPER" in p for p in row["problems"])


def test_a_helper_contract_guard_paired_with_its_reach_is_accepted(repo):
    root = repo([guard(proves_helper="apiFetch", paired_with="apifetch-reach"),
                 guard(**reachy(id="apifetch-reach",
                                complement=[{"name": "w", "cmd": emit("b", "c", "d"),
                                             "proven_by": "tests/x.py::t"}]))])
    rows = population.run_population(root, {"register": "qa/guards.yml"}, today=TODAY)["rows"]
    assert rows[0]["problems"] == []


def test_a_helper_contract_paired_with_a_property_guard_is_not_enough(repo):
    root = repo([guard(proves_helper="apiFetch", paired_with="another-sweep"),
                 guard(id="another-sweep")])
    rows = population.run_population(root, {"register": "qa/guards.yml"}, today=TODAY)["rows"]
    assert any("names no `paired_with:` REACH guard" in p for p in rows[0]["problems"])


def test_a_stimulus_must_be_shown_able_to_produce_the_effect(repo):
    """Two orderings, no indicator twice, nearly filed — and neither experiment
    could have produced one, because the wrapper captured window.fetch at parse
    time. The null result was a property of the instrument."""
    row = judged(repo, stimulus="a delayed response, to provoke the loading indicator", capability=cap())
    assert any("CANNOT REPORT THAT IT DID NOT FIRE" in p and "property of the instrument" in p
               for p in row["problems"])


def test_a_stimulus_with_a_positive_control_is_accepted(repo):
    row = judged(repo, stimulus="a delayed response, to provoke the loading indicator",
                 capability=cap(fires=[{"cmd": emit("caught it"), "from": "docs/ledger.md",
                                        "was": "the reports list, 2.1s cold",
                                        "produced": "indicator visible 1.4s, via route interception below the "
                                                    "page's own wrapper"}]))
    assert row["problems"] == []


def test_a_reach_guard_declares_what_it_is_for(repo):
    """A property ratchet and a holding ratchet look identical in the file — a
    shrink-only count with a ceiling — and have opposite correct endings."""
    row = judged(repo, **reachy(**{"for": None}))
    assert any("OPPOSITE CORRECT ENDINGS" in p and "end state is DELETION" in p for p in row["problems"])


def test_a_holding_ratchet_needs_no_pair_but_must_say_when_it_ends(repo):
    """A ceiling of 119 unparseable functions exists only to stop that number
    growing while the parser is known wrong. When a real parser lands, delete
    it — do not invent a property bucket beside it."""
    row = judged(repo, **reachy(**{"for": "holding", "paired_with": None}))
    assert any("names `ends_when:`" in p and "deletable" in p.lower() for p in row["problems"])

    ok = judged(repo, **reachy(**{"for": "holding", "paired_with": None,
                                  "ends_when": "the AST parser replaces the brace matcher; delete this file"},
                               complement=[{"name": "w", "cmd": emit("b", "c", "d"),
                                            "proven_by": "tests/x.py::t"}]))
    assert ok["problems"] == []


def test_a_subject_that_cannot_resolve_the_unit_reports_a_floor(repo):
    """A scan crediting a FILE for a property held by an ELEMENT under-reports
    by construction: the one surface actually driven — 37 rows, 20 columns, zero
    sort controls — was not among the 8, because its file contains sort markup
    somewhere outside the main table."""
    row = judged(repo, subject={"cmd": emit("a"), "reports": "floor"})
    assert row["reports"] == "floor" and row["problems"][0].startswith("2 of 3 never examined")


def test_a_bad_reports_value_is_named(repo):
    assert any("it is `count` or `floor`" in p
               for p in judged(repo, subject={"cmd": emit("a"), "reports": "estimate"})["problems"])


def test_a_floor_is_printed_beside_the_numbers(repo, capsys):
    root = repo([guard(subject={"cmd": emit("a"), "reports": "floor"})])
    population.run(["--repo", str(root)], today=TODAY)
    out = capsys.readouterr().out
    assert "FLOOR, NOT A COUNT" in out and "one route handler" in out


def test_an_absence_claim_must_name_where_it_expected_the_thing(repo):
    """8 files flagged for lacking a filtered-empty message; each page has
    several lists, so the receiving session could not tell which list was
    flagged. You cannot point at what is not there."""
    row = judged(repo, claims_shape="absence")
    assert any("AN ABSENCE HAS NO LINE NUMBER" in p and "path::anchor" in p for p in row["problems"])


def test_an_absence_claim_with_anchored_members_is_judged_normally(repo):
    row = judged(repo, claims_shape="absence",
                 population={"cmd": emit("clients.html::#client-table", "leads.html::#lead-table"), "count": 2},
                 subject={"cmd": emit("clients.html::#client-table")})
    assert row["missing"] == ["leads.html::#lead-table"]
    assert not any("ABSENCE HAS NO LINE NUMBER" in p for p in row["problems"])


def test_a_presence_claim_is_unaffected(repo):
    assert judged(repo)["problems"] == []


def test_a_metric_must_name_the_environment_it_was_measured_in(repo):
    """1998ms was staging, one laptop, one network, one client's data volume.
    A row that goes green on that rests on the wrong measurement."""
    row = judged(repo, metric="search latency to last response", capability=cap())
    assert any("NAMES THE ENVIRONMENT IT WAS MEASURED IN" in p for p in row["problems"])


def test_the_seam_between_two_honest_guards_is_named(repo):
    """A unit sweep checks required fields are MARKED and reads dialog markup.
    An e2e sweep checks they are ASSOCIATED and never opens a dialog. Each is
    correct in its own scope, and 78 unnamed controls live in the space both
    exclude — not a dishonest guard anywhere, a seam between two honest ones."""
    root = repo([guard(id="marked-in-markup", subject={"cmd": emit("a")},
                       abuts="associated-in-the-browser",
                       jointly={"cmd": emit("a", "b", "dialog-field"),
                                "describes": "every required control a person can reach"}),
                 guard(id="associated-in-the-browser", subject={"cmd": emit("b")})])
    row = population.run_population(root, {"register": "qa/guards.yml"}, today=TODAY)["rows"][0]
    assert row["seam"] == ["dialog-field"]
    assert any("fall in the SEAM between this guard and associated-in-the-browser" in p
               for p in row["problems"])
    assert any("Each guard is correct in its own scope" in p for p in row["problems"])


def test_two_guards_that_meet_leave_no_seam(repo):
    root = repo([guard(id="one", subject={"cmd": emit("a")}, abuts="two",
                       jointly={"cmd": emit("a", "b"), "describes": "every control"}),
                 guard(id="two", subject={"cmd": emit("b", "c")})])
    row = population.run_population(root, {"register": "qa/guards.yml"}, today=TODAY)["rows"][0]
    assert row["seam"] == [] and not any("SEAM" in p for p in row["problems"])


def test_abuts_without_a_joint_population_is_refused(repo):
    row = judged(repo, abuts="some-other-guard")
    assert any("comes with `jointly:" in p and "SEAM" in p for p in row["problems"])


def test_a_metric_declares_the_range_a_working_system_produces(repo):
    """303 located contrast failures, every one wrong, many at a ratio of
    exactly 1.0 — invisible text on a page somebody was reading. No review,
    mutation or control caught it; the impossibility did."""
    row = judged(repo, metric="contrast ratio of every text element",
                 measured_in="staging, light theme, 1440x900",
                 capability=cap(plausible=None))
    assert any("declares no `plausible:` range" in p and "INSTRUMENT FAULT" in p for p in row["problems"])
