"""tools/install_lockd.sh restarts lockd only when no run holds or waits through it.

2026-11-02: a reinstall restarted lockd under a project's CI unit run, which stopped as "lock lost while it ran".
The guard (from "# Who holds" to the wait loop's `done`) is cut out of the script and run as it is, against a
lock directory this test fills: live entries through the service hold it back, dead or host-only ones do not.
"""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "install_lockd.sh"


def _guard() -> str:
    lines = SCRIPT.read_text().splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("# Who holds"))
    end = next(i for i in range(start, len(lines)) if lines[i] == "done")
    return "\n".join(["set -eu", "idle_wait=$1", *lines[start:end + 1], "echo RESTARTING"])


def _run(lock: Path, idle_wait: int):
    return subprocess.run(["sh", "-c", _guard(), "guard", str(idle_wait)], capture_output=True, text=True,
                          timeout=60, env={**os.environ, "QABENCH_HEAVY_LOCK": str(lock)})


def _lock(tmp_path: Path) -> Path:
    lock = tmp_path / "heavy.lock"
    (tmp_path / "heavy.lock.holders").mkdir()
    (tmp_path / "heavy.lock.queue").mkdir()
    return lock


def test_a_live_run_through_the_service_holds_the_restart_back_and_is_named(tmp_path):
    lock = _lock(tmp_path)
    live = subprocess.Popen(["sleep", "60"])
    try:
        (tmp_path / "heavy.lock.holders" / "1-x").write_text(
            f"ci-unit for ci, in a container via the host lock service, pid {live.pid} in /w since 18:40 (6 cores)")
        r = _run(lock, 0)
        assert r.returncode == 4, r.stdout + r.stderr
        assert "NOT RESTARTED" in r.stdout and "ci-unit for ci" in r.stdout and "RESTARTING" not in r.stdout
    finally:
        live.kill()


def test_a_queued_run_through_the_service_counts_too(tmp_path):
    lock = _lock(tmp_path)
    live = subprocess.Popen(["sleep", "60"])
    try:
        (tmp_path / "heavy.lock.queue" / f"{time.time_ns()}-{live.pid}").write_text(
            "ci-e2e for ci, in a container via the host lock service (4 cores)")
        r = _run(lock, 0)
        assert r.returncode == 4 and "ci-e2e" in r.stdout
    finally:
        live.kill()


def test_dead_entries_and_host_runs_do_not(tmp_path):
    lock = _lock(tmp_path)
    dead = subprocess.Popen(["true"]); dead.wait()
    (tmp_path / "heavy.lock.holders" / "1-x").write_text(
        f"gone for ci, in a container via the host lock service, pid {dead.pid} in /w since 18:40 (6 cores)")
    (tmp_path / "heavy.lock.queue" / f"{time.time_ns()}-{dead.pid}").write_text(
        "gone for ci, in a container via the host lock service (4 cores)")
    (tmp_path / "heavy.lock.holders" / "2-y").write_text(
        f"land for a session, pid {os.getpid()} in /w since 18:40 (6 cores)")       # a host run survives a restart
    r = _run(lock, 0)
    assert r.returncode == 0 and "RESTARTING" in r.stdout, r.stdout + r.stderr


def test_it_restarts_once_the_run_finishes(tmp_path):
    lock = _lock(tmp_path)
    # Orphaned so the system reaps it: a child of this test would linger as a zombie and still answer kill -0.
    pid = subprocess.run(["sh", "-c", "sleep 3 >/dev/null 2>&1 & echo $!"], capture_output=True, text=True).stdout.strip()
    (tmp_path / "heavy.lock.holders" / "1-x").write_text(
        f"ci-unit for ci, in a container via the host lock service, pid {pid} in /w since 18:40 (6 cores)")
    r = _run(lock, 60)
    assert r.returncode == 0 and "waiting for the runs" in r.stdout and "RESTARTING" in r.stdout
