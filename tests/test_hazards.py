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


def test_a_self_hosted_docker_job_running_tests_must_trust_its_workspace(tmp_path):
    """tharros and iga, 2026-09-21: git exited 128 after checkout and git-backed tests read an empty corpus."""
    bare = ("on: [push]\njobs:\n  unit:\n    runs-on: [self-hosted, linux, iga]\n"
            "    steps:\n      - run: python -m qabench heavy --name ci-unit -- python -m pytest tests -q\n")
    assert scan(tmp_path, bare, name=".github/workflows/ci.yml")[0] == 1
    fixed = ("on: [push]\nenv:\n  GIT_CONFIG_COUNT: '1'\n  GIT_CONFIG_KEY_0: safe.directory\n"
             "  GIT_CONFIG_VALUE_0: ${{ github.workspace }}\n" + bare.split("\n", 1)[1])
    _lockd_hosts(tmp_path / "b", "iga")
    _lockd_hosts(tmp_path / "c", "macOS")
    assert scan(tmp_path / "b", fixed, name=".github/workflows/ci.yml")[0] == 0
    macos = bare.replace("[self-hosted, linux, iga]", "[self-hosted, macOS]")
    assert scan(tmp_path / "c", macos, name=".github/workflows/ci.yml")[0] == 0


def test_a_character_tail_of_command_output_is_refused_and_a_line_tail_is_not(tmp_path):
    """anat land.py: `r.stdout[-800:]` printed `irect-use-of-jinja2...: 0 -> 2` — the path cut from the head."""
    assert scan(tmp_path, "say(r.stdout[-800:])\n", name="scripts/land.py")[0] == 1
    assert scan(tmp_path / "e", "print(p.stderr[-1500:])\n", name="scripts/ratchet.py")[0] == 1
    assert scan(tmp_path / "b", "say('\\n'.join(r.stdout.splitlines()[-15:]))\n", name="scripts/land.py")[0] == 0


WF = ("on: [push]\nenv:\n  GIT_CONFIG_COUNT: '1'\n  GIT_CONFIG_KEY_0: safe.directory\n"
      "  GIT_CONFIG_VALUE_0: ${{ github.workspace }}\njobs:\n  e2e:\n    runs-on: %s\n    steps:\n%s")


def test_a_suite_on_a_self_hosted_runner_outside_the_heavy_lock_is_red(tmp_path):
    """2026-11-02: anat's host runners at load 176 beside a landing that held the lock; my8200's container runner
    timed a walk out at load ~58. One heavy run per machine holds only if every heavy leg takes the lock."""
    steps = {
        "pytest": "      - name: e2e\n        run: python -m pytest tests/e2e -q\n",
        "make": "      - name: tier\n        run: |\n          pip install -e .\n          make test-e2e\n",
        "nightly": "      - name: bench\n        run: python -m qabench nightly\n",
    }
    for i, (what, step) in enumerate(steps.items()):
        rc, out = scan(tmp_path / str(i), WF % ("[self-hosted, linux, my8200]", step), name=".github/workflows/ci.yml")
        assert rc == 1 and any("outside the machine's heavy lock" in o for o in out), (what, out)


def test_a_wrapped_suite_a_hosted_runner_and_an_excused_step_are_clean(tmp_path):
    wrapped = "      - name: e2e\n        run: python -m qabench heavy --name ci-e2e -- python -m pytest tests/e2e -q\n"
    _lockd_hosts(tmp_path / "a", "my8200")
    assert scan(tmp_path / "a", WF % ("[self-hosted, linux, my8200]", wrapped), name=".github/workflows/ci.yml")[0] == 0
    hosted = "      - name: e2e\n        run: python -m pytest tests/e2e -q\n"
    assert scan(tmp_path / "b", WF % ("ubuntu-latest", hosted), name=".github/workflows/ci.yml")[0] == 0
    excused = ("      - name: smoke\n        run: |\n          # hazard-ok: read-only checks on staging, minutes long\n"
               "          python -m pytest tests/smoke -q\n")
    rc, out = scan(tmp_path / "c", WF % ("[self-hosted, linux, my8200]", excused), name=".github/workflows/ci.yml")
    assert rc == 0 and any("EXCUSED: read-only checks on staging" in o for o in out), out
    mention = ("      - name: note\n        run: |\n          pip install -r requirements.txt pytest\n"
               "          echo done  # after pytest\n          python - <<'PY'\n          # pytest's junit counts\n          PY\n")
    assert scan(tmp_path / "d", WF % ("[self-hosted, linux, my8200]", mention), name=".github/workflows/ci.yml")[0] == 0


def test_a_project_gate_can_ask_for_the_unlocked_suites_alone(tmp_path):
    step = "      - name: e2e\n        run: python -m pytest tests/e2e -q\n"
    f = tmp_path / ".github/workflows/ci.yml"
    f.parent.mkdir(parents=True)
    f.write_text(WF % ("[self-hosted, linux, my8200]", step))
    n, red = hazards.unlocked_suites(tmp_path)
    assert n == 1 and len(red) == 1 and red[0].startswith(".github/workflows/ci.yml: job e2e, step e2e")
    f.write_text(WF % ("[self-hosted, linux, my8200]", step.replace("run: ", "run: python -m qabench heavy --name ci-e2e -- ")))
    _lockd_hosts(tmp_path, "my8200")
    assert hazards.unlocked_suites(tmp_path) == (1, [])


def _lockd_hosts(root, *labels):
    (root / "qa").mkdir(parents=True, exist_ok=True)
    (root / "qa/manifest.yml").write_text("lockd_hosts: [" + ", ".join(labels) + "]\n" if labels else "bench: {}\n")


def test_a_wrapped_suite_on_a_runner_without_the_lock_service_is_red(tmp_path):
    """2026-11-02: a project's wrapped steps ran on a Docker runner on another Mac, where no lockd runs, and every one
    came back DID NOT RUN. A wrapped job must be pinned to a runner label that only a lockd host carries."""
    wrapped = "      - name: unit\n        run: python -m qabench heavy --name ci-unit -- python -m pytest -q\n"
    f = tmp_path / ".github/workflows/ci.yml"
    f.parent.mkdir(parents=True)
    f.write_text(WF % ("[self-hosted, mac-docker-other]", wrapped))
    _lockd_hosts(tmp_path, "gate-host")
    n, red = hazards.unlocked_suites(tmp_path)
    assert len(red) == 1 and "names no lockd host label (gate-host)" in red[0], red
    _lockd_hosts(tmp_path)                                  # nothing declared: red, never a guess
    n, red = hazards.unlocked_suites(tmp_path)
    assert len(red) == 1 and "declares no `lockd_hosts:`" in red[0], red
    _lockd_hosts(tmp_path, "gate-host")
    f.write_text(WF % ("[self-hosted, gate-host]", wrapped))
    assert hazards.unlocked_suites(tmp_path) == (1, [])
    f.write_text(WF % ("{group: runners, labels: [self-hosted, gate-host]}", wrapped))
    assert hazards.unlocked_suites(tmp_path) == (1, [])
    f.write_text(WF % ("[self-hosted, mac-docker-other]",
                       wrapped.replace("run: ", "run: |\n          # hazard-ok: a host runner, its own flock\n          ")))
    assert hazards.unlocked_suites(tmp_path) == (1, [])
    rc, out = scan(tmp_path, f.read_text(), name=".github/workflows/ci.yml")
    assert rc == 0 and any("EXCUSED: a host runner, its own flock" in o for o in out), out
