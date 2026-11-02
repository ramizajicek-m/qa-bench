"""The machine's heavy-run lock, served over TCP to the containers on it.

WHY. The gate host's Docker runners (six projects, 2026-11-02) ran their suites outside the
heavy lock: a flock does not cross Docker-for-Mac's VM, so a container's `qabench heavy` locked
a file only that container could see. The night of 2026-11-02 a walk timed out on a 2-CPU
runner at host load ~58 while the lock read as fair. So a container does not take a lock of
its own at all: it asks the host.

    python -m qabench lockd [--bind 127.0.0.1] [--port 7461]     # on the host, kept running

ONE LOCK, ONE QUEUE. For each waiter the service starts `python -m qabench heavy` on the host:
the same flock (~/.qabench/heavy.lock, QABENCH_HEAVY_LOCK), the same <lock>.queue/ ticket and the
same holder line as a host run or a gate stage, in the kernel's order. The service adds no lock
and no order of its own; it only carries the waiting lines and the grant back over the socket.

RELEASED WHEN A CONTAINER DIES. The client beats every BEAT seconds while it waits and while it
holds. A connection that closes, or goes silent for SILENT seconds (a container killed outright
sends no FIN through the VM's proxy), ends that waiter's host process, which is what releases
the flock and lets its ticket be swept.

FAIL CLOSED. A client that cannot reach the service, or loses it, does not run its command, or
stops it: DID NOT RUN, exit 3. A command never runs "unlocked" because the lock was unreachable.
"""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

PORT = 7461
BEAT = 10
SILENT = 45
GRANTED = "qabench-lockd: granted"
# Docker Desktop's name for the host, inside any container on it.
CONTAINER_DEFAULT = f"host.docker.internal:{PORT}"


class Unreachable(Exception):
    """The host's lock could not be had: the command must not run."""


def cpu_quota(path: str = "/sys/fs/cgroup/cpu.max") -> float | None:
    """The CPUs a cgroup may use (`quota period`), or None when it is unlimited or there is no cgroup."""
    try:
        quota, period = Path(path).read_text().split()[:2]
        return None if quota == "max" else round(int(quota) / int(period), 2)
    except (OSError, ValueError):
        return None


def in_container() -> bool:
    return Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()


def address() -> str:
    """Where this process's heavy lock lives: "" for this machine's own file, host:port for the host's service.
    A container always asks the host — its own flock would lock a file nothing else can see."""
    return os.environ.get("QABENCH_HEAVY_LOCKD") or (CONTAINER_DEFAULT if in_container() else "")


class RemoteHeavyLock:
    """HeavyLock's shape over the socket: waits, echoes the host's waiting lines, and sets `lost` when the
    host's lock goes away while held."""

    def __init__(self, name: str, addr: str, echo=print, connect_timeout: float = 10, cores: int | None = None):
        self.name, self.addr, self.echo, self.connect_timeout, self.cores = name, addr, echo, connect_timeout, cores
        self.waited, self.lost, self.sock = 0.0, threading.Event(), None

    def __enter__(self):
        held = f"tcp://{self.addr}"
        if os.environ.get("QABENCH_HEAVY_HELD") == held:
            self.echo(f"heavy: the host's lock ({self.addr}) is already held by this run's own ancestor — proceeding inside it")
            self.nested = True
            return self
        self.nested = False
        host, _, port = self.addr.rpartition(":")
        who = next((os.environ[k] for k in ("QABENCH_SESSION", "LAND_SESSION", "ANAT_SESSION") if os.environ.get(k)),
                   os.environ.get("GITHUB_REPOSITORY", "an unnamed session") + (
                       f" {os.environ['GITHUB_JOB']}" if os.environ.get("GITHUB_JOB") else ""))
        t0 = time.monotonic()
        try:
            self.sock = socket.create_connection((host, int(port)), timeout=self.connect_timeout)
        except (OSError, ValueError) as ex:
            # NAME THE RUNNER: 2026-11-02 a project's jobs were DID NOT RUN on a second runner, on another Mac with no
            # lockd, that carried the same labels as the gate host's — and the message read as a network blink.
            on = os.environ.get("RUNNER_NAME")
            raise Unreachable(f"the host's lock service at {self.addr} is unreachable ({ex})"
                              + (f" from runner {on}" if on else "")
                              + " — if that runner's host has no lockd, pin the job to a lockd host's runner label "
                                "(qa/manifest.yml lockd_hosts)") from None
        self.sock.settimeout(None)
        self.sock.sendall((json.dumps({"name": self.name, "who": who, "cores": self.cores}) + "\n").encode())
        self._stop = threading.Event()
        threading.Thread(target=self._beat, daemon=True).start()
        self.rfile = self.sock.makefile("r", encoding="utf-8", errors="replace")
        for line in self.rfile:
            line = line.rstrip("\n")
            if line == GRANTED:
                break
            self.echo(line)
        else:
            self._close()
            raise Unreachable(f"the host's lock service at {self.addr} closed the connection before granting the lock")
        self.waited = round(time.monotonic() - t0, 1)
        self.echo(f"heavy: the host's heavy-run lock granted through {self.addr} after {self.waited}s")
        threading.Thread(target=self._watch, daemon=True).start()
        self._prev = os.environ.get("QABENCH_HEAVY_HELD")
        os.environ["QABENCH_HEAVY_HELD"] = held
        return self

    def _beat(self):
        while not self._stop.wait(BEAT):
            try:
                self.sock.sendall(b"beat\n")
            except OSError:
                self.lost.set()
                return

    def _watch(self):
        """Anything after the grant, or the end of the stream, means the host no longer holds it for us."""
        try:
            self.rfile.readline()
        except OSError:
            pass
        if not self._stop.is_set():
            self.lost.set()

    def _close(self):
        self._stop.set()
        try:
            self.sock.close()
        except OSError:
            pass

    def __exit__(self, *exc):
        if self.nested:
            return False
        if self._prev is None:
            os.environ.pop("QABENCH_HEAVY_HELD", None)
        else:
            os.environ["QABENCH_HEAVY_HELD"] = self._prev
        self._stop.set()
        try:
            self.sock.sendall(b"release\n")
        except OSError:
            pass
        self._close()
        return False


