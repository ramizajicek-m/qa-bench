"""`qabench ran` — judged on the two runs of 2026-09-20 whose false direction was a PASS.

The verdict function is pure and gets the table; the CLI gets real subprocesses,
because "the exit code survived" and "the whole output was kept" are claims
about a process, and a fake would assert neither.
"""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import pytest
import yaml

from qabench import ran

SPEC = {"completed": r"(\d+) passed", "failed": r"^FAILED |(\d+) failed"}

PYTEST_GREEN = "....\n4 passed in 1.20s\n"
PYTEST_RED = "FAILED tests/test_a.py::test_x - assert 0\n3 passed, 1 failed in 1.20s\n"
#: The conftest login death: exit 2, no FAILED line, no summary — and every
#: caller that greps for FAILED reads this as clean.
DIED_IN_FIXTURES = "ERROR tests/e2e/conftest.py::login failed: status=500\n!!!! Interrupted: 1 error !!!!\n"
EMPTY = "no tests ran in 0.01s\n0 passed in 0.01s\n"


@pytest.mark.parametrize("code, out, want", [
    (0, PYTEST_GREEN, ran.PASS),
    (1, PYTEST_RED, ran.FAIL),
    (0, PYTEST_RED, ran.FAIL),           # a runner that reports failures and exits 0 is still a failure
    (2, DIED_IN_FIXTURES, ran.INVALID),  # the incident
    (0, DIED_IN_FIXTURES, ran.INVALID),  # ...and it is invalid even if something swallowed the code
    (0, EMPTY, ran.INVALID),             # reached the end, executed nothing
])
def test_the_table(code, out, want):
    assert ran.verdict(code, out, SPEC)[0] == want


def test_a_finished_run_whose_exit_code_disagrees_with_its_summary_is_invalid():
    v, why = ran.verdict(2, PYTEST_GREEN, SPEC)
    assert v == ran.INVALID and "disagrees with its own summary" in why and "closes a row on nothing" in why


def test_an_undeclared_command_falls_back_to_the_kits_markers():
    """anat's postflight shapes, so a pytest run needs no declaration — and the
    weaker claim is said out loud in the artefact rather than quietly widened."""
    assert ran.verdict(0, PYTEST_GREEN, {})[0] == ran.PASS
    # The property that matters is that the fixture death is never a PASS. With
    # the kit's defaults it lands on FAIL rather than INVALID, because `^ERROR `
    # is a failure line the default catalogue knows and the declared one in
    # SPEC (which greps only for FAILED) does not — which is the whole reason
    # the run read as clean to its caller.
    assert ran.verdict(2, DIED_IN_FIXTURES, {})[0] != ran.PASS
    assert ran.verdict(2, DIED_IN_FIXTURES, SPEC)[0] == ran.INVALID


def test_the_completion_artefact_decides_before_the_exit_code():
    """`make land | tail -25` yields tail's 0. A rule that reads the exit code
    first is a rule a pipe can launder; nothing can fake a summary line."""
    assert ran.verdict(0, DIED_IN_FIXTURES, SPEC)[0] == ran.INVALID
    assert "DID NOT FINISH" in ran.verdict(0, DIED_IN_FIXTURES, SPEC)[1]


def test_a_run_reaching_a_hundred_percent_has_finished_and_one_that_was_killed_has_not():
    assert ran.verdict(0, "tests/a.py ....   [100%]\n", {})[0] == ran.PASS
    assert ran.verdict(-9, "tests/a.py ....   [ 52%]\n", {})[0] == ran.INVALID


@pytest.fixture
def repo(tmp_path):
    def write(**ran_cfg):
        (tmp_path / "qa").mkdir(exist_ok=True)
        cfg = {"artefacts": "qa/runs", "commands": {"suite": SPEC}, **ran_cfg}
        (tmp_path / "qa" / "manifest.yml").write_text(yaml.safe_dump({"ran": cfg}), encoding="utf-8")
        return tmp_path
    return write


def say(text: str) -> list[str]:
    """argv that prints `text` and exits 0 — and keeps its own exit code."""
    return ["/bin/echo", text]


def test_the_exit_code_is_the_commands_own_not_a_filters(repo, capsys):
    """`make land | tail -25` yielded tail's 0. There is no pipeline here to lose it in."""
    root = repo()
    code = ran.run(["--repo", str(root), "--name", "suite", "--", "/bin/sh", "-c",
                    "echo 'FAILED tests/test_a.py::test_x'; echo '3 passed, 1 failed'; exit 1"], echo=lambda *_: None)
    assert code == 1
    art = json.loads((root / "qa" / "runs" / "suite.json").read_text())
    assert art["exit_code"] == 1 and art["verdict"] == ran.FAIL


