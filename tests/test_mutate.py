"""The mutation harness, which exists because the obvious way to undo a
mutation destroys uncommitted work.

`git checkout -- <file>` restores HEAD. When the thing under test is itself
uncommitted — which is the normal case while writing a guard — that is a REVERT.
anat met it three times on 2026-08-23 and built scripts/mutate.sh; eliad copied
it; the other five repos and this kit had nothing, so it happened five more times
on 2026-09-13 in one session, to someone who had written the rule and used the
tool correctly four times first.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

from qabench.mutate import main


def _repo(tmp_path: pathlib.Path) -> pathlib.Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    f = tmp_path / "m.py"
    f.write_text("value = 2\n")
    subprocess.run(["git", "add", "m.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "-m", "base"], cwd=tmp_path, check=True)
    return f


def test_the_restore_brings_back_the_WORKING_COPY_not_HEAD(tmp_path):
    """THE WHOLE POINT, and the bug that produced it five times in one day."""
    f = _repo(tmp_path)
    f.write_text("value = 3  # an uncommitted fix\n")

    rc = main([str(f), 's.replace("3", "99")', "--", sys.executable, "-c",
               f"assert '99' in open({str(f)!r}).read()"])
    assert rc == 0, "the command should have seen the mutation"
    assert f.read_text() == "value = 3  # an uncommitted fix\n", (
        "the restore read HEAD instead of the working copy — which is the defect "
        "this tool exists to make impossible")


def test_a_no_op_expression_is_refused(tmp_path):
    """A mutation that changes nothing reads exactly like a guard that did not fire.

    eliad's battery reported TEN dead guards that way; the truth was that ten
    anchors had drifted and nothing had been mutated at all.
    """
    f = _repo(tmp_path)
    rc = main([str(f), 's.replace("not-present", "x")', "--", sys.executable, "-c", "pass"])
    assert rc == 2
    assert f.read_text() == "value = 2\n"


def test_the_exit_code_is_the_commands_so_a_survivor_reads_as_zero(tmp_path):
    """0 means the mutation SURVIVED — the guard cannot see it.

    Stated in the docstring because it is the one thing people read backwards.
    """
    f = _repo(tmp_path)
    survived = main([str(f), 's.replace("2", "7")', "--", sys.executable, "-c", "pass"])
    assert survived == 0
    caught = main([str(f), 's.replace("2", "7")', "--", sys.executable, "-c",
                   "raise SystemExit(1)"])
    assert caught == 1


def test_the_file_is_restored_even_when_the_command_crashes(tmp_path):
    f = _repo(tmp_path)
    f.write_text("value = 5\n")
    main([str(f), 's.replace("5", "6")', "--", "definitely-not-a-real-command-xyz"])
    assert f.read_text() == "value = 5\n"


def test_a_missing_file_and_a_bad_expression_touch_nothing(tmp_path):
    f = _repo(tmp_path)
    assert main([str(tmp_path / "nope.py"), 's', "--", "true"]) == 2
    assert main([str(f), 's.this_is_not_valid(', "--", "true"]) == 2
    assert f.read_text() == "value = 2\n"


def test_a_dirty_target_is_warned_about_not_refused(tmp_path, capsys):
    """Mid-edit is the case this tool exists for, so it runs. The warning is
    aimed at the `git checkout --` that comes afterwards out of habit — two
    people lost work to exactly that on 2026-09-20, hours apart."""
    f = _repo(tmp_path)
    f.write_text("value = 3  # an uncommitted fix\n")

    rc = main([str(f), 's.replace("3", "99")', "--", sys.executable, "-c", "raise SystemExit(1)"])
    err = capsys.readouterr().err
    assert rc == 1                                        # the command's own code: the guard caught it
    assert "UNCOMMITTED" in err and "git checkout --" in err
    assert f.read_text() == "value = 3  # an uncommitted fix\n"


def test_a_clean_target_is_not_warned_about(tmp_path, capsys):
    f = _repo(tmp_path)
    main([str(f), 's.replace("2", "4")', "--", sys.executable, "-c", "pass"])
    assert "UNCOMMITTED" not in capsys.readouterr().err
