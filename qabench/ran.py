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

A DECISION FILE HAS A FOURTH STATE NOBODY DESIGNS FOR. Pass, fail and
did-not-run are the three anybody plans. The fourth is A PREVIOUS RUN'S VERDICT,
readable before the next run clears it: perfectly well-formed, and about
different code. So every artefact stamps the commit it decided about, and
`stale()` says so when the tree has moved — because without it a reader cannot
distinguish "this run passed" from "some earlier run passed", and the second
reads exactly like the first.

THE ACT OF OBSERVING IS NOT FREE. An investigation can consume, trigger or
destroy the thing it is investigating, and it does so through the steps that
look LEAST like intervention — recording, preparing, checking. The harmlessness
is not incidental to the hazard, it is the mechanism: a step that announced
itself as consequential would have been examined first. Three instances follow,
from one project in one day, sharing NO mechanism — a git remote's side effect,
an automation trigger, resource contention. What they share is the reasoning
that walks into them: "this is only a read", "this is only preparation", "this
is only writing it down". EACH OF THOSE IS A CLAIM ABOUT INTENT, AND SYSTEMS
RESPOND TO ACTIONS — which is why a list of known triggers will not cover it:
the next one will be a mechanism nobody listed.

THE PRACTICAL TEST, which is worth more than the instances: FOR ANY STEP TAKEN
BECAUSE IT SEEMS FREE, ASK WHAT IS DOWNSTREAM OF ITS SUCCESS, AND WHAT IT
CONSUMES WHILE IT RUNS. Three sub-questions cover every instance here and
generalise past them:

    does it WRITE anywhere the system under investigation READS?
        (a push, a branch, a file something watches)
    does anything FIRE on its completion?
        (auto-promote, auto-merge, a webhook, a job triggered by an artefact)
    does it CONSUME the scarce thing whose scarcity is the subject?
        (a runner, a lock, a rate limit, a connection pool)

AND ITS LIMIT, because this could easily become a rule that stops anybody
recording anything: THE ANSWER IS ALMOST ALWAYS "YES, AND IT IS FINE" — nothing
pending, nothing fires, nothing scarce — so write it down and land it now. It is
a QUESTION ASKED AT THE MOMENT, never a practice. And it has to be a prompted
question rather than a remembered rule: two of the three instances were about to
be committed by people who had ALREADY READ THE FIRST. UNDERSTANDING THE SHAPE
DID NOT DEFEND AGAINST IT.

  THIRD INSTANCE — WATCHING EXTENDS THE WAIT. A post-deploy guard is queued
  behind a six-shard browser tier on a single self-hosted runner. Polling for
  it means running jobs — or at minimum API calls in a loop — against the very
  machine whose scarcity is the reason it is queued. OBSERVING THE CONTENTION
  PARTICIPATES IN IT. (This was very nearly the next move of the session that
  found the first two.)

FIRST INSTANCE — RECORDING AN INCIDENT IS NOT FREE — THE ACT OF RECORDING IT CAN DESTROY THE
EVIDENCE THAT WOULD HAVE EXPLAINED IT. This is a different category from every
other failure in this kit: the rest are instruments that MEASURE THE WRONG
THING, and this is an instrument that CHANGES THE THING.

A staging deploy failed on a commit whose CI was green, with no build and no
logs attached, so no cause could be established from the record. Two readings
were available and one experiment separated them — the NEXT commit carried the
same config, so if it built, the "it tried to build without the config" reading
was dead. That deployment was PENDING. The write-up was finished and about to
land: deployment ids, the success and failure records side by side, the missing
build. LANDING PUSHES TO MAIN. A PUSH TO MAIN CREATES A DEPLOYMENT. A NEW
DEPLOYMENT SUPERSEDES THE PENDING ONE. The record would have documented an
unresolvable mystery AND MADE IT UNRESOLVABLE, in the same commit, and it would
have been accurate about everything except the one thing that mattered.

The commit was held, the deployment resolved (it succeeded — the innocent
reading, a single unexplained gate-stage failure), and the record landed WITH
the resolution in it.

