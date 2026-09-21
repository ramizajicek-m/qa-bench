"""nightly names what is NEW since the last night: a constant red is not a signal."""
from types import SimpleNamespace

from qabench import nightly


def res(name, failed, completed=True):
    return {"name": name, "completed": completed, "failed": [(f, "detail") for f in failed]}


CFG = SimpleNamespace(origin="https://staging.example")


def test_first_night_has_no_baseline():
    d = nightly._delta(CFG, [res("pages", ["a"])])
    assert "no baseline" in d["line"] and d["new"] == []


def test_new_failures_on_an_already_red_stage_are_named():
    """ana-log: 33 new failures arrived on a tier already red and nobody saw them."""
    nightly._delta(CFG, [res("pages", ["a"])])
    d = nightly._delta(CFG, [res("pages", ["a", "b"])])
    assert d["new"] == ["pages::b"] and "1 NEW" in d["line"]


def test_the_same_red_is_not_news():
    nightly._delta(CFG, [res("pages", ["a"])])
    assert nightly._delta(CFG, [res("pages", ["a"])])["new"] == []


def test_a_stage_that_did_not_run_does_not_read_as_fixed():
    nightly._delta(CFG, [res("pages", ["a"])])
    d = nightly._delta(CFG, [res("pages", [], completed=False)])
    assert d["vanished"] == [] and d["new"] == []


def test_a_fixed_failure_is_reported_gone():
    nightly._delta(CFG, [res("pages", ["a"])])
    assert nightly._delta(CFG, [res("pages", [])])["vanished"] == ["pages::a"]


def test_the_identity_is_the_label_not_the_volatile_detail():
    nightly._delta(CFG, [{"name": "p", "completed": True, "failed": [("x", "run 1 at 03:10")]}])
    assert nightly._delta(CFG, [{"name": "p", "completed": True, "failed": [("x", "run 2 at 03:12")]}])["new"] == []
