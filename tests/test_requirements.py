"""`qabench questions` / `qabench asked` — the requester was asked, and said what.

Claims: (1) the pack loads, every question id is unique within the lists a
surface combines, and `always` is part of every kind; (2) a surface with every
question answered by a named person on a date is green; (3) an unanswered
question is red and quotes the question; (4) an answer that is an assumption is
red — "we assumed 120×100" is how a default nobody confirmed read like a fact
(ana-log AL-069); (5) an open question needs an owner and a date and goes red
past it; (6) answers with nobody named are red; (7) no register is 3, not 0.

Mutation (watched 2026-09-19): `_ASSUMED` emptied → claim 4 reads green;
`o.get("review_by")` dropped from the open check → claim 5's undated case green.
"""
from __future__ import annotations

import datetime as dt

import pytest
import yaml

from qabench import requirements as rq

TODAY = dt.date(2026, 9, 19)


def _surface(kinds, answers=None, open_=None, who=True):
    s = {"kinds": kinds, "answers": answers or {}, "open": open_ or {}}
    if who:
        s.update(asked_of="Israel (warehouse manager)", asked_on="2026-09-16")
    return {"surfaces": {"label": s}}


def _all_answered(kinds):
    return {q["id"]: "a person's real answer" for q in rq.questions_for(kinds)}


def test_the_pack_loads_and_always_is_in_every_kind():
    p = rq.pack()
    always = {q["id"] for q in p["always"]}
    for kind in p["kinds"]:
        ids = [q["id"] for q in rq.questions_for([kind], p)]
        assert len(ids) == len(set(ids)) and always <= set(ids)


def test_every_question_answered_by_a_named_person_is_green():
    assert rq.judge(_surface(["print", "scan"], _all_answered(["print", "scan"])), TODAY) == []


def test_an_unasked_question_is_red_and_quotes_itself():
    answers = _all_answered(["print"])
    del answers["orientation"]
    red = rq.judge(_surface(["print"], answers), TODAY)
    assert len(red) == 1 and "portrait or landscape" in red[0]["problem"]


@pytest.mark.parametrize("assumption", ["we assumed 120×100", "probably portrait", "TBD", "?"])
def test_an_assumption_is_not_an_answer(assumption):
    answers = {**_all_answered(["print"]), "paper-size": assumption}
    red = rq.judge(_surface(["print"], answers), TODAY)
    assert [r for r in red if "assumption" in r["problem"]], red


def test_an_open_question_needs_an_owner_and_a_date_and_expires():
    answers = _all_answered(["print"])
    del answers["per-sheet"]
    owned = rq.judge(_surface(["print"], answers, {"per-sheet": {"owner": "Rami", "review_by": "2026-09-30"}}), TODAY)
    assert owned == []
    undated = rq.judge(_surface(["print"], answers, {"per-sheet": {"owner": "Rami"}}), TODAY)
    assert "no owner and review_by" in undated[0]["problem"]
    expired = rq.judge(_surface(["print"], answers, {"per-sheet": {"owner": "Rami", "review_by": "2026-09-01"}}), TODAY)
    assert "open past" in expired[0]["problem"]


def test_answers_with_nobody_named_are_red():
    red = rq.judge(_surface(["print"], _all_answered(["print"]), who=False), TODAY)
    assert any("whose words" in r["problem"] for r in red)


def test_an_unknown_kind_is_red_not_ignored():
    red = rq.judge(_surface(["hologram"], {}), TODAY)
    assert "unknown surface kind" in red[0]["problem"]


def test_no_register_is_did_not_run(tmp_path):
    assert rq.run_asked(["--repo", str(tmp_path)], today=TODAY) == 3


def test_a_register_run_end_to_end(tmp_path):
    (tmp_path / "qa").mkdir()
    reg = _surface(["print"], _all_answered(["print"]))
    (tmp_path / "qa" / "requirements.yml").write_text(yaml.safe_dump(reg, allow_unicode=True), encoding="utf-8")
    assert rq.run_asked(["--repo", str(tmp_path)], today=TODAY) == 0
