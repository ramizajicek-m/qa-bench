"""`press()` — attribute requests to the control that caused them.

The measurement that made this necessary: anat has 973 controls and 125 are
judgeable, because `judgeable` means the lifter resolved what URL a control calls
and 804 buttons have no resolvable action. Adding a passive browser recorder
moved that number by ZERO — recording more traffic tells you `POST /api/x`
happened, not which of 804 buttons sent it.

A press names the control directly, so the click is the identity.
"""

from __future__ import annotations

import json

import pytest

from qabench import gestures as G
from qabench.press import NestedPress, press, read_presses


class FakePage:
    """The three Playwright methods `press` touches, and nothing else."""

    def __init__(self, responses=()):
        self._handlers = []
        self._queued = list(responses)
        self.waited = 0

    def on(self, event, fn):
        assert event == "response"
        self._handlers.append(fn)

    def remove_listener(self, event, fn):
        self._handlers.remove(fn)

    def wait_for_timeout(self, ms):
        self.waited += ms
        for r in self._queued:          # they land inside the window
            for h in list(self._handlers):
                h(r)
        self._queued = []

    def emit(self, response):
        for h in list(self._handlers):
            h(response)


class FakeResponse:
    def __init__(self, method, url, status):
        self.request = type("R", (), {"method": method})()
        self.url = url
        self.status = status


def test_a_press_attributes_the_window_to_the_control(tmp_path, monkeypatch):
    """The point of the whole module: no URL is known in advance.

    Mutation: make `press.__exit__` write `control: None` and this goes red.
    """
    monkeypatch.setenv("QABENCH_RECORD_PRESSES", str(tmp_path / "p.jsonl"))
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    page = FakePage([FakeResponse("POST", "http://app/api/whatever/7", 200)])

    cid = "admin/clients/detail.html::button[id=fs-bf-save]"
    with press(page, cid, settle_ms=1):
        pass

    rows = [json.loads(l) for l in (tmp_path / "p.jsonl").read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["control"] == cid
    assert rows[0]["accepted"] is True
    assert rows[0]["requests"] == ["POST http://app/api/whatever/7 200"]


def test_a_refused_press_is_recorded_as_not_accepted(tmp_path, monkeypatch):
    """A 403 in the window is a press that did not act."""
    monkeypatch.setenv("QABENCH_RECORD_PRESSES", str(tmp_path / "p.jsonl"))
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    page = FakePage([FakeResponse("POST", "http://app/api/x", 403)])
    with press(page, "t.html::button[id=b]", settle_ms=1):
        pass
    row = json.loads((tmp_path / "p.jsonl").read_text().splitlines()[0])
    assert row["accepted"] is False


def test_presses_REFUSE_to_nest(tmp_path, monkeypatch):
    """Two clicks in one window cannot be told apart.

    A wrong attribution is worse than none — that cost six false "accepted"
    verdicts on 2026-09-13, and this is the guard against repeating it one layer
    out.

    Mutation: drop the `_OUTSTANDING` check and this goes red.
    """
    monkeypatch.setenv("QABENCH_RECORD_PRESSES", str(tmp_path / "p.jsonl"))
    page = FakePage()
    with press(page, "a", settle_ms=1):
        with pytest.raises(NestedPress) as e:
            with press(page, "b", settle_ms=1):
                pass
        assert "serialise" in str(e.value)


def test_the_outstanding_flag_is_released_even_when_the_body_raises(monkeypatch):
    """Or one failing test poisons every press after it."""
    monkeypatch.delenv("QABENCH_RECORD_PRESSES", raising=False)
    page = FakePage()
    with pytest.raises(ZeroDivisionError):
        with press(page, "a", settle_ms=1):
            1 / 0
    with press(page, "b", settle_ms=1):     # must not raise NestedPress
        pass


def test_a_failing_press_records_NOTHING(tmp_path, monkeypatch):
    """A click that raised is not evidence about the control.

    The test failed; whether the control works is unknown, and writing
    `accepted: false` would report a broken control instead of a broken test.
    """
    monkeypatch.setenv("QABENCH_RECORD_PRESSES", str(tmp_path / "p.jsonl"))
    page = FakePage()
    with pytest.raises(RuntimeError):
        with press(page, "a", settle_ms=1):
            raise RuntimeError("the locator was not visible")
    assert not (tmp_path / "p.jsonl").exists() or not (tmp_path / "p.jsonl").read_text().strip()


def test_recording_is_off_unless_asked_for(tmp_path, monkeypatch):
    """An ordinary suite run must be unchanged."""
    monkeypatch.delenv("QABENCH_RECORD_PRESSES", raising=False)
    page = FakePage([FakeResponse("POST", "http://app/x", 200)])
    with press(page, "a", settle_ms=1):
        pass
    assert not list(tmp_path.iterdir())


def test_a_control_pressed_twice_is_accepted_if_it_EVER_was(tmp_path):
    """One refusal among several presses is a test driving the refusal."""
    f = tmp_path / "p.jsonl"
    f.write_text("\n".join([
        json.dumps({"control": "a", "requests": [], "accepted": False}),
        json.dumps({"control": "a", "requests": [], "accepted": True}),
        json.dumps({"control": "b", "requests": [], "accepted": False}),
    ]))
    assert read_presses(f) == {"a": True, "b": False}


def test_each_xdist_worker_writes_its_own_press_file(tmp_path, monkeypatch):
    """The same lesson as the request recorder: one path, eight workers, one survivor."""
    from qabench.press import target_path

    monkeypatch.setenv("QABENCH_RECORD_PRESSES", str(tmp_path / "p.jsonl"))
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    assert target_path().name == "p.jsonl"
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw5")
    assert target_path().name == "p.gw5.jsonl"


def _repo(tmp_path, tmpl, corpus):
    (tmp_path / "templates").mkdir()
    for name, body in tmpl.items():
        (tmp_path / "templates" / name).write_text(body)
    (tmp_path / "tests").mkdir()
    for name, body in corpus.items():
        (tmp_path / "tests" / name).write_text(body)


def test_a_PRESSED_control_becomes_judgeable_without_a_resolvable_action(tmp_path):
    """THE POINT. This is the line that moves 125 of 973.

    A button whose handler no static reader can follow is `mutates: unknown` with
    no action, so no recording can ever decide it. A press decides it.

    Mutation: drop the `presses` union from `judgeable_with_presses` and this goes
    red with the control still unjudgeable.
    """
    _repo(tmp_path,
          {"a.html": '<button id="mystery" onclick="doSomethingClever()">go</button>'},
          {"t.py": "# names #mystery"})

    plain = G.measure(tmp_path, min_controls=1, min_corpus=1, recording={"POST /x"})
    mystery = [g for g in plain.population if "mystery" in g.id]
    assert mystery, "the fixture did not lift the button"
    cid = mystery[0].id
    assert not mystery[0].action, "the fixture's button must have no resolvable action"
    assert cid not in plain.judgeable, "unjudgeable without a press — the premise"

    pressed = G.measure(tmp_path, min_controls=1, min_corpus=1,
                        recording={"POST /x"}, presses={cid: True})
    assert cid in pressed.judgeable, "a pressed control must be judgeable"
    assert cid in pressed.hit, "and an accepted press must count as hit"

    refused = G.measure(tmp_path, min_controls=1, min_corpus=1,
                        recording={"POST /x"}, presses={cid: False})
    assert cid in refused.judgeable, "a refused press is still JUDGED"
    assert cid not in refused.hit, "but not accepted — that is the distinction"
