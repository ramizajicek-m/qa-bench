"""The host's heavy lock served to its containers: one lock, one queue, fail closed, released when a container dies.

2026-11-02: six projects' Docker runners on the gate host ran outside the heavy lock (a flock does not cross
Docker-for-Mac's VM), and a night walk timed out on a starved 2-CPU runner while the lock read as fair."""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from qabench import lockd, ran

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def served(tmp_path, monkeypatch):
    """A lock service on an ephemeral port over a lock file of the test's own."""
    lock = tmp_path / "heavy.lock"
    monkeypatch.setenv("QABENCH_HEAVY_LOCK", str(lock))
    monkeypatch.delenv("QABENCH_HEAVY_HELD", raising=False)
    monkeypatch.delenv("QABENCH_HEAVY_LOCKD", raising=False)
    log, port = [], []
    up = threading.Event()
    threading.Thread(target=lockd.serve, kwargs=dict(port=0, log=log.append, ready=lambda p: (port.append(p), up.set())),
                     daemon=True).start()
    assert up.wait(10)
    return {"lock": lock, "addr": f"127.0.0.1:{port[0]}", "log": log}


def _env(**kw):
    env = {k: v for k, v in os.environ.items() if k not in ("QABENCH_HEAVY_HELD",)}
    env["PYTHONPATH"] = str(ROOT)
    env.update(kw)
    return env


def _host_holder(lock, seconds, name="host e2e"):
    """A host run holding the machine's lock, the way a gate stage or `qabench heavy` on the host does."""
    p = subprocess.Popen([sys.executable, "-c",
                          "import sys, time\nfrom qabench import ran\n"
                          f"with ran.HeavyLock({name!r}, path={str(lock)!r}, echo=lambda *_: None):\n"
                          "    print('held', flush=True); time.sleep(float(sys.argv[1]))", str(seconds)],
                         stdout=subprocess.PIPE, text=True, env=_env())
    assert p.stdout.readline().strip() == "held"
    return p


def _wait_for(pred, timeout=20):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.1)
    return False


def test_a_container_waits_behind_a_host_run_in_the_same_queue_and_is_listed_there(served, monkeypatch):
    holder = _host_holder(served["lock"], 3)
    monkeypatch.setenv("QABENCH_HEAVY_LOCKD", served["addr"])
    monkeypatch.setenv("QABENCH_SESSION", "my-ci integration")
    queue = Path(f"{served['lock']}.queue")
    listed = []
    threading.Thread(target=lambda: _wait_for(lambda: listed.extend(
        e.read_text() for e in queue.iterdir()) or listed), daemon=True).start()
    out = []
    t0 = time.monotonic()
    rc = ran.heavy(["--name", "ci-integration", "--", sys.executable, "-c", "pass"], echo=out.append)
    assert rc == 0
    assert time.monotonic() - t0 >= 2, "the container's run went ahead while a host run held the lock"
    assert holder.wait(10) == 0
    said = "\n".join(out)
    assert "held by: host e2e for" in said, said            # the host's own waiting line, carried over the socket
    assert "1st in the queue" in said, said
    assert any("ci-integration" in t and "in a container via the host lock service" in t for t in listed), listed
    assert f"lock: the host's, through {served['addr']}" in said


def test_a_host_run_waits_behind_a_container_and_names_it_as_the_holder(served, monkeypatch):
    client = subprocess.Popen([sys.executable, "-m", "qabench", "heavy", "--name", "ci-e2e", "--",
                               sys.executable, "-c", "import time; time.sleep(3)"],
                              stdout=subprocess.PIPE, text=True,
                              env=_env(QABENCH_HEAVY_LOCKD=served["addr"], QABENCH_SESSION="my-ci e2e",
                                       QABENCH_HEAVY_LOCK="/nonexistent/never-used"))
    assert _wait_for(lambda: any("holds: ci-e2e" in s for s in served["log"]))
    said = []
    t0 = time.monotonic()
    with ran.HeavyLock("host land", path=str(served["lock"]), echo=said.append):
        assert time.monotonic() - t0 >= 1, "the host run took the lock a container held"
    assert client.wait(20) == 0
    assert any("held by: ci-e2e" in s and "my-ci e2e, in a container via the host lock service" in s
               for s in said), said