def test_a_run_that_died_in_its_fixtures_exits_three(repo):
    root = repo()
    code = ran.run(["--repo", str(root), "--name", "suite", "--", "/bin/sh", "-c",
                    "echo 'ERROR conftest.py::login failed: status=500'; exit 2"], echo=lambda *_: None)
    assert code == 3
    art = json.loads((root / "qa" / "runs" / "suite.json").read_text())
    assert art["verdict"] == ran.INVALID and art["exit_code"] == 2


def test_a_green_run_passes_and_keeps_its_whole_output(repo):
    root = repo()
    assert ran.run(["--repo", str(root), "--name", "suite", "--"] + say("4 passed in 1.2s"),
                   echo=lambda *_: None) == 0
    art = json.loads((root / "qa" / "runs" / "suite.json").read_text())
    assert art["verdict"] == ran.PASS
    assert "4 passed" in (root / art["log"]).read_text()
    assert art["started"] and art["finished"] and art["argv"][0] == "/bin/echo"


def test_the_whole_output_is_kept_past_the_pipe_buffer(repo):
    """A PIPE nobody drains deadlocks at 64 KB; the tee loop owns both ends."""
    root = repo()
    assert ran.run(["--repo", str(root), "--name", "suite", "--", "/bin/sh", "-c",
                    "i=0; while [ $i -lt 2000 ]; do echo 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'; "
                    "i=$((i+1)); done; echo '4 passed'"], echo=lambda *_: None) == 0
    assert len((root / "qa" / "runs" / "suite.log").read_text()) > 64 * 1024


