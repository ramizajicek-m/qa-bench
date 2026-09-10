"""Local draft: not executed. Each future case uses its own temporary lease.

Protocol/locking qualification, not product coverage. Never uses the actual
host lease directory or starts a project suite, browser, database or build.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from qabench import resource_gate as gate


@pytest.fixture(autouse=True)
def quiet_host(monkeypatch):
    monkeypatch.setattr(gate, "memory_observation", lambda: {"pressure": 1, "free_pct": 60})


def lease(tmp_path, project="anat"):
    return gate.HostLease(tmp_path / "host-state", task=f"task-{project}", project=project,
                          worktree=tmp_path / project, kind="tests", min_free_pct=25)


def test_two_projects_compete_for_one_host_lease_then_next_can_proceed(tmp_path):
    first, second = lease(tmp_path), lease(tmp_path, "ana-log")
    with first:
        with pytest.raises(gate.Refused, match="task-anat"):
            second.acquire()
    with second:
        saved = json.loads((tmp_path / "host-state/heavy-work.lock").read_text())
        assert saved["project"] == "ana-log" and saved["pid"] == os.getpid()
        assert saved["status"] == "active" and saved["memory_at_start"]["free_pct"] == 60
    assert json.loads((tmp_path / "host-state/heavy-work.lock").read_text())["status"] == "released"


@pytest.mark.parametrize("observation", [
    {"pressure": 4, "free_pct": 60}, {"pressure": 2, "free_pct": 60},
    {"pressure": 1, "free_pct": 24}, {"pressure": None, "free_pct": 60},
    {"pressure": 1, "free_pct": None}, {"pressure": True, "free_pct": 60},
])
def test_unhealthy_or_unknown_host_refuses_before_work(tmp_path, monkeypatch, observation):
    monkeypatch.setattr(gate, "memory_observation", lambda: observation)
    with pytest.raises(gate.Refused):
        lease(tmp_path).acquire()
    monkeypatch.setattr(gate, "memory_observation", lambda: {"pressure": 1, "free_pct": 60})
    with lease(tmp_path):
        pass


def test_host_is_sampled_only_after_owning_the_lock(tmp_path, monkeypatch):
    observations = []
    monkeypatch.setattr(gate, "memory_observation", lambda: observations.append("sampled") or {"pressure": 1, "free_pct": 60})
    with lease(tmp_path):
        with pytest.raises(gate.Refused):
            lease(tmp_path, "another").acquire()
        assert observations == ["sampled"]


def test_admission_receipt_identifies_new_owner_before_memory_probe(tmp_path, monkeypatch):
    with lease(tmp_path, "old"):
        pass

    def observe():
        saved = json.loads((tmp_path / "host-state/heavy-work.lock").read_text())
        assert saved["task"] == "task-new" and saved["status"] == "admitting"
        with pytest.raises(gate.Refused, match="task-new"):
            lease(tmp_path, "third").acquire()
        return {"pressure": 1, "free_pct": 60}

    monkeypatch.setattr(gate, "memory_observation", observe)
    with lease(tmp_path, "new"):
        pass


def test_unavailable_memory_probe_releases_admission_without_orphan_claim(tmp_path, monkeypatch):
    def unavailable():
        raise gate.Refused("probe unavailable")

    monkeypatch.setattr(gate, "memory_observation", unavailable)
    with pytest.raises(gate.Refused, match="probe unavailable"):
        lease(tmp_path).acquire()
    saved = json.loads((tmp_path / "host-state/heavy-work.lock").read_text())
    assert saved["status"] == "released" and saved["outcome"] == "admission_refused"
    monkeypatch.setattr(gate, "memory_observation", lambda: {"pressure": 1, "free_pct": 60})
    with lease(tmp_path, "another"):
        pass


@pytest.mark.parametrize("crash_at", ["probe", "active"])
def test_parent_crash_does_not_silently_release_orphan_work(tmp_path, crash_at):
    # A distinct interpreter owns the lock and exits without cleanup. Kernel
    # release alone is insufficient: worker lifetime is not known after a crash.
    script = """
import os, sys
from pathlib import Path
from qabench import resource_gate as gate
def observe():
    if sys.argv[2] == 'probe':
        os._exit(0)
    return {'pressure': 1, 'free_pct': 60}
gate.memory_observation = observe
root = Path(sys.argv[1])
held = gate.HostLease(root / 'host-state', task='crashed-task', project='anat',
                     worktree=root / 'anat', kind='tests', min_free_pct=25).acquire()
os._exit(0)
"""
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path), crash_at],
                            cwd=Path(gate.__file__).resolve().parents[1], timeout=10)
    assert result.returncode == 0
    with pytest.raises(gate.Refused, match="reconcile"):
        lease(tmp_path, "ana-log").acquire()


@pytest.mark.parametrize("receipt", ['{"version":1,"status":"active"}', 'partial{', '{"version":99,"status":"released"}'])
def test_unknown_receipt_is_never_expired_by_age(tmp_path, receipt):
    state = tmp_path / "host-state"
    state.mkdir(mode=0o700)
    (state / "heavy-work.lock").write_text(receipt)
    with pytest.raises(gate.Refused):
        lease(tmp_path).acquire()


def test_ordinary_exception_releases_after_context_cleanup(tmp_path):
    with pytest.raises(ValueError):
        with lease(tmp_path):
            raise ValueError("workload failed")
    with lease(tmp_path, "another"):
        pass


def test_receipt_does_not_store_environment_or_command_arguments(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_RESOURCE_TEST_SECRET", "do-not-record-this-value")
    with lease(tmp_path):
        raw = (tmp_path / "host-state/heavy-work.lock").read_text()
        assert "do-not-record-this-value" not in raw
        assert set(json.loads(raw)) == {"version", "task", "project", "worktree", "kind", "pid", "host",
                                         "started_at", "memory_at_start", "min_free_pct", "status"}
