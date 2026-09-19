"""`qabench escapes` — the escape rate and the ODC histogram, and no row hides.

Three claims, lifted from anat's test_defect_escape_rate_is_measured.py and
generalised: (1) arithmetic on a fixture — 2 customer + 8 internal = 20 %;
(2) a finder matching neither vocabulary is RED and named, never silently
internal; (3) the seeded-fault benchmark loads, every id is unique, every shape
and trigger is in the vocabulary, and every reporter classifies as customer —
so a benchmark row can never read as an internal find.

Mutation (watched 2026-09-19): "israel" removed from ESTATE_PEOPLE → claim 3
names AL-001; the `return None` at the end of classify_finder changed to
`return "internal"` → claim 2 goes green-for-the-wrong-reason and the fixture
in claim 1 reads 18 % — both red.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from qabench import escapes

TODAY = dt.date(2026, 9, 19)
KIT = Path(__file__).resolve().parents[1]

_FIXTURE = """## 2026-09-08 — a section

| Defect | Found by | Had looked and said sound | Calibration fix |
|---|---|---|---|
| an old-format row | the robustness reviewer | panel | guard |
| another | Independent refuter, round 3 | — | guard |

## 2026-09-15 — filed under the twelve checks

| date | what reached whom | found by | check that owned it | why it did not fire | trigger |
|---|---|---|---|---|---|
| 2026-09-15 | a label the wrong way round | Israel, from the printer | C5 | half a question | Hardware Configuration |
| 2026-09-15 | a stale mirror | יענקי, by WhatsApp | C7 | lag does not vote | Software Configuration |
| 2026-09-15 | a stale ref | the smoke triage | C8 | — | Coverage |
| 2026-09-15 | a floor recorded | the night | — | not a defect | |
| 2026-09-16 | a vacuous guard | `tools/mutate.py` | C10 | — | |
| 2026-09-16 | a wrong count | the parity run | C2 | — | |
| 2026-09-16 | a skipped tier | a session, reading the summary | C8 | — | |
| 2026-09-16 | a dead link | the link walk | C10 | — | |
| 2026-09-17 | a process question | Rami, asking how do we know it ran | C8 | — | |
"""


def test_the_rate_is_customer_over_all_defects():
    rows = escapes.ledger_rows(_FIXTURE)
    d = escapes.defect_escape_rate(rows, today=TODAY, days=30)
    assert d["unclassified"] == [], d
    assert (d["customer"], d["internal"], d["total"]) == (2, 8, 10)     # the "—" row is not a defect
    assert d["rate"] == 0.2


def test_an_unclassified_finder_is_red_and_named(tmp_path):
    text = _FIXTURE + "| 2026-09-17 | a mystery | the weather | C1 | — | |\n"
    d = escapes.defect_escape_rate(escapes.ledger_rows(text), today=TODAY, days=30)
    assert d["unclassified"] == ["2026-09-17 'the weather'"]
    (tmp_path / "ledger.md").write_text(text, encoding="utf-8")
    assert escapes.run(["--ledger", str(tmp_path / "ledger.md")], today=TODAY) == 1


def test_a_trigger_column_feeds_the_histogram_and_an_unknown_trigger_is_a_finding():
    rows = escapes.ledger_rows(_FIXTURE)
    h = escapes.trigger_histogram(rows)
    assert h["triggers"] == {"Hardware Configuration": 1, "Software Configuration": 1, "Coverage": 1}
    assert h["untagged"] == 8 and h["unknown"] == []
    rows.append({"trigger": "Bad Luck"})
    assert escapes.trigger_histogram(rows)["unknown"] == ["Bad Luck"]


@pytest.mark.parametrize("phrase", [
    "Chilik controls the warehouse floor and found it",
    "Israel building a pallet in the morning",
    "Mimi acceptance of the month-end run",
    "Ran trace of the booking page",
    "a customer, reading the inventory",
])
def test_a_person_in_the_head_wins_over_an_internal_word_in_the_same_head(phrase):
    """The order of the two vocabularies is the honesty property: a customer's
    finding must never read as ours because the sentence also used one of our
    words. Mutation (watched 2026-09-19): the INTERNAL check moved above the
    customer check -> every case here reads 'internal'."""
    assert escapes.classify_finder(phrase) == "customer"


def test_the_benchmark_classifies_every_row_however_old(tmp_path):
    old = tmp_path / "b.yml"
    old.write_text("rows:\n- {id: X-1, date: 2020-01-01, by: 'the weather', shape: a, trigger: Sequencing, what: w, why: y}\n",
                   encoding="utf-8")
    assert escapes.run(["--benchmark", str(old)], today=TODAY) == 1


def test_a_project_can_add_its_own_people():
    assert escapes.classify_finder("Dvora, on the phone") is None
    assert escapes.classify_finder("Dvora, on the phone", people=["dvora"]) == "customer"


def test_no_ledger_is_did_not_run_not_a_pass(tmp_path):
    assert escapes.run(["--repo", str(tmp_path)], today=TODAY) == 3


def test_a_ledger_that_parses_to_nothing_is_did_not_run_not_a_failure(tmp_path):
    (tmp_path / "ledger.md").write_text("# a ledger with prose and no table\n", encoding="utf-8")
    assert escapes.run(["--ledger", str(tmp_path / "ledger.md")], today=TODAY) == 3


@pytest.fixture(scope="module")
def benchmark():
    return escapes.benchmark_rows(KIT / "benchmarks" / "escaped.yml")


def test_the_benchmark_is_well_formed(benchmark):
    ids = [r["id"] for r in benchmark]
    assert len(ids) == len(set(ids)) and len(ids) >= 120
    bad = [(r["id"], r.get("shape"), r.get("trigger")) for r in benchmark
           if r.get("shape") not in escapes.SHAPES or r.get("trigger") not in escapes.TRIGGERS]
    assert bad == []
    assert all(r.get("what") and r.get("why") and r.get("date") for r in benchmark)


def test_every_benchmark_reporter_reads_as_a_customer(benchmark):
    wrong = [(r["id"], r["by"]) for r in benchmark if escapes.classify_finder(r["by"]) != "customer"]
    assert wrong == [], wrong


def test_the_benchmark_run_prints_the_shape_and_trigger_totals(capsys):
    assert escapes.run(["--benchmark", str(KIT / "benchmarks" / "escaped.yml")], today=TODAY) == 0
    out = capsys.readouterr().out
    assert "Lateral Compatibility" in out and "two correct halves" in out and "customer 1" in out