BEFORE RECORDING AN INCIDENT, ASK WHETHER YOUR RECORDING MECHANISM TOUCHES THE
SYSTEM UNDER INVESTIGATION. It does more often than it sounds: any repo whose
pushes trigger deploys, any incident about a queue where filing takes a slot,
any investigation into a runner where your own job competes for it, any
log-volume problem investigated by writing logs, any lock contention diagnosed
by taking the lock. The path is invisible because "WRITE IT DOWN" IS THE ONE
ACTION EVERYBODY TREATS AS SAFE, and every rule about incident response says
record it immediately and before it resolves — advice that is right, and that
here would have burned the evidence.

DO NOT TURN THIS INTO A POLICY ABOUT WHEN TO COMMIT. The session that found it
HELD the write-up while the deployment that would explain the failure was
pending, and RELEASED it — two further landings — as soon as that deployment
resolved. BOTH WERE CORRECT, and no rule of the form "hold incident records
until X" or "land them immediately" gets both right, because they are OPPOSITE
ACTIONS JUSTIFIED BY THE SAME FACT: the experiment had finished.

So it is a QUESTION ASKED AT THE MOMENT OF RECORDING, not a practice followed:
DOES MY RECORDING MECHANISM TOUCH THE SYSTEM UNDER INVESTIGATION, AND IS
ANYTHING STILL PENDING THAT IT WOULD DISTURB? If yes, hold, and say in the
record that you held and why — otherwise the next person wonders about the gap
between the timestamp in the prose and the timestamp on the commit. If nothing
is pending, LAND IT NOW: holding a record for its own sake is just a record that
does not exist yet.

THAT SHAPE GENERALISES PAST THIS HAZARD AND IS THE MORE USEFUL HALF. THE HAZARDS
HERE ARE SITUATIONAL, SO A POLICY ENCODES ONE SITUATION AND MISFIRES IN THE
NEXT. A QUESTION TRAVELS. AND THE SECOND-ORDER VERSION FOLLOWS
IMMEDIATELY: the same hazard applies to the FIX. Retrying a failed deploy to see
whether it fails again ALSO supersedes the pending one. "Reproduce it" and
"observe it" can both be the destructive act, not only the write-up.

THE HARMLESS PRECURSOR IS THE IRREVERSIBLE ACT — the recording hazard above has
a twin, and the two need each other. A coordinating session asked for a
read-only answer to "what is the production promotion gate still missing for
this commit, and how long would producing it take?" — explicitly so the later
decision could be "it can go in N minutes" — and said IN CAPITALS: prepare
nothing, promote nothing. SATISFYING THAT GATE IS THE PROMOTION. The repo had
PROMOTE_ON_GREEN set, and the nightly's promote job needed exactly those two
gate jobs and dispatched the production deploy about forty seconds after they
passed; there is no gather-then-decide step anywhere in the path. So the
instruction's ONLY possible execution was a production release nobody had
authorised, written in the same message as the instruction not to.

It was not caught by care, and care would not have found it: the request was
innocuous and the constraint sounded conservative. It was caught because
answering the TIMING question meant reading the workflow, and the promote job
sat forty lines below the jobs being looked up. Nobody reads a workflow to
answer a timing question.

Two instances, different mechanisms, one form — recording an incident would
have destroyed its evidence; preparing a decision would have MADE it — AND IN
BOTH THE HARMLESSNESS IS WHAT CARRIES IT, because a step that announced itself
as consequential would have been checked. So: BEFORE DOING THE HARMLESS
PRECURSOR, READ WHAT IT TRIGGERS. And since that is unbounded, the practical
test: for any action framed as preparation, gathering, recording or checking,
ask what is DOWNSTREAM OF ITS SUCCESS — not what the action does, but what
happens automatically when it succeeds. Auto-promote on green, auto-merge on
green, a deploy on push, a webhook on a status change, a scheduled job that
fires when an artefact appears. Each turns a read into a write, and none is
visible from the thing you were asked to do.

AND THE MIRROR IMAGE, which is the failure of applying this too hard: A DECISION
THAT LOOKS LIKE A DEFECT COSTS THE SAME AS A DEFECT THAT LOOKS LIKE A DECISION.
In the same investigation six browser-tier shards were failing in the nightly
while production promoted anyway — which reads as a gap and was not: the tier
had been deliberately made post-promote surveillance, dated, after a four-hour
browser leg on one shared runner left production 25 commits behind a green main
three runs running, and made safe by an automated post-deploy rollback landing
FIRST. The discriminator is identical in both directions — DOES THE RECORD NAME
AN ATTEMPT AND A REASON? It did, in a comment, at the point of the change: the
argument for writing the reason AT THE SITE rather than in a document nobody
reads on the night.