def test_a_busy_host_is_recorded_and_the_run_still_happens(repo):
    """Reported, never judged. There is no measured instance of contention
    producing a false pass — the one reported as such was a wrong entry point —
    so this records what was up and lets the run decide."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
        root = repo(record={"ports": [port]})
        code = ran.run(["--repo", str(root), "--name", "suite", "--"] + say("4 passed"), echo=lambda *_: None)
    art = json.loads((root / "qa" / "runs" / "suite.json").read_text())
    assert code == 0 and art["verdict"] == ran.PASS
    assert art["host_busy"] == [f"port {port} was listening"]


def test_the_host_snapshot_is_recorded_even_when_clean(repo):
    root = repo(record={"ports": [1], "processes": ["a-process-name-nothing-has"]})
    ran.run(["--repo", str(root), "--name", "suite", "--"] + say("4 passed"), echo=lambda *_: None)
    art = json.loads((root / "qa" / "runs" / "suite.json").read_text())
    assert art["host"]["ports"] == {"1": False}
    assert art["host"]["processes"] == {"a-process-name-nothing-has": 0}
    assert art["host_busy"] == []


def test_no_ran_block_is_three(tmp_path):
    (tmp_path / "qa").mkdir()
    (tmp_path / "qa" / "manifest.yml").write_text("checks: {}\n", encoding="utf-8")
    assert ran.run(["--repo", str(tmp_path), "--name", "suite", "--"] + say("4 passed"), echo=lambda *_: None) == 3


def test_an_undeclared_command_says_so_in_its_artefact(repo):
    root = repo()
    assert ran.run(["--repo", str(root), "--name", "unknown-suite", "--"] + say("4 passed"),
                   echo=lambda *_: None) == 0
    art = json.loads((root / "qa" / "runs" / "unknown-suite.json").read_text())
    assert art["declared"] is False and "the weaker claim" in art["why"]


def test_no_double_dash_is_three(repo):
    assert ran.run(["--repo", str(repo()), "--name", "suite"], echo=lambda *_: None) == 3


def test_our_own_ancestors_are_not_the_host(monkeypatch):
    """A shell whose command line is the compound command that launched this run
    contains every pattern the caller typed — including the one being looked
    for. Measured the first time this ran: a pattern no process was named after
    matched once, in the zsh that had just been handed it. The ps table is faked
    here because the claim under test is the ancestor arithmetic, not the
    reading of ps."""
    import os
    import subprocess as sp
    me = os.getpid()
    table = (f"  PID  PPID COMMAND\n"
             f"{me:>5} {me+1:>5} python -m pytest -k test_stack.sh\n"     # us
             f"{me+1:>5}     1 /bin/zsh -c 'pytest ... test_stack.sh'\n"  # our parent
             f"{me+2:>5}     1 /bin/sh scripts/test_stack.sh up\n")       # somebody else
    monkeypatch.setattr(ran.subprocess, "run",
                        lambda *a, **k: sp.CompletedProcess(a[0] if a else [], 0, table, ""))
    assert ran.snapshot({"processes": ["test_stack.sh"]}).processes == {"test_stack.sh": 1}


#: The live instance, 2026-09-20: `make land` refused, make exited 1, and the
#: wrapper that invoked it through a pipeline reported 0. Nothing landed.
LAND_REFUSED = ("REFUSING TO LAND: tier1 is red on the merged tree\n"
                "make: *** [land] Error 1\n")
LAND_PUSHED = "tier1 green on the merged tree\npushed 6939c4f\n"
LAND = {"completed": r"make: \*\*\* |pushed |REFUSING",
        "refused": r"^REFUSING TO LAND",
        "decided": r"^pushed [0-9a-f]{7,40}"}


def test_a_refusal_is_never_a_pass_whatever_the_exit_code():
    """The exit code was laundered by a pipeline; the refusal was still printed.
    The next session in a serialised lane reads this and advances the queue."""
    for code in (0, 1, 2):
        v, why = ran.verdict(code, LAND_REFUSED, LAND)
        assert v == ran.REFUSED and "never be the same observation" in why
    assert ran.EXIT[ran.REFUSED] != 0


def test_a_pass_asserts_the_artefact_not_the_absence_of_a_complaint():
    assert ran.verdict(0, LAND_PUSHED, LAND)[0] == ran.PASS
    quiet = "tier1 green on the merged tree\nmake: *** [land] Error 1\n"
    v, why = ran.verdict(0, quiet, LAND)
    assert v == ran.INVALID and "never said it DID the thing" in why and "Assert the artefact" in why


def test_a_refusal_and_a_success_are_different_observations():
    """The whole rule, in the form the reporting session put it."""
    assert ran.verdict(0, LAND_REFUSED, LAND)[0] != ran.verdict(0, LAND_PUSHED, LAND)[0]


def test_the_refusal_is_read_before_the_failure_lines():
    """`make: *** [land] Error 1` is a failure line. The accurate word for what
    happened is REFUSED — the command decided, it did not break."""
    assert ran.verdict(1, LAND_REFUSED, LAND)[0] == ran.REFUSED


def test_a_command_declaring_no_refusal_is_unaffected(repo):
    assert ran.verdict(0, PYTEST_GREEN, SPEC)[0] == ran.PASS
    root = repo()
    assert ran.run(["--repo", str(root), "--name", "suite", "--"] + say("4 passed"), echo=lambda *_: None) == 0


GATE = {"completed": r"(\d+) passed",
        "gates": [{"name": "semgrep", "evidence": r"^semgrep: \d+ findings",
                   "elsewhere": "the `lint` job in qa-nightly.yml", "locally": "make venv-semgrep"}]}


def test_a_gate_that_did_not_run_here_is_named_in_the_verdict():
    """A green local run must mention that a gating check was never attempted.
    The floor asked for by the reporting session: not that every gate be
    runnable locally — a minute of semgrep per change is how people stop
    running the tier — but that a skipped gate and a passed gate never read
    the same."""
    v, why = ran.verdict(0, PYTEST_GREEN, GATE)
    assert v == ran.PASS
    assert "NOT ATTEMPTED HERE" in why and "semgrep" in why
    assert "the `lint` job" in why and "make venv-semgrep" in why


def test_a_gate_that_did_run_is_not_mentioned():
    v, why = ran.verdict(0, "semgrep: 0 findings\n" + PYTEST_GREEN, GATE)
    assert v == ran.PASS and "NOT ATTEMPTED" not in why


def test_a_gate_that_cannot_say_where_it_runs_is_invalid():
    """The silent case, and the only one refused outright."""
    spec = {"completed": GATE["completed"], "gates": [{"name": "semgrep", "evidence": r"^semgrep:"}]}
    v, why = ran.verdict(0, PYTEST_GREEN, spec)
    assert v == ran.INVALID and "silently and invisibly" in why


def test_the_artefact_names_the_gates_nobody_attempted(repo):
    root = repo(commands={"suite": GATE})
    assert ran.run(["--repo", str(root), "--name", "suite", "--"] + say("4 passed"), echo=lambda *_: None) == 0
    art = json.loads((root / "qa" / "runs" / "suite.json").read_text())
    assert art["not_attempted"] == ["semgrep"] and art["verdict"] == ran.PASS