def test_an_unreachable_service_is_did_not_run_and_the_command_never_starts(tmp_path, monkeypatch):
    monkeypatch.delenv("QABENCH_HEAVY_HELD", raising=False)
    with __import__("socket").socket() as s:                # a port nothing listens on
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    monkeypatch.setenv("QABENCH_HEAVY_LOCKD", f"127.0.0.1:{port}")
    marker = tmp_path / "ran"
    out = []
    rc = ran.heavy(["--name", "ci-unit", "--", sys.executable, "-c", f"open({str(marker)!r}, 'w')"], echo=out.append)
    assert rc == 3
    assert not marker.exists(), "the command ran without the lock"
    assert any("DID NOT RUN" in o and "unreachable" in o for o in out), out


def test_a_container_never_takes_a_lock_of_its_own(monkeypatch):
    monkeypatch.delenv("QABENCH_HEAVY_LOCKD", raising=False)
    monkeypatch.setattr(lockd, "in_container", lambda: True)
    assert lockd.address() == "host.docker.internal:7461"
    monkeypatch.setattr(lockd, "in_container", lambda: False)
    assert lockd.address() == ""
    monkeypatch.setenv("QABENCH_HEAVY_LOCKD", "10.0.0.1:9")
    assert lockd.address() == "10.0.0.1:9"


def test_a_container_killed_while_it_holds_releases_the_hosts_lock(served):
    client = subprocess.Popen([sys.executable, "-m", "qabench", "heavy", "--name", "ci-doomed", "--",
                               sys.executable, "-c", "import time; time.sleep(600)"],
                              stdout=subprocess.DEVNULL, env=_env(QABENCH_HEAVY_LOCKD=served["addr"]))
    assert _wait_for(lambda: any("holds: ci-doomed" in s for s in served["log"]))
    client.kill()
    client.wait()
    t0 = time.monotonic()
    with ran.HeavyLock("next", path=str(served["lock"]), echo=lambda *_: None):
        assert time.monotonic() - t0 < 15


def test_a_container_that_goes_silent_is_released_after_the_silence_limit(served, monkeypatch):
    """A container killed through the VM's proxy may send no FIN: silence, not only a close, ends its hold."""
    import json
    import socket
    monkeypatch.setattr(lockd, "SILENT", 2)
    host, port = served["addr"].split(":")
    s = socket.create_connection((host, int(port)))
    s.sendall((json.dumps({"name": "ci-mute", "who": "x"}) + "\n").encode())
    assert _wait_for(lambda: any("holds: ci-mute" in l for l in served["log"]))
    # no beats, no close: the socket stays open and says nothing
    assert _wait_for(lambda: any("went silent" in l and "ci-mute" in l for l in served["log"]), timeout=15)
    t0 = time.monotonic()
    with ran.HeavyLock("next", path=str(served["lock"]), echo=lambda *_: None):
        assert time.monotonic() - t0 < 5
    s.close()


def test_a_waiter_that_dies_in_the_queue_leaves_it(served, monkeypatch):
    holder = _host_holder(served["lock"], 60)                # still held throughout: the ticket must go while it waits
    client = subprocess.Popen([sys.executable, "-m", "qabench", "heavy", "--name", "ci-gone", "--", "true"],
                              stdout=subprocess.DEVNULL, env=_env(QABENCH_HEAVY_LOCKD=served["addr"]))
    queue = Path(f"{served['lock']}.queue")
    assert _wait_for(lambda: any("ci-gone" in e.read_text() for e in queue.iterdir()))
    client.kill()
    client.wait()
    assert _wait_for(lambda: any("closed the connection" in l and "ci-gone" in l for l in served["log"]), timeout=15)
    assert ran.queue_ahead(queue, None) == []
    assert holder.poll() is None
    holder.kill()


def test_a_lock_lost_mid_run_stops_the_command_and_says_did_not_run(served, monkeypatch, tmp_path):
    monkeypatch.setenv("QABENCH_HEAVY_LOCKD", served["addr"])
    marker = tmp_path / "finished"
    out = []

    def kill_the_hosts_hold():
        assert _wait_for(lambda: any("holds: ci-cut" in s for s in served["log"]))
        pid = int(next(s for s in served["log"] if "waits: ci-cut" in s).rsplit("host pid ", 1)[1].rstrip(")"))
        os.killpg(pid, 9)

    threading.Thread(target=kill_the_hosts_hold, daemon=True).start()
    t0 = time.monotonic()
    rc = ran.heavy(["--name", "ci-cut", "--", sys.executable, "-c",
                    f"import time; time.sleep(30); open({str(marker)!r}, 'w')"], echo=out.append)
    assert rc == 3
    assert time.monotonic() - t0 < 25
    assert not marker.exists()
    assert any("DID NOT RUN to the end" in o for o in out), out