# ---------------------------------------------------------------- the service, on the host

HOLD = f"import sys; print({GRANTED!r}, flush=True); sys.stdin.read()"


def _serve_one(conn: socket.socket, peer, log):
    conn.settimeout(SILENT)
    rfile = conn.makefile("r", encoding="utf-8", errors="replace")
    try:
        hello = json.loads(rfile.readline() or "{}")
    except (ValueError, OSError):
        conn.close()
        return
    name = str(hello.get("name") or "a container's heavy run")[:200]
    # The container's declared cores; a client from before the budget declares none and takes the whole host.
    cores = hello.get("cores")
    cores = ["--cores", str(cores)] if isinstance(cores, int) and not isinstance(cores, bool) and cores > 0 else []
    who = f"{str(hello.get('who') or 'an unnamed session')[:200]}, in a container via the host lock service"
    env = {k: v for k, v in os.environ.items() if k not in ("QABENCH_HEAVY_HELD", "QABENCH_HEAVY_LOCKD", "LAND_SESSION",
                                                            "ANAT_SESSION")}
    env.update(QABENCH_SESSION=who, QABENCH_LOCKD_HOLDER=name, PYTHONUNBUFFERED="1",
               PYTHONPATH=os.pathsep.join(filter(None, [str(Path(__file__).resolve().parent.parent),
                                                        os.environ.get("PYTHONPATH")])))
    # The waiter IS a host `qabench heavy`: same flock, same queue ticket, same holder line, kernel's order.
    child = subprocess.Popen([sys.executable, "-m", "qabench", "heavy", "--name", name, *cores, "--", sys.executable, "-c", HOLD],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                             text=True, start_new_session=True)
    log(f"lockd: {peer[0]}:{peer[1]} waits: {name} for {who} (host pid {child.pid})")
    send = threading.Lock()
    done = threading.Event()

    def relay():
        for line in child.stdout:
            line = line.rstrip("\n")
            if line.startswith("heavy: ") and " exited " in line:
                continue                                       # the hold's own summary; the client prints its own
            with send:
                try:
                    conn.sendall((line + "\n").encode())
                except OSError:
                    break
            if line == GRANTED:
                log(f"lockd: {peer[0]}:{peer[1]} holds: {name} for {who}")
        if not done.is_set():                                  # the host process ended under a live client: say so
            log(f"lockd: {peer[0]}:{peer[1]}: the host process for {name} ended before release")
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    threading.Thread(target=relay, daemon=True).start()
    why = "closed the connection"
    try:
        for line in rfile:
            if line.strip() == "release":
                why = "released it"
                break
        # else: the client went away
    except (socket.timeout, TimeoutError):
        why = f"went silent for {SILENT}s (a container killed outright sends nothing)"
    except OSError as ex:
        why = f"dropped ({ex})"
    done.set()
    try:
        child.stdin.close()                                    # a granted hold ends on this
    except OSError:
        pass
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:                          # still waiting in the queue: end it there
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
    log(f"lockd: {peer[0]}:{peer[1]} {why}: {name} for {who} — its host process ended, rc {child.returncode}")
    try:
        conn.close()
    except OSError:
        pass


def serve(bind: str = "127.0.0.1", port: int = PORT, log=print, ready=None) -> None:
    srv = socket.create_server((bind, port), reuse_port=False)
    log(f"lockd: serving the heavy-run lock "
        f"{os.environ.get('QABENCH_HEAVY_LOCK') or Path.home() / '.qabench' / 'heavy.lock'} on {bind}:{port}")
    if ready:
        ready(srv.getsockname()[1])
    while True:
        conn, peer = srv.accept()
        threading.Thread(target=_serve_one, args=(conn, peer, log), daemon=True).start()


def main(argv: list[str]) -> int:
    bind = argv[argv.index("--bind") + 1] if "--bind" in argv else "127.0.0.1"
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else PORT
    try:
        # Every line carries its UTC time: a log with no times could not say what the service saw (2026-11-02).
        serve(bind, port, log=lambda s: print(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {s}", flush=True))
    except KeyboardInterrupt:
        return 0
    return 0
