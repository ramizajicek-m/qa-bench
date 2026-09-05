"""Boot the fake app on a free port per flag-set, point the bench at it."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

FIXTURE = Path(__file__).resolve().parent / "fixture_repo"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Server:
    def __init__(self, flags: dict[str, str]):
        self.port = _free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        env = {**os.environ, **flags, "PYTHONPATH": str(FIXTURE)}
        self.log = open(f"/tmp/qabench-fake-{self.port}.log", "w")   # a PIPE deadlocks at 64 KB
        self.proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "fake_app:app", "--port", str(self.port),
                                      "--log-level", "warning"], cwd=FIXTURE, env=env, stdout=self.log, stderr=subprocess.STDOUT)
        for _ in range(100):
            try:
                if httpx.get(self.url + "/health", timeout=1).status_code == 200:
                    return
            except httpx.HTTPError:
                time.sleep(0.1)
        raise RuntimeError("fake app did not boot; see " + self.log.name)

    def stop(self):
        self.proc.terminate()
        self.proc.wait(timeout=10)
        self.log.close()


@pytest.fixture
def bench_env(monkeypatch, tmp_path):
    """Credentials for both roles, a shot dir, cwd at the fixture repo."""
    monkeypatch.setenv("QA_OWNER_PASSWORD", "pw-owner-secret-1")
    monkeypatch.setenv("QA_STAFF_PASSWORD", "pw-staff-secret-1")
    monkeypatch.setenv("QA_SHOT_DIR", str(tmp_path / "shots"))
    monkeypatch.delenv("QA_EXPECT_SHA", raising=False)
    monkeypatch.chdir(FIXTURE)
    return tmp_path / "shots"


@pytest.fixture
def server_factory(monkeypatch):
    started: list[Server] = []

    def _start(**flags: str) -> Server:
        s = Server({k: v for k, v in flags.items()})
        started.append(s)
        monkeypatch.setenv("QA_BASE_URL", s.url)
        return s
    yield _start
    for s in started:
        s.stop()