THE RIGHT CHECK AT THE WRONG TIME: A SAFETY ARGUMENT WHOSE PRECONDITION IS
SCHEDULED BEHIND THE THING IT PROTECTS AGAINST. A promote gate was deliberately
loosened — a four-hour browser tier became post-promote surveillance — and the
workflow says, at the site, what made that safe: every project gained an
automated post-deploy rollback first, and the rule is rollback before
gate-loosening, never the reverse. The reasoning is correct and the order holds
in the DESIGN. It does not hold in the SCHEDULE. Measured minutes after a real
promotion: production served the new commit, and the rollback `guard` job — the
thing the whole loosening rests on — was QUEUED BEHIND SIX BROWSER SHARDS on a
single self-hosted runner, one in progress. The tier had run 21:10 to 01:04 the
night before. For a window after every promotion, the deployment is live and
the thing that would roll it back has not started.

Every other failure in this kit is a check that measures the WRONG THING. This
one measures the RIGHT thing at the WRONG TIME: the guard is correct, the tier
is correctly non-gating, and the queueing is a property of having one runner
rather than a defect in any workflow. THE FAILURE IS IN THE COMPOSITION, AND NO
INSTRUMENT ASKS WHEN A CHECK RUNS RELATIVE TO THE RISK IT COVERS. It was visible
only because the precondition was written down at the site — without that
sentence, a guard running late looks like a guard.

So: WHEN A GATE IS LOOSENED BECAUSE SOMETHING ELSE COVERS THE RISK, ASK WHETHER
THE COVERING THING IS SCHEDULED TO RUN BEFORE THE EXPOSURE BEGINS, NOT MERELY
WHETHER IT EXISTS. The repair is priority, not policy: the guard needs the runner
before the surveillance tier does. The same repository had learned this once
already — its gates sat queued behind a 60-minute browser leg for three runs
running and production stayed 25 commits behind a green main, fixed by ordering
the browser tier after the gates — and the guard was the piece not included in
that reordering. Across one estate the MECHANISM was present in five of five projects and the
EXPOSURE verified in one: whether a project is exposed turns on one question —
DOES ITS POST-DEPLOY PATH START A LONG JOB ON THE SAME RUNNER BEFORE OR WITH THE
GUARD? If the guard is the only thing queued, design and schedule agree and there
is nothing to fix. It is per-project scheduling, so it is carried here as a
question rather than a check.

AFTER ANY MUTATING STEP, READ BACK THE VALUE THAT MUST HAVE MOVED, AND ASSERT IT
MOVED. Not "did the command succeed" — exit codes lie by omission — but "is the
thing that had to change now different". `decided:` above is this rule for a
command this module runs; the rule itself is wider and applies to every step a
session takes by hand. Three instances in one session, three different kinds,
none of which any guard would have found:

  A STALE REPORT READ AS A FRESH ONE. A resolver was patched, a sweep launched,
  and `judged 7500` reported — BYTE-IDENTICAL TO THE PREVIOUS RUN, to the digit,
  after a change that had to move it. The run had not finished; the previous
  report was being read. THE TELL WAS THE DIGITS, NOT THE TIMESTAMP.

  A COMMIT THAT SILENTLY DID NOT HAPPEN. Backticks inside a double-quoted commit
  message ran as COMMAND SUBSTITUTION, the chain died, and `git add` had already
  succeeded — so the tree looked committed. Caught only by printing
  `git log --oneline -1` and reading the OLD sha where a new one belonged.

  A BULK EDIT THAT TOUCHED THE WRONG THING AND STOPPED. A colour rewrite
  anchored on `color:` also matched the tail of `border-color:`; its own
  assertion aborted after the first stylesheet was written and before the
  second, so one file changed, one did not, and the count of rewritten files did
  not match the count of files.

  A FETCH THAT TIMED OUT AND WAS NEVER READ BACK. `git fetch origin` timed out
  at session start and was moved to the background; an audit then read `main`
  seven commits behind `origin/main`, and its findings survived only because
  none of the audited files changed across that range. A TIMED-OUT COMMAND IS
  THE LOUDEST POSSIBLE SIGNAL AND IT STILL PASSED SILENTLY, because the next
  step read a ref that was merely PRESENT. PRESENCE IS NOT FRESHNESS. The
  read-back for a fetch is `git ls-remote origin refs/heads/<branch>` equal to
  `git rev-parse origin/<branch>`, before reading the tree.

