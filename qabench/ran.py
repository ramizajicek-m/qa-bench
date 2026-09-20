"""ran — a run reports what it REACHED, and a run that did not reach its subject is INVALID, never a pass.

    python -m qabench ran --name e2e -- make test-e2e
    python -m qabench ran --name land --json -- make land

WHY. Two incidents on 2026-09-20, and they are the only two of that day whose
false direction was a PASS. Everything else made the estate look worse than it
was; these made it look better.

  `make land | tail -25` yields TAIL's exit code. A failed gate reported
  success, and the pipe hid every line of the run for its whole duration. The
  kit ledger already carries the same shape from 2026-09-05, where a sweep's
  stdout went through `grep | head -80` and a truncated ledger was read as the
  result.

  An e2e sweep died in the conftest login fixture with `status=500`, 83 times,
  before loading a single page: exit code 2, ZERO "FAILED" lines. A caller
  grepping for FAILED reads that as a clean sweep and closes a row on a run
  that never started. An aborted run and a clean sweep are textually identical
  unless somebody reads the tail — so no rule may depend on somebody reading
  the tail.

  That second run was first reported to this module's author as host
  contention, a peer session's docker stack up on the same Mac. It was not: the
  cause was the wrong entry point, `make test` rather than `make e2e`, which
  boots no database and no app. The session that reported it checked its own
  command and withdrew the diagnosis, and this module is written on the
  withdrawal rather than on the story, because a guard justified by a
  measurement that turns out to be false is worse than no guard. Hence: the
  host is RECORDED and never judged — there is no measured instance of
  contention producing a false pass, so nothing here refuses to start on one,
  and if the first real instance ever arrives, the artefacts hold the evidence
  instead of a recollection. (Machine-wide serialisation is a separate rule
  standing on separate, measured evidence: three concurrent suites turned a
  15-minute gate into 35. Slowness, not a false verdict.)

  THE SHAPE IS INDEPENDENT OF THE CAUSE, which is why it is still worth an
  instrument: a run that dies in its fixtures exits non-zero, prints zero
  FAILED lines, and reads as clean — whether the cause is a wrong harness, a
  dead host, an OOM kill or contention.

THE RULE, in one sentence: a verdict comes from an ARTEFACT OF COMPLETION, and
"no failures" is never read as success on its own. A check that cannot tell
"the code is wrong" from "the host was busy" is not a check.

  PASS     the command exited 0, the output carries the declared completion
           marker, the marker's count is greater than zero, nothing refused,
           nothing failed, and — where the command declares one — the artefact
           saying it DID THE THING is present
  FAIL     something the runner calls a failure is in the output, whatever it
           exited — a runner that reports failures and exits 0 is a FAIL here
  REFUSED  the command decided not to act and said so. Not a defect; not a pass
  INVALID  exit non-zero with nothing reported failed · no completion marker at
           all · a marker whose count is zero · a command that can act and
           never said it did · a declared GATE that was not attempted and does
           not say where it does run. Exit 3, and 3 is never read as 0

A GATING CHECK THAT EXISTS ONLY IN CI IS INVISIBLE TO THE PERSON WHO CAN ACT ON
IT. anat's catalogue ratchet judges ruff and semgrep. ruff runs in the per-change
tier — a second, pinned, with a self-test that a synthetic undefined name still
comes back F821. semgrep is a minute of CPU, so it runs only in the `lint` job,
and locally its assertion SKIPS. The consequence is not that semgrep is
unchecked; it is checked, in CI. The consequence is that the per-change tier has
NEVER ONCE executed it, so there is a class of finding nobody can reproduce
before landing: the first you learn of one is a red job, and GitHub withholds
logs until the whole run completes, so for the window that matters you have a
red gate you cannot read on a cause you cannot reproduce.

The contract question was put to this kit directly: must every gating check be
runnable locally, or must it merely SAY SO when it is not? The floor here is the
second and the target is the first, because "runnable locally" is not always
affordable — a minute of semgrep per change is how people stop running the tier
at all — while "gates you silently and invisibly" is never acceptable. So a
command declares its `gates:`, each with the evidence that it ran; a gate with
no evidence in the output is named IN THE VERDICT, with where it does run and
what would make it runnable here. A gate that cannot say where it runs is
INVALID: that is the silent case, and it is the only one refused outright.

A skipped check and a passed check are textually identical unless something
insists on the difference — the same sentence as the artefact-of-completion rule
above, one level out.

A REFUSAL AND A SUCCESS MUST NOT BE THE SAME OBSERVATION, which is the live
instance this grew from, hours after the module was written. `make land`
printed "REFUSING TO LAND: tier1 is red on the merged tree" and `make: ***
[land] Error 1`, and the wrapper invoking it reported exit 0 — the status came
from the end of a pipeline rather than from the command. Nothing had landed and
the tree was unchanged. The hurt is not to the author reading the tail: it is
to the NEXT session in a serialised lane, which judges the landing by its status,
concludes it pushed, and advances the queue past a refusal nobody saw. A session
that believes it landed stops watching.

The repo already had the rule — capture `$?` from the command, never from the
pipeline; `set -o pipefail` on any block that pipes — written down twice, and
the Makefile applies it to the targets it owns. It still happened, because THE
PIPE WAS NOT IN THE CALLEE. A repo can harden every target it owns and still be
invoked through a pipeline it does not control. That is why this module is the
CALLER: argv with no shell is not a hardening anyone has to remember.

So a command that can refuse declares `refused:`, and a command that acts
declares `decided:` — the artefact it prints when it did the thing ("pushed
<sha>"). A PASS then asserts the artefact rather than the absence of a
complaint, and "it exited 0" is never the evidence that anything happened.

Three mechanics carry it, each paid for by one of the incidents above:

  THE COMPLETION ARTEFACT DECIDES FIRST, the exit code second. An exit code is
  the thing a pipeline eats; the artefact is not. anat's scripts/suite_postflight.py
  is the reference implementation and predates this module — it is where the
  `_DONE` shapes below and the habit of stating the weaker claim out loud come
  from.
  NO SHELL. The command is argv, run directly. There is no pipeline for a
  filter to swallow the exit code into, which is the `| tail -25` row.
  THE WHOLE OUTPUT IS KEPT, tee'd to a file as it is read, never through a
  filter that can close early — and the verdict reads the FILE.
  THE HOST IS RECORDED, NEVER JUDGED — the declared ports, processes and
  containers, snapshot before the run and written into the artefact. Reported,
  not a finding: see the withdrawal above.

WHAT IT CANNOT SEE, stated: whether the run's ASSERTIONS were any good. This is
the completion half only. A suite that reached the end and executed 2,321
honest-looking tests over the wrong population is exactly what `qabench
population` is for, and neither stands in for the other.

Manifest shape:

    ran:
      artefacts: qa/runs                 # one JSON per run, tracked
      record:                            # what was up on the host, for the artefact — never a verdict
        ports: [5432, 3000, 9000]
        processes: ["test_stack.sh"]
        containers: ["anat-postgres", "anat-postgrest"]
      commands:
        e2e:
          completed: '(\\d+) (?:passed|deselected)'   # optional; the kit's pytest-shaped default is used
          failed: '^FAILED |(\\d+) failed|(\\d+) error'   # without it, the run is judged on completion alone
        tier1:
          gates:                            # checks that gate a change but may not run HERE
            - name: semgrep
              evidence: '^semgrep: \\d+ findings'   # what its having run looks like
              elsewhere: "the `lint` job in qa-nightly.yml"
              locally: "make venv-semgrep"           # optional, and the target to aim at
        land:
          completed: 'make: \\*\\*\\* |pushed |REFUSING'
          refused: '^REFUSING TO LAND'      # a decision, not a defect — and never a pass
          decided: '^pushed [0-9a-f]{7,40}' # the artefact; a PASS asserts THIS, not exit 0
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PASS, FAIL, REFUSED, INVALID = "PASS", "FAIL", "REFUSED", "INVALID"
EXIT = {PASS: 0, FAIL: 1, REFUSED: 1, INVALID: 3}


@dataclass
class Host:
    """What was up on this machine when the run started."""
    ports: dict[str, bool] = field(default_factory=dict)
    processes: dict[str, int] = field(default_factory=dict)      # pattern -> how many matched
    containers: list[str] = field(default_factory=list)
    docker: str = ""                                             # "" or why it could not be asked

    def busy(self, declared: dict) -> list[str]:
        """What was up. RECORDED IN THE ARTEFACT, never a verdict — no measured
        instance exists of any of this producing a false pass, and the one that
        was reported as such was a wrong entry point. The day a real instance
        arrives, these lines are what turns it from a recollection into
        evidence."""
        out = [f"port {p} was listening" for p, up in self.ports.items() if up]
        out += [f"{n} process(es) matching {pat!r}" for pat, n in self.processes.items() if n]
        out += [f"container {c} was up" for c in self.containers if c in (declared.get("containers") or [])]
        return out


def _listening(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket() as s:
        s.settimeout(0.25)
        return s.connect_ex((host, int(port))) == 0


def snapshot(declared: dict) -> Host:
    """Ask, never assume. A tool that is absent is recorded as absent, not as clean."""
    h = Host()
    for p in declared.get("ports") or []:
        h.ports[str(p)] = _listening(p)
    patterns = declared.get("processes") or []
    if patterns:
        try:
            ps = subprocess.run(["ps", "-Ao", "pid,ppid,command"], capture_output=True, text=True, timeout=20).stdout
        except (OSError, subprocess.SubprocessError):
            ps = ""
        rows = []
        for line in ps.splitlines()[1:]:
            parts = line.split(None, 2)
            if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
                rows.append((int(parts[0]), int(parts[1]), parts[2]))
        # OUR OWN ANCESTORS ARE NOT THE HOST. A shell whose command line is the
        # whole compound command that launched this run contains every pattern
        # the caller typed — including the pattern being looked for. Measured
        # here the first time this was run: a pattern no process was named
        # after matched once, in the zsh that had just been handed it. Walking
        # up from getpid() is the only reading of "what ELSE is up".
        parent = {pid: ppid for pid, ppid, _ in rows}
        mine, pid = set(), os.getpid()
        while pid and pid not in mine:
            mine.add(pid)
            pid = parent.get(pid, 0)
        for pat in patterns:
            h.processes[pat] = sum(1 for pid, _, cmd in rows if pat in cmd and pid not in mine)
    if declared.get("containers"):
        if not shutil.which("docker"):
            h.docker = "docker is not on PATH — containers not asked about"
        else:
            try:
                p = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=30)
                h.containers = sorted(n for n in p.stdout.split() if n) if p.returncode == 0 else []
                h.docker = "" if p.returncode == 0 else f"docker ps exited {p.returncode}"
            except (OSError, subprocess.SubprocessError) as ex:
                h.docker = f"docker ps could not run: {ex}"
    return h


#: Every shape pytest uses to say it REACHED THE END, lifted from anat's
#: scripts/suite_postflight.py, which has been asserting this since 2026-08-22.
#: "no tests ran" and "collected" count: they are verdicts, just not about
#: failures. `[100%]` is here because a targeted `-q --no-header` run often
#: prints nothing else — and it still discriminates, since a killed run shows
#: the percentage it reached (`[ 52%]`) and 100 is reached only by finishing.
DONE = (r"\b\d+\s+(passed|failed|error|errors|skipped|deselected|xfailed|xpassed)\b"
        r"|no tests ran"
        r"|\b\d+\s+tests?\s+collected\b"
        r"|\berror\b.*\bcollecting\b"
        r"|\[\s*100%\s*\]")
#: Used only when the command declares no `failed:`. A run judged on completion
#: alone makes the WEAKER claim, and `run_one` writes that into the artefact
#: rather than letting it read like the strong one.
FAILED_DEFAULT = r"^FAILED |^ERROR |\b\d+ (?:failed|errors?)\b"


def verdict(exit_code: int, output: str, spec: dict) -> tuple[str, str]:
    """(PASS | FAIL | INVALID, the sentence). Pure: the whole rule lives here.

    THE ARTEFACT OF COMPLETION DECIDES FIRST and the exit code last. An exit
    code can be replaced by a pipeline's — `make land | tail -25` yields
    tail's — so a rule that consults it first is a rule a pipe can launder.
    Nothing can fake a summary line the runner never printed.
    """
    completed = spec.get("completed") or DONE
    failed = spec.get("failed") or FAILED_DEFAULT
    refused, decided = spec.get("refused"), spec.get("decided")
    gates = spec.get("gates") or []
    hits = list(re.finditer(completed, output, re.M))
    counts = [int(g) for m in hits for g in m.groups() if g and g.isdigit()]
    failures = list(re.finditer(failed, output, re.M))

    if not hits:
        return INVALID, (f"nothing in the output matches the completion marker {completed!r} — THE RUN DID NOT "
                         f"FINISH, whatever it exited ({exit_code}). It also printed "
                         f"{'no' if not failures else str(len(failures))} failure line(s), so anything grepping "
                         "for failures would call this green")
    if counts and not any(counts):
        return INVALID, (f"the run reached the end and executed NOTHING ({completed!r} matched a count of 0) — "
                         "an empty run is not a clean one")
    if refused and re.search(refused, output, re.M):
        return REFUSED, (f"the command REFUSED and said so ({refused!r} matched), whatever it exited "
                         f"({exit_code}) — a refusal and a success must never be the same observation, and "
                         "the next session in the lane reads this one")
    if failures:
        return FAIL, (f"the runner reported failure{'' if len(failures) == 1 else 's'} "
                      f"({len(failures)} line(s) matched)"
                      + (f", and exited {exit_code}" if exit_code
                         else " and exited 0 — a runner that reports failures and exits 0 is still a failure"))
    if decided and not re.search(decided, output, re.M):
        return INVALID, (f"nothing in the output matches {decided!r} — the command never said it DID the thing, "
                         "and `it exited 0` is not evidence that anything happened. Assert the artefact")
    unattempted = [g for g in gates if not re.search(g.get("evidence") or r"(?!x)x", output, re.M)]
    silent = [g for g in unattempted if not g.get("elsewhere")]
    if silent:
        return INVALID, ("gating check(s) " + ", ".join(str(g.get("name", "?")) for g in silent)
                         + " were not attempted here and do not say where they DO run — a check that gates you "
                           "silently and invisibly is the one case this refuses outright")
    if exit_code != 0:
        return INVALID, (f"exited {exit_code} with nothing reported failed — the run finished but its exit code "
                         "disagrees with its own summary, and reading that as a pass closes a row on nothing")
    note = ""
    if unattempted:
        note = " — NOT ATTEMPTED HERE: " + "; ".join(
            f"{g.get('name', '?')} (runs in {g['elsewhere']}"
            + (f"; `{g['locally']}` to run it here)" if g.get("locally") else ")")
            for g in unattempted)
    return PASS, (f"exited 0, finished, {counts[0] if counts else 'n/a'} executed, nothing refused, nothing failed"
                  + (f", and it said so ({decided!r})" if decided else "") + note)


def execute(argv: list[str], log: Path, *, cwd: Path, echo=print) -> int:
    """Run argv with no shell, tee every line to `log`, return the real exit code.

    Reading the pipe in this loop is what makes it safe: a PIPE nobody drains
    deadlocks at 64 KB, and a filter on the other end can close early and take
    the exit code with it. Neither can happen to a loop that owns both ends.
    """
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as fh:
        p = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1)
        for line in p.stdout:
            fh.write(line)
            echo(line.rstrip("\n"))
        p.stdout.close()
        return p.wait()


def run_one(root: Path, cfg: dict, name: str, argv: list[str], *, now=None, echo=print) -> dict:
    """Preflight, run, judge, and write the artefact. The artefact IS the result."""
    now = now or dt.datetime.now(dt.timezone.utc)
    declared = cfg.get("record") or {}
    spec = (cfg.get("commands") or {}).get(name) or {}
    art_dir = root / (cfg.get("artefacts") or "qa/runs")
    host = snapshot(declared)
    log = art_dir / f"{name}.log"
    code = execute(argv, log, cwd=root, echo=echo)
    v, why = verdict(code, log.read_text(encoding="utf-8", errors="replace"), spec)
    record = {
        "name": name, "argv": argv, "started": now.isoformat(), "cwd": str(root),
        "host": host.__dict__, "host_busy": host.busy(declared),
        # The weaker claim, stated out loud rather than quietly widened: a
        # command the manifest does not describe is judged on the kit's
        # pytest-shaped defaults, which are right for a pytest run and a guess
        # for anything else.
        "declared": bool(spec), "verdict": v, "why": why, "exit_code": code,
        # Named in the artefact as well as in the sentence: the next session
        # reads the JSON, and a gate nobody attempted is exactly what a green
        # local run otherwise fails to mention.
        "not_attempted": [g.get("name") for g in (spec.get("gates") or [])
                          if not re.search(g.get("evidence") or r"(?!x)x",
                                           log.read_text(encoding="utf-8", errors="replace"), re.M)],
        "log": str(log.relative_to(root)), "finished": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if not spec:
        record["why"] += (f" — judged on the kit's default markers; `ran.commands.{name}` declares none, so this "
                          "is the weaker claim")
    art_dir.mkdir(parents=True, exist_ok=True)
    (art_dir / f"{name}.json").write_text(json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")
    record["artefact"] = str((art_dir / f"{name}.json").relative_to(root))
    return record


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def run(argv: list[str], *, echo=print) -> int:
    if "--" not in argv:
        print("usage: python -m qabench ran --name NAME -- COMMAND [ARGS...]\n"
              "the command after `--` is run as argv, never through a shell: a pipeline is how "
              "`make land | tail -25` reported a failed gate as success", file=sys.stderr)
        return 3
    cut = argv.index("--")
    opts, cmd = argv[:cut], argv[cut + 1:]
    if not cmd:
        print("nothing after `--` to run (exit 3)", file=sys.stderr)
        return 3
    root = Path(_arg(opts, "--repo", ".")).resolve()
    name = _arg(opts, "--name") or Path(cmd[0]).name
    mpath = root / "qa" / "manifest.yml"
    doc = (yaml.safe_load(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}) or {}
    cfg = doc.get("ran")
    if not cfg:
        print(f"no `ran:` block in {mpath} — nothing declares what completion looks like for this project, "
              "so no run here can be told from one that died in its fixtures (exit 3)", file=sys.stderr)
        return 3
    record = run_one(root, cfg, name, cmd, echo=echo)
    if "--json" in opts:
        print(json.dumps(record, indent=1, ensure_ascii=False))
    else:
        print(f"\n{record['verdict']}  {name}: {record['why']}")
        print(f"       artefact {record['artefact']}" + (f" · log {record['log']}" if record["log"] else ""))
    return EXIT[record["verdict"]]
