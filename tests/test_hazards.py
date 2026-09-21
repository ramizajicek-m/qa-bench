"""hazards: shell lines that make an observer report what it did not observe."""
from qabench import hazards


def scan(tmp_path, text, name="scripts/wait.sh"):
    f = tmp_path / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)
    out = []
    return hazards.run(["--repo", str(tmp_path)], echo=out.append), out


def test_a_pgrep_that_matches_its_own_command_line_is_red(tmp_path):
    """anat: the waiter's own command line contained the pattern, so 'alive?' was always yes."""
    code, _ = scan(tmp_path, 'until [ -f d ] || ! pgrep -f "scripts/land.py --batch x"; do sleep 5; done\n')
    assert code == 1


def test_a_self_excluding_pattern_is_clean(tmp_path):
    assert scan(tmp_path, 'pgrep -f "[p]ython.*scripts/land.py"\n')[0] == 0


def test_ps_grep_without_exclusion_is_red_and_with_it_clean(tmp_path):
    assert scan(tmp_path, "ps aux | grep land.py\n")[0] == 1
    assert scan(tmp_path / "b", "ps aux | grep land.py | grep -v grep\n")[0] == 0


def test_a_test_run_piped_into_tail_is_red(tmp_path):
    """`make land | tail -25` reported a failed gate as success."""
    assert scan(tmp_path, "\tmake land | tail -25\n", name="Makefile")[0] == 1
    assert scan(tmp_path / "b", "pytest tests -q | tail -3\n")[0] == 1


def test_tee_or_pipefail_or_a_log_file_is_clean(tmp_path):
    assert scan(tmp_path, "pytest -q | tee run.log | tail -3\n")[0] == 0
    assert scan(tmp_path / "b", "set -o pipefail\npytest -q | tail -3\n")[0] == 0
    assert scan(tmp_path / "c", "pytest -q > run.log 2>&1; tail -3 run.log\n")[0] == 0


def test_a_non_test_pipe_into_tail_is_not_this_hazard(tmp_path):
    assert scan(tmp_path, "git log --oneline | head -5\n")[0] == 0


def test_an_excused_line_is_printed_not_failed(tmp_path):
    code, out = scan(tmp_path, 'pgrep -f "land.py" # hazard-ok: counting any, including this one\n')
    assert code == 0 and any("EXCUSED" in o for o in out)


def test_a_commented_line_is_not_code(tmp_path):
    assert scan(tmp_path, '# pgrep -f "land.py" was the bug\n')[0] == 0


def test_nothing_to_read_is_did_not_run(tmp_path):
    assert hazards.run(["--repo", str(tmp_path)], echo=lambda *_: None) == 3