That is four operations with one detector in one night — measurement, commit,
edit and fetch — and the fourth is the case for it being a habit rather than a
set of guards: nobody would have written a guard for "the fetch did not finish".

A FIFTH, AND IT INVALIDATES A CATEGORY OF CLAIM: ON THIS MACHINE A LANDING'S
EXIT STATUS IS NOT EVIDENCE THE LANDING HAPPENED. Twice in one night in anat,
from different causes with the same symptom. First the harness backgrounded the
command and reported 0. Then `make land` died with `Terminated: 15`, pushed
nothing and left staging unchanged, and the background-task notification said
"completed (exit code 0)". SIGTERM is not an exception, so land.py's in-process
recovery for a red batch could not fire, because nothing was raised. A killed
landing and a real one look identical from the notification. So every "landed"
report rests on the notification unless someone read back the CONTENT: the
commits present on origin after a fetch, origin's sha equal to the intended tip,
and the lane lock released. That read-back found three commits stranded under a
leftover batch merge and staging unchanged, which would otherwise have been
reported as shipped.

AND ITS COROLLARY FOR THE READER: ESTABLISH WHAT FAILED BEFORE READING THE CODE
THAT HANDLES FAILURES. In the same incident a peer's remembered instruction
("re-run with --batch none") was checked by reading land.py, which already does
exactly that. The reading was CORRECT about the script and IRRELEVANT to the
situation, because the run was not dying of a red batch; it was being killed. A
correct reading of an irrelevant mechanism is worse than no reading, because it
produces confidence. It is the neighbouring-property class one level up: not
evidence that measures the wrong quantity, but a reader examining the wrong
mechanism. The discriminator is cheap: the exit signal, the last line of the
log, or whether the handler's exception was ever raised.

EACH IS ONE EXTRA OBSERVATION, TAKEN FROM THE ARTEFACT RATHER THAN THE PROCESS:
the report's own `judged`, the new sha, the second file's content. The
alternative is three guards — for stale reports, for shell quoting, for regex
anchoring — three maintenance burdens against one habit that covers all three
and generalises to steps nobody has thought of yet.

STATED SO IT DOES NOT COLLAPSE INTO "CHECK YOUR WORK": the assertion is on a
SPECIFIC VALUE THAT THE STEP'S SEMANTICS REQUIRE TO DIFFER, CHOSEN BEFORE THE
STEP RUNS. "The sha is new." "The judged count differs from the last run's."
"Both files' mtimes moved." What it is NOT is re-running the command, re-reading
the log, or asking whether it errored — all three cases above had a clean-looking
process and a wrong artefact.

ITS LIMIT, honestly: it works only where the required change is NAMEABLE IN
ADVANCE. A step whose effect is "some subset of these fourteen files may change"
has no single value to read back, and there the answer is the older one — open
one changed line and READ it, never count matches.

AND IT PAIRS WITH THE CORPUS DEFENCES rather than duplicating them: those defend
a POPULATION from silently changing size, this defends an ACTION from silently
not happening. Same underlying thing — a verdict that does not depend on the
thing it claims to measure — caught at the read side and the write side.

A REFUSAL TO VERIFY IS DATA, AND IT MAY NOT BE OVERRIDDEN WITH A DIFFERENT KIND
OF EVIDENCE. The same day this module was written, a browser pass reported one
row UNVERIFIED — it could not find an unfiltered-empty list to compare — and
that refusal was then settled from SOURCE evidence, which showed the helper was
correct. The helper was correct. Fourteen lists rendered their empty row by hand
and never called it, and two sessions got the row wrong the same morning,
independently, by the same move. SOURCE EVIDENCE CAN SHOW A MECHANISM IS RIGHT;
IT CANNOT SHOW WHAT REACHES THE PERSON. When a browser result and a source
result disagree about what someone SEES, the browser wins — and when the browser
says "I could not verify this", that is not an invitation to settle it from
source. The weaker observation was the honest one. This is the INVALID rule
below, one level out: a verdict that could not be reached is not a verdict, and
substituting a different question's answer for it is exactly how "no failures"
becomes "success".

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


