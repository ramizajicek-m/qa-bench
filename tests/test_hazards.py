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
    code, _ = scan(tmp_path, 'zsh -c \'until [ -f d ] || ! pgrep -f "scripts/land.py --batch x"; do sleep 5; done\'\n')
    assert code == 1
    assert scan(tmp_path / "mk", '\t@until ! pgrep -f "land.py"; do sleep 5; done\n', name="Makefile")[0] == 1


def test_a_pgrep_in_a_script_file_or_workflow_step_cannot_match_itself(tmp_path):
    """Executed from a file, the pattern is on no command line: anat's five postgrest checks were innocent."""
    assert scan(tmp_path, 'pgrep -f postgrest\n')[0] == 0
    assert scan(tmp_path / "w", '      run: pgrep -f "postgrest"\n', name=".github/workflows/t.yml")[0] == 0


def test_ps_for_one_pid_is_not_a_search(tmp_path):
    assert scan(tmp_path, 'bash -c \'ps -E -p "$pid" | grep -qE postgrest\'\n')[0] == 0


def test_a_self_excluding_pattern_is_clean(tmp_path):
    assert scan(tmp_path, 'bash -c \'pgrep -f "[p]ython.*scripts/land.py"\'\n')[0] == 0


def test_ps_grep_without_exclusion_is_red_and_with_it_clean(tmp_path):
    assert scan(tmp_path, "\tps aux | grep land.py\n", name="Makefile")[0] == 1
    assert scan(tmp_path / "b", "\tps aux | grep land.py | grep -v grep\n", name="Makefile")[0] == 0


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
    code, out = scan(tmp_path, '\tpgrep -f "land.py" # hazard-ok: counting any, including this one\n', name="Makefile")
    assert code == 0 and any("EXCUSED" in o for o in out)


def test_a_commented_line_is_not_code(tmp_path):
    assert scan(tmp_path, '\t# pgrep -f "land.py" was the bug\n', name="Makefile")[0] == 0
    assert scan(tmp_path / "b", '\tpytest -q > run.log # not | tail -3\n', name="Makefile")[0] == 0


def test_nothing_to_read_is_did_not_run(tmp_path):
    assert hazards.run(["--repo", str(tmp_path)], echo=lambda *_: None) == 3


def test_advisory_prints_but_exits_zero(tmp_path):
    f = tmp_path / "Makefile"
    f.write_text("\tmake land | tail -25\n")
    out = []
    assert hazards.run(["--repo", str(tmp_path), "--advisory"], echo=out.append) == 0 and any("RED" in o for o in out)


def test_a_push_workflow_keyed_on_the_ref_cancels_earlier_commits(tmp_path):
    """anat 2026-09-20 and tharros 2026-09-21: a later push cancelled the previous commit's pending gate."""
    wf = "on:\n  push:\n    branches: [main]\nconcurrency:\n  group: ci-${{ github.ref }}\n  cancel-in-progress: true\njobs:\n  t:\n    runs-on: x\n    steps: []\n"
    assert scan(tmp_path, wf, name=".github/workflows/ci.yml")[0] == 1


def test_batching_that_protects_the_running_verdict_is_clean(tmp_path):
    """ana-log's design, Rami's decision 2026-09-17: pending runs batch, a running one is never killed on main."""
    wf = ("on:\n  push: {}\nconcurrency:\n  group: tests-${{ github.ref }}\n"
          "  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}\njobs: {}\n")
    assert scan(tmp_path, wf, name=".github/workflows/tests.yml")[0] == 0
    plain = "on:\n  push: {}\nconcurrency:\n  group: tests-${{ github.ref }}\njobs: {}\n"
    assert scan(tmp_path / "b", plain, name=".github/workflows/tests.yml")[0] == 0


def test_a_sha_keyed_or_scheduled_workflow_is_clean(tmp_path):
    ok = "on:\n  push: {}\nconcurrency:\n  group: ci-${{ github.ref }}-${{ github.sha }}\n  cancel-in-progress: true\njobs: {}\n"
    assert scan(tmp_path, ok, name=".github/workflows/ci.yml")[0] == 0
    nightly = "on:\n  schedule: [{cron: '1 1 * * *'}]\nconcurrency:\n  group: n-${{ github.ref }}\n  cancel-in-progress: true\njobs: {}\n"
    assert scan(tmp_path / "b", nightly, name=".github/workflows/n.yml")[0] == 0


def test_a_job_level_ref_group_is_found_too(tmp_path):
    wf = "on: [push]\njobs:\n  unit:\n    concurrency:\n      group: unit-${{ github.ref }}\n      cancel-in-progress: true\n    runs-on: x\n"
    assert scan(tmp_path, wf, name=".github/workflows/t.yml")[0] == 1
