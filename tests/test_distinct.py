"""`qabench distinct` — judged on the corruption that kept every shape intact.

A `str.replace` keyed on the last sentence of one row's reason hit twenty-one
other rows that ended with the same bookkeeping sentence, and every test over
that tracker stayed green: rows present, requirements verbatim, implemented rows
naming collectable tests. The structure was perfect and the contents were false.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
import yaml

from qabench import distinct

TODAY = dt.date(2026, 9, 20)

BOILERPLATE = ("Swept in the 2026-09-14 gap pass; evidence collected and the row left partial "
               "pending a browser check. ")
NAV08 = ("the sidebar mark moves to the sub-item inside a client, which the five top-level paths "
         "the e2e drives can never show, so the row is demoted until a detail page is driven. ") * 6


def rows(*pairs) -> list[dict]:
    return [{"id": i, "text": t} for i, t in pairs]


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "qa").mkdir()
    (tmp_path / "qa" / "decisions.yml").write_text("decisions: []\n", encoding="utf-8")

    def write(**spec):
        (tmp_path / "qa" / "manifest.yml").write_text(
            yaml.safe_dump({"distinct": {"tables": {"tracker": {"rows": "unused", **spec}}}}), encoding="utf-8")
        return tmp_path
    return write


def judged(repo, table_rows, **spec):
    root = repo(**spec)
    cfg = {"tables": {"tracker": {"rows": "unused", **spec}}}
    return distinct.run_distinct(root, cfg, today=TODAY,
                                 read=lambda *_a, **_k: (table_rows, ""))["tables"][0]


def test_a_reason_pasted_into_twenty_one_rows_is_named(repo):
    """The incident. Every row keeps its shape; NAV-08's reason is in all of them."""
    table = rows(("NAV-08", BOILERPLATE + NAV08),
                 *[(f"SEC-{n:02d}", f"row {n} says its own thing. " + BOILERPLATE + NAV08) for n in range(1, 22)])
    row = judged(repo, table, max_shared=400)
    assert row["offenders"], "a leak of 1012 characters across 22 rows must be named"
    assert any("a LEAK, which the data must lose" in p for p in row["problems"])
    assert "NAV-08" in {o["a"] for o in row["offenders"]} | {o["b"] for o in row["offenders"]}
    assert row["measured"] >= len(NAV08)


def test_innocent_shared_boilerplate_passes(repo):
    """219 characters is the real table's longest innocent overlap; 400 is the
    pin. The check must not fire on the bookkeeping sentence alone."""
    table = rows(*[(f"R-{n:02d}", f"row {n} has its own reason, which is different from every other. "
                                  + BOILERPLATE) for n in range(1, 22)])
    row = judged(repo, table, max_shared=400)
    assert row["problems"] == [] and row["offenders"] == []
    assert row["measured"] < 400


def test_an_unpinned_table_is_told_what_to_pin(repo):
    table = rows(("A", "aaa " + BOILERPLATE), ("B", "bbb " + BOILERPLATE))
    row = judged(repo, table)
    assert row["measured"] >= len(BOILERPLATE)
    assert any("pin a number above it" in p and str(row["measured"]) in p for p in row["problems"])


def test_a_pin_below_the_tables_own_overlap_says_so(repo):
    """A threshold chosen rather than measured fires on the boilerplate itself,
    and a guard that cries wolf is switched off — after which nothing guards the
    real case. The finding says which of the two things each pair is."""
    table = rows(("A", "aaa " + BOILERPLATE), ("B", "bbb " + BOILERPLATE))
    row = judged(repo, table, max_shared=10)
    assert row["offenders"]
    assert any("ABOVE the table's longest" in p and "switched off in a week" in p for p in row["problems"])


def test_the_window_slides_so_a_leak_mid_reason_is_found(repo):
    """A leak lands mid-reason. A check anchored to a line or a prefix would
    step straight over the one that actually happened."""
    leak = "X" * 500
    table = rows(("A", "unique opening for A. " + leak + " unique close for A."),
                 ("B", "an entirely different opening. " + leak + " and a different close."))
    row = judged(repo, table, max_shared=400)
    assert row["offenders"] and row["offenders"][0]["chars"] == 400
    assert row["measured"] >= 500


def test_the_measurement_is_exact(repo):
    table = rows(("A", "p" * 137 + "aaa"), ("B", "p" * 137 + "bbb"))
    assert judged(repo, table, max_shared=400)["measured"] == 137


def test_an_exempted_pair_neither_fires_nor_raises_the_floor(repo):
    """An exempted pair must not become the measurement: if it did, the next
    leak would hide behind the overlap somebody already signed off."""
    shared = "S" * 900
    table = rows(("GEN-01", "one. " + shared), ("GEN-02", "two. " + shared),
                 ("OTHER", "three, wholly its own."))
    row = judged(repo, table, max_shared=400, exemptions=[
        {"pair": ["GEN-01", "GEN-02"], "reason": "both quote the same clause verbatim, by decision",
         "evidence": "qa/decisions.yml", "review_by": "2026-12-01"}])
    assert row["offenders"] == [] and row["problems"] == []
    assert row["measured"] < 400, "the excused pair must not set the floor"


def test_an_expired_exemption_is_red(repo):
    shared = "S" * 900
    table = rows(("GEN-01", "one. " + shared), ("GEN-02", "two. " + shared))
    row = judged(repo, table, max_shared=400, exemptions=[
        {"pair": ["GEN-01", "GEN-02"], "reason": "x", "evidence": "qa/decisions.yml",
         "review_by": "2026-09-01"}])
    assert any("expired 2026-09-01" in p for p in row["problems"])


def test_fewer_than_two_rows_decides_nothing(repo):
    row = judged(repo, rows(("A", "only one")), max_shared=400)
    assert row["unrunnable"] and "decides nothing" in row["problems"][0]


def test_a_row_source_that_cannot_run_is_three(repo):
    root = repo(max_shared=400)
    cfg = {"tables": {"tracker": {"rows": "/bin/sh -c exit2", "max_shared": 400}}}
    out = distinct.run_distinct(root, cfg, today=TODAY)
    assert out["unrunnable"]


def test_the_cli_exits_one_on_a_leak_and_three_with_no_block(tmp_path):
    (tmp_path / "qa").mkdir()
    (tmp_path / "qa" / "manifest.yml").write_text("checks: {}\n", encoding="utf-8")
    assert distinct.run(["--repo", str(tmp_path)], today=TODAY) == 3

    script = tmp_path / "rows.py"
    leak = "X" * 500
    script.write_text("import json;print(json.dumps(["
                      f"{{'id':'A','text':'a. {leak}'}},{{'id':'B','text':'b. {leak}'}}]))", encoding="utf-8")
    (tmp_path / "qa" / "manifest.yml").write_text(yaml.safe_dump({"distinct": {"tables": {"tracker": {
        "rows": f"{__import__('sys').executable} {script}", "max_shared": 400}}}}), encoding="utf-8")
    assert distinct.run(["--repo", str(tmp_path)], today=TODAY) == 1
