"""Inactive cooperative host lease for expensive work (C8/C12).

Importing this module observes or changes nothing. Callers must share one
host-local state directory and hold the lease until all their workers finish.
This is not an OS sandbox, a container-wide lock or a deployment lock.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import socket
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


class Refused(RuntimeError):
    """Work must not start; the reason is safe to show without command args."""


def memory_observation() -> dict:
    """Read macOS pressure, never allocate memory or start a workload.

    Other hosts need their own collector. A Docker guest must not present its
    memory figures as the laptop's; unknown is a refusal, not a quiet pass.
    """
    if sys.platform != "darwin":
        raise Refused("host memory collector is unavailable on this platform")
    try:
        pressure = subprocess.run(
            ["/usr/sbin/sysctl", "-n", "kern.memorystatus_vm_pressure_level"],
            check=True, capture_output=True, text=True, timeout=5,
        )
        available = subprocess.run(
            ["/usr/bin/memory_pressure"], check=True, capture_output=True,
            text=True, timeout=15,
        )
        match = re.search(r"free percentage:\s*(\d+)%", available.stdout)
        if not match:
            raise Refused("host free-memory observation is unreadable")
        return {"pressure": int(pressure.stdout.strip()), "free_pct": int(match.group(1))}
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise Refused("host memory observation is unavailable") from exc


def check_memory(observation: dict, *, min_free_pct: int) -> None:
    # Threshold is a declared host policy, not a claim calibrated on this Mac.
    if type(min_free_pct) is not int or not 1 <= min_free_pct <= 100:
        raise Refused("declare a free-memory threshold between 1 and 100")
    pressure, available = observation.get("pressure"), observation.get("free_pct")
    if type(pressure) is not int or pressure not in (1, 2, 4):
        raise Refused("host memory pressure is unknown")
    if type(available) is not int or not 0 <= available <= 100:
        raise Refused("host free-memory observation is unknown")
    if pressure != 1 or available < min_free_pct:
        raise Refused("host has insufficient headroom for another expensive workload")


def _label(value: str, field: str) -> str:
    if (not isinstance(value, str) or not value.strip() or len(value) > 200
            or any(ord(c) < 32 for c in value)):
        raise Refused(f"invalid {field}")
    return value


class HostLease:
    """One participating expensive workload at a time, across project worktrees.

    Acquisition never waits or starts work. The owning process holds a kernel
    flock. A crash releases the kernel lock but leaves an active receipt: the
    next caller refuses until orphan workers are reconciled. Time alone never
    clears that receipt. Do not unlink/replace the lock file while in use.
    """

    def __init__(self, state_dir: Path, *, task: str, project: str,
                 worktree: Path, kind: str, min_free_pct: int):
        self.state_dir = Path(state_dir)
        if not self.state_dir.is_absolute() or not Path(worktree).is_absolute():
            raise Refused("state directory and worktree must be absolute")
        if kind not in ("tests", "build", "mutation", "browser", "promotion-validation"):
            raise Refused("unknown workload kind")
        self.identity = {"task": _label(task, "task"), "project": _label(project, "project"),
                         "worktree": str(Path(worktree)), "kind": kind,
                         "pid": os.getpid(), "host": socket.gethostname()}
        self.min_free_pct = min_free_pct
        self._fd = None
        self._started = {}

    def _read(self) -> dict | None:
        os.lseek(self._fd, 0, os.SEEK_SET)
        raw = os.read(self._fd, 16385)
        if not raw:
            return None
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise Refused("lease receipt is unreadable; reconciliation required") from exc
        if len(raw) > 16384 or not isinstance(value, dict):
            raise Refused("lease receipt is invalid; reconciliation required")
        return value

    def _write(self, status: str, **extra) -> None:
        value = {"version": 1, **self.identity, **self._started, "status": status, **extra}
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
        os.lseek(self._fd, 0, os.SEEK_SET)
        os.ftruncate(self._fd, 0)
        while raw:
            written = os.write(self._fd, raw)
            if written == 0:
                raise OSError("lease receipt write did not advance")
            raw = raw[written:]
        os.fsync(self._fd)

    def acquire(self) -> "HostLease":
        if self._fd is not None:
            raise Refused("lease already acquired by this object")
        if os.getpid() != self.identity["pid"]:
            raise Refused("create a new lease object in the process that will own it")
        self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        # A private, stable directory avoids two names/owners for one lease.
        directory = self.state_dir.lstat()
        if (not stat.S_ISDIR(directory.st_mode) or directory.st_uid != os.getuid()
                or directory.st_mode & 0o022):
            raise Refused("lease state directory must be owned and not writable by others")
        fd = os.open(self.state_dir / "heavy-work.lock",
                     os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        self._fd = fd
        locked = False
        admission_started = False
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                raise Refused("lease file has unsafe ownership or type")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except BlockingIOError as exc:
                holder = self._read()
                # Do not dump command/environment strings or unvalidated data.
                task = (_label(holder.get("task"), "holder task")
                        if holder and holder.get("status") in ("active", "admitting") else "receipt pending")
                raise Refused(f"another workload holds the machine lease: {task}") from exc
            prior = self._read()
            if prior is not None and (prior.get("version") != 1 or prior.get("status") != "released"):
                raise Refused("previous workload did not release cleanly; reconcile its workers first")
            self._started = {"started_at": datetime.now(timezone.utc).isoformat(),
                             "min_free_pct": self.min_free_pct}
            admission_started = True
            self._write("admitting")
            observation = memory_observation()
            check_memory(observation, min_free_pct=self.min_free_pct)
            self._started["memory_at_start"] = observation
            self._write("active")
            return self
        except BaseException:
            try:
                if admission_started:
                    # Caller code has not started; refusing admission creates
                    # no orphan workers and must not permanently block retry.
                    self._write("released", outcome="admission_refused",
                                released_at=datetime.now(timezone.utc).isoformat())
            finally:
                if locked:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                self._fd = None
            raise

    def close(self) -> None:
        if self._fd is None:
            return
        if os.getpid() != self.identity["pid"]:
            raise Refused("only the owning process may release the lease")
        try:
            self._write("released", released_at=datetime.now(timezone.utc).isoformat())
        finally:
            os.close(self._fd)
            self._fd = None

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
