# Shared resource admission — local draft, inactive

Rami authorized isolated source implementation and review while another Codex task and the staging/promotion process remain active. This change adds source only. It does not acquire the real machine lock, inspect live memory, start a test, install a plugin, create a daemon, or change a runner/workflow.

## What the current code establishes

Anat's `tests/conftest.py::pytest_configure` checks interpreter pins and acquires `tests/_suite_lock.py`. That lock protects shared test accounts. Its `Makefile` explicitly sets `ANAT_SUITE_LOCK=0` for isolated suites, correctly allowing independent databases to coexist. Its separate `scripts/suite_preflight.py` samples machine pressure, but that memory check is not fully called by the pytest hook. Therefore a statement that “bare pytest has no guard at all” is too broad, and a statement that “the suite lock protects laptop capacity” is also false.

Five other project workflows inspected in the owned drafts use self-hosted Linux runners. They can consume the Mac's resources through Docker even while a macOS process sees a different hostname, filesystem or kernel-lock domain. Per-project locks, GitHub workflow concurrency and container-local memory measurements cannot provide one laptop-wide resource budget.

No current lock, runner or other task was changed by this inspection.

## Draft mechanism

`qabench.resource_gate.HostLease` is an opt-in library. Importing it has no side effects. A future caller supplies one protected, absolute host-state directory, task identifier, project, worktree, workload kind and an explicit free-memory threshold. It holds an exclusive nonblocking kernel lock before sampling memory. A second participating workload refuses immediately with the current owner's task rather than silently waiting or starting.

The receipt records host, task, project, worktree, PID, workload type, start/end, initial memory observation and policy threshold. It deliberately does not record command arguments or environment values. macOS pressure must be normal and free-memory percentage must satisfy the declared threshold; unknown or unsupported host observations refuse. No threshold has been calibrated on this laptop by this draft.

Normal completion releases after the caller's work and cleanup end. A crash leaves an active receipt even if the kernel releases the file lock. The next acquisition refuses until an operator has reconciled the previous workload and any orphan workers. Age or a dead parent alone cannot establish that all child processes have finished. There is no automatic stale-lock deletion and no process-killing command.

This is **cooperative admission, not enforced machine isolation**. It does not stop an uninstrumented pytest, build, Docker service or different user's process. It neither samples ongoing peak RSS nor limits memory after admission. Every admitted caller must hold ownership until its entire worker tree has terminated; context-manager exit is not a substitute for worker cleanup. There is no production/staging authorization in this resource lease.

## Adoption sequence, after capacity is available

1. Qualify the lease in disposable state: competing projects, separate processes, low/unknown memory, holder crash and malformed receipt; then verify healthy release/reacquisition. The new source tests have not run.
2. Choose one host-level broker/state authority for macOS and Docker runners. All processes sharing laptop memory must request the same authority; a lock inside each container is insufficient. Bind task/run identity and workload lifetime, not merely the short-lived Docker client command.
3. Integrate an early pytest plugin into every supported entry point before project conftest imports or fixture/server startup. Confirm direct `pytest`, `python -m pytest`, Make targets, mutation subprocesses and browser tiers actually reach it. A wrapper alone does not cover bypasses. No such plugin is activated in this increment.
4. Integrate builds and runner jobs through the same authority. Handle xdist/child ownership as one workload; children must not contend for a second lease held by their parent. Preserve existing database/account locks because they protect different resources.
5. Register the already-running services and runs before enforcement, without terminating them. Missing attribution is a named unknown. A memory snapshot cannot prove an unregistered busy process is safe.
6. Make the broker's queue/owner/age visible across tasks; include an independent heartbeat so broker failure is observable. Keep admission separate from the landing/promotion lock and acquire locks in one documented order to avoid deadlocks.
7. Establish worker and memory limits from measurements, then allow bounded parallel light work if justified. The initial draft admits one participating expensive workload; source editing and read-only review do not request a lease.

Activation must not occur midway through today's testing/promotion. Before activation, reconcile this draft with any concurrent implementation of a machine gate, retain one owner/implementation, and prove it on the current merged candidate. The eventual migration of callers is required work, not something this source-only library already achieved.