def decides_about(root: Path, ignore: str = "") -> dict:
    """WHICH TREE this verdict is about. A DECISION FILE HAS A FOURTH STATE
    NOBODY DESIGNS FOR: a previous run's verdict, readable before the next run
    clears it. Pass / fail / did-not-run are the three anybody plans; the fourth
    is a verdict that is perfectly well-formed and about a different commit.
    Stamping the sha it decides about is what tells them apart — without it a
    reader cannot distinguish "this run passed" from "some earlier run passed".
    """
    out = {"sha": "", "dirty": None}
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=20)
        if head.returncode == 0:
            out["sha"] = head.stdout.strip()
            st = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, timeout=30)
            if st.returncode == 0:
                # The run's own artefacts do not make the tree it judged
                # unrecoverable — everything else does.
                lines = [l for l in st.stdout.splitlines()
                         if l.strip() and not (ignore and ignore in l)]
                out["dirty"] = bool(lines)
    except (OSError, subprocess.SubprocessError):
        pass
    return out


def stale(record: dict, root: Path) -> str:
    """"" when this artefact is about the tree in front of you; otherwise why not."""
    was = (record or {}).get("decides_about") or {}
    now = decides_about(root, ignore=str(was.get("ignored") or ""))
    if not was.get("sha") or not now.get("sha"):
        return "this artefact does not say which commit it decided about — it cannot be told from an earlier run's"
    if was["sha"] != now["sha"]:
        return (f"this artefact decided about {was['sha'][:12]}, and the tree is at {now['sha'][:12]} — a "
                "previous run's verdict, readable and well-formed and about different code")
    if was.get("dirty") or now.get("dirty"):
        return (f"this artefact decided about {was['sha'][:12]} with uncommitted changes present — the tree it "
                "judged is not recoverable, so the verdict is about a state nobody can return to")
    return ""


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
FAILED_DEFAULT = r"^FAILED |^ERROR |\b[1-9]\d* (?:failed|errors?)\b"
#: What counts as EXECUTED in a default-marker summary. Skipped and deselected
#: mark that the run reached the end and are not execution: "0 passed, 3 skipped"
#: finished and ran nothing. Found by an independent review — the first version
#: read the executed count out of DONE's capture group, which captured the
#: STATUS WORD rather than the digit, so under the kit's own default markers the
#: "executed NOTHING" check could never fire and an empty run read as PASS.
#: And a clean summary printing "0 failed" read as FAIL, since the failure
#: pattern accepted a zero: `[1-9]` above is that fix.
EXECUTED = r"\b(\d+)\s+(?:passed|failed|errors?|xfailed|xpassed)\b"


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
    if spec.get("completed"):
        # A declared marker: its own capture groups carry the count.
        counts = [int(g) for m in hits for g in m.groups() if g and g.isdigit()]
        executed_nothing = bool(counts) and not any(counts)
    else:
        # The default markers: count only EXECUTED categories. A bare "[100%]"
        # proves the run finished and says nothing about how many ran, so an
        # empty count is only a finding when a summary line or "no tests ran"
        # actually says so.
        counts = [int(m.group(1)) for m in re.finditer(EXECUTED, output, re.M)]
        executed_nothing = (re.search(r"no tests ran", output) is not None
                            or (bool(re.search(r"\b\d+\s+(?:passed|failed|errors?|skipped|deselected|xfailed|xpassed)\b",
                                               output)) and sum(counts) == 0))
    failures = list(re.finditer(failed, output, re.M))

    if not hits:
        return INVALID, (f"nothing in the output matches the completion marker {completed!r} — THE RUN DID NOT "
                         f"FINISH, whatever it exited ({exit_code}). It also printed "
                         f"{'no' if not failures else str(len(failures))} failure line(s), so anything grepping "
                         "for failures would call this green")
    if executed_nothing:
        return INVALID, ("the run reached the end and EXECUTED NOTHING — an empty run is not a clean one, and a "
                         "run whose every test was skipped or deselected is empty")
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


#: TESTING IS THE LOAD THAT BREAKS THE THING BEING TESTED (ana-log, 2026-09-21). The estate's Mac reached
#: load 75, then 105, on fourteen cores: the Actions runner VM plus several sessions' full suites, two
#: launched a minute apart, each running unit and e2e in parallel. On ana that produced three red CI runs
#: of HTTP timeouts, a CI Postgres dropped into recovery mid-run, and a 2 h 30 m queue that tripped
#: Railway's 2 h limit. "A different test fails each run and each passes alone" is the signature of
#: order-dependence AND of a saturated machine; a fix that coincides with a quiet machine is
#: indistinguishable from a fix that worked. So every run records the load it was measured under, and a
#: run above LOADED x cores says so in its verdict line.
LOADED = 1.5


def top_consumers(n: int = 6, *, ps=None) -> list[str]:
    """The top CPU consumers by RANK, never by name.

    A check that filters for `pytest|land.py|make` can only find the tools somebody thought of: on
    2026-09-21 a slot was released as "machine free" while a CI job's headless Chromium ran at 98 % (its
    processes are `node` and `chrome-headless-shell`) and Spotlight's mdworker indexed five sessions' trees
    at 140 % of a core — neither matched any name. Enumerate and rank; the owner is usually legible from
    the path."""
    try:
        out = ps() if ps else subprocess.run(["ps", "-Ao", "pcpu,etime,command"], capture_output=True,
                                             text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    rows = []
    for line in out.splitlines()[1:]:
        parts = line.split(None, 2)
        try:
            rows.append((float(parts[0]), line.strip()[:160]))
        except (ValueError, IndexError):
            continue
    return [r for _, r in sorted(rows, key=lambda x: -x[0])[:n]]


def _load(getloadavg=os.getloadavg) -> float | None:
    try:
        return round(getloadavg()[0], 1)
    except (OSError, AttributeError):
        return None


class HeavyLock:
    """One heavy suite per machine, as a LOCK rather than a courtesy. "Be considerate" is not a scheduler:
    each session reasoned correctly from what it could see, and none could see the others. `--heavy` takes
    an exclusive lock at ~/.qabench/heavy.lock (QABENCH_HEAVY_LOCK), waits for it, and says who held it."""

    def __init__(self, name: str, echo=print, path: str | None = None):
        self.path = Path(path or os.environ.get("QABENCH_HEAVY_LOCK") or Path.home() / ".qabench" / "heavy.lock")
        self.name, self.echo, self.fh, self.waited = name, echo, None, 0.0

    def __enter__(self):
        import fcntl
        import time
        # RE-ENTRANT ACROSS THE PROCESS TREE. A heavy run whose command itself calls `ran --heavy` (a land.py
        # check wrapping `./dev test unit`, which one day wraps another) would block forever on a lock its own
        # ancestor holds — the one way a kernel lock deadlocks a single job (ana-qa). The holder exports
        # QABENCH_HEAVY_HELD with the lock's path; a descendant that sees it proceeds and says so.
        if os.environ.get("QABENCH_HEAVY_HELD") == str(self.path):
            self.echo("ran: heavy-run lock already held by this run's own ancestor — proceeding inside it")
            self.fh, self.nested = None, True
            return self
        self.nested = False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(self.path, "a+")
        t0 = time.monotonic()
        try:
            fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.fh.seek(0)
            holder = self.fh.read().strip() or "another heavy run"
            self.echo(f"ran: waiting for the machine's heavy-run lock, held by: {holder}")
            fcntl.flock(self.fh, fcntl.LOCK_EX)
        self.waited = round(time.monotonic() - t0, 1)
        self.fh.seek(0)
        self.fh.truncate()
        # WHO, not only what: git and ps record no owner, so sessions inferred one from a worktree NAME and
        # were wrong twice on 2026-09-21. The session name comes from the landing conventions already in use.
        who = next((os.environ[k] for k in ("QABENCH_SESSION", "LAND_SESSION", "ANAT_SESSION") if os.environ.get(k)),
                   "an unnamed session")
        self.fh.write(f"{self.name} for {who}, pid {os.getpid()} in {os.getcwd()} since "
                      f"{dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}")
        self.fh.flush()
        self._prev = os.environ.get("QABENCH_HEAVY_HELD")
        os.environ["QABENCH_HEAVY_HELD"] = str(self.path)      # inherited by the command this lock wraps
        return self

    def __exit__(self, *exc):
        import fcntl
        if self.nested:
            return False
        if self._prev is None:
            os.environ.pop("QABENCH_HEAVY_HELD", None)
        else:
            os.environ["QABENCH_HEAVY_HELD"] = self._prev
        try:
            self.fh.seek(0)
            self.fh.truncate()
            fcntl.flock(self.fh, fcntl.LOCK_UN)
        finally:
            self.fh.close()
        return False


def run_one(root: Path, cfg: dict, name: str, argv: list[str], *, now=None, echo=print,
            getloadavg=os.getloadavg) -> dict:
    """Preflight, run, judge, and write the artefact. The artefact IS the result."""
    now = now or dt.datetime.now(dt.timezone.utc)
    load_start = _load(getloadavg)
    declared = cfg.get("record") or {}
    spec = (cfg.get("commands") or {}).get(name) or {}
    art_dir = root / (cfg.get("artefacts") or "qa/runs")
    host = snapshot(declared)
    log = art_dir / f"{name}.log"
    code = execute(argv, log, cwd=root, echo=echo)
    load_end = _load(getloadavg)
    v, why = verdict(code, log.read_text(encoding="utf-8", errors="replace"), spec)
    cores = os.cpu_count() or 1
    peak = max([x for x in (load_start, load_end) if x is not None], default=None)
    under_load = peak is not None and peak / cores > LOADED
    if under_load:
        why += (f" — measured UNDER LOAD (load {peak} on {cores} cores): a failure here is not yet evidence about "
                "the code, and a later green is not evidence of a fix, until it is re-run on a quiet machine")
    record = {
        "name": name, "argv": argv, "started": now.isoformat(), "cwd": str(root),
        "host": host.__dict__, "host_busy": host.busy(declared),
        # The weaker claim, stated out loud rather than quietly widened: a
        # command the manifest does not describe is judged on the kit's
        # pytest-shaped defaults, which are right for a pytest run and a guess
        # for anything else.
        "declared": bool(spec), "verdict": v, "why": why, "exit_code": code,
        "decides_about": {**decides_about(root, ignore=str(art_dir.relative_to(root))),
                          "ignored": str(art_dir.relative_to(root))},
        # Named in the artefact as well as in the sentence: the next session
        # reads the JSON, and a gate nobody attempted is exactly what a green
        # local run otherwise fails to mention.
        "not_attempted": [g.get("name") for g in (spec.get("gates") or [])
                          if not re.search(g.get("evidence") or r"(?!x)x",
                                           log.read_text(encoding="utf-8", errors="replace"), re.M)],
        "log": str(log.relative_to(root)), "finished": dt.datetime.now(dt.timezone.utc).isoformat(),
        "load": {"start": load_start, "end": load_end, "cores": cores, "under_load": under_load,
                 "top": top_consumers() if under_load else []},
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
        print("usage: python -m qabench ran --name NAME [--heavy] -- COMMAND [ARGS...]\n"
              "  --heavy  take the machine-wide heavy-run lock (~/.qabench/heavy.lock), naming its holder while "
              "waiting; re-entrant for the command it wraps\n"
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
    if "--heavy" in opts:
        with HeavyLock(name, echo=echo) as lock:
            record = run_one(root, cfg, name, cmd, echo=echo)
            record["heavy_lock_waited_s"] = lock.waited
    else:
        record = run_one(root, cfg, name, cmd, echo=echo)
    if "--json" in opts:
        print(json.dumps(record, indent=1, ensure_ascii=False))
    else:
        print(f"\n{record['verdict']}  {name}: {record['why']}")
        print(f"       artefact {record['artefact']}" + (f" · log {record['log']}" if record["log"] else ""))
    return EXIT[record["verdict"]]
