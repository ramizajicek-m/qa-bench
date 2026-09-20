"""population — a guard's SUBJECT is the property's population, not the example's neighbourhood.

    python -m qabench population                 # the `population:` block of qa/manifest.yml
    python -m qabench population --json          # the rows, for a test to read
    python -m qabench population --repo DIR      # another checkout

WHY. On 2026-09-20 twelve defects were found behind green tests in anat and
ana-log. Eight are one shape, and it is not a missing insight — `contract.yml`
already requires every piece of evidence to "print the SIZE of the population
it examined". The size was printed. Nothing ever compared it to a population
derived INDEPENDENTLY of the guard, so a guard could sweep the neighbourhood of
the example it was written against and report that neighbourhood's size as
though it were the whole:

  ACT-11  the corpus of "routes that report a count" was keyed on the PATH
          containing "batch" or "bulk". Re-keyed on the AST property — a route
          that iterates a collection and returns a dict containing len()/sum()
          — it found 11 more routes and a second live defect.
  MSG-03  a ratchet on raw HTTP status codes in user-facing errors counted
          admin templates and api.js. The technician field app has its own
          fetch wrapper; the ratchet read zero on it and technicians on roofs
          read "Not saved: Not Found".
  FRM-01  the required-signature mark is styled by style.css. The markup sweep
          credited the rule to every template alike, including three standalone
          documents that never load it.
  FRM-04  a switch over eleven pydantic error types was tested against the
          eleven cases in the switch. Twelve more are reachable.
  FRM-10  a detector using `\\bcan_\\b` can never match `can_edit_field` — there
          is no word boundary between word characters. It reported ZERO gated
          fields, which reads exactly like a clean tree. The real number was
          ten, one of them a live defect.
  and the harness class: a guard that watched ONE global name (AnatList) while
          seven harnesses failed on another (AnatDate).

So every guard names two commands. `population` enumerates what the property
claims to hold over; `subject` prints what the guard actually examined. This
module runs both and compares them by MEMBER. A member of the population the
guard never examined is a hole with a name, not a percentage.

FOUR RULES, each paid for by one of the rows above:

  1. A POPULATION IS DERIVED, NEVER NAMED. `derived_from` is one of ast,
     route_table, schema, enumeration, filesystem — the ways to ask what a
     thing IS. `names`, `grep` and their kin are refused, because a naming
     heuristic is the defect (ACT-11, MSG-03). This is the meta-rule that
     stops a widened corpus being narrowed back later.
  2. ZERO IS RED. A subject of nothing against a population of something is a
     finding, never a pass: a detector matching nothing is indistinguishable
     from a clean tree (FRM-10).
  3. THE GAP IS NAMED MEMBER BY MEMBER, so "credited to every template alike"
     is impossible to write (FRM-01).
  4. THE POPULATION COUNT IS PINNED AND THE PIN IS EXACT. It may rise in the
     commit that raises it; it may fall only behind `shrunk:` with a reason,
     evidence and a date. A corpus that quietly returns to a naming heuristic
     fails here.

A MEMBER MAY BE A PAIR, and that is how the catalogue cases are written. ACT-05
swept 146 dialogs and made every save answer 500 — one arm of the client. A
dropped connection resolves through the `catch` with status 0 and never throws,
so a handler written against an exception falls into its success branch and no
number of 500s can see it. Emit `dialog::500` and `dialog::offline` and the two
modes are two members: a mode that reached nothing is then a gap with a name
instead of a count one mode covered for. An injection harness enumerates its
modes by asking what the CLIENT does differently, never by picking a plausible
error — for a fetch client that is three arms, an error status (the response
path), a transport failure (the catch around fetch), and a SUCCESS carrying an
unexpected body, which takes no error path at all and throws inside the
renderer after the region has been cleared. The third is the one everybody
forgets and the only one that produces STA-07's literal subject, a blank white
screen; a sweep that sends 500 and only 500 cannot reach it. ACT-10 is the same
shape in a PAIRING — a button's verb against its success sentence — where the
guard checked one end: 20 of 183 messages resolved to a control, and the other
163 were nobody's.

The sharpest case of all is a differential whose corpus is the INTERSECTION of
the two things it compares: the field app's 16 HTTP reason phrases against
api.js's 39, under a comment claiming parity, tested on 404/422/403/500 — four
phrases in both lists. It could not see the difference it existed to measure.
The population there is the union; the subject was the intersection, and this
module prints the twenty-three names in the first and not the second.

REFUSE, DO NOT ATTRIBUTE — the failure in the other direction, and it now has a
number. A resolver that guessed each toast's button from the nearest enclosing
named function produced three confident phantoms in one hour, and a phantom
costs more than a miss: it costs somebody the time to disbelieve the guard, and
then the real findings it makes afterwards. Measured on a second corpus the same
day: of 8 cross-references in a tracker's reasons, a strict extractor RESOLVED 3
and REFUSED 5 — and both real defects were inside the 3. Refusing five of eight
cost zero findings, while the loose pass over the same corpus produced two
phantoms that had to be withdrawn by hand. Fewer claims examined, same defects
found, none invented; the objection that a confident-only parser under-detects
did not survive contact with the data. A subject command therefore prints only the members the guard
PROVED it judged. Everything it could not resolve it leaves out, where this
module names it as a gap — which is the honest denominator, and removes the
reason to guess: a guard can no longer buy coverage with an attribution.

THE POPULATION IS NOT ALWAYS CODE. An aggregate requirement — "no action fails
while the screen looks as though it succeeded" — is satisfied when its PARTS
are, and a parts list is a denominator like any other. GEN-03's was written by
example and did not name ACT-11, which is the row the silent failure of the day
actually was, so the aggregate could have gone green with the principle's own
defect live. Any tracker that decomposes principles into rows has this shape.
The population there is `requirement_text` and the exclusions are `exemptions`:
each one read rather than filled in, because SEC-04 deliberately says less (a
login error must not reveal whether the account exists) and that is a different
question, not a gap. A sweep whose exclusion list was filled in quickly to get
green would be the defect wearing the fix's clothes.

A CLOSED DENOMINATOR IS ACHIEVABLE AT SCALE, and the obvious objection — that
this only works on small corpora — has a counterexample in the tree. anat's
MSG-04 guard does not report its unjudged share, it drives it to zero:
`test_no_sentence_is_hidden_from_the_sweep` asserts that NO person-facing error
detail is dynamic, so a sentence the AST walk cannot read is a failure rather
than a quiet gap in the denominator. Page literals judged, the page helper
executed under node with every branch judged by the same rule, pass-throughs
traced to the server or to apiFetch, 1,399 server sentences judged, nothing
left over. That is the reference implementation, and the ambition this module
reports against: a guard states its denominator and drives the unjudged share
to zero, or names what is in it.

WHAT IT CANNOT SEE, stated: that the guard's ORACLE is right. A guard may sweep
the whole population and still assert the wrong thing about each member — FRM-04
swept its eleven types and asked the implementation what the answer was, FRM-05
drove one field where every ordering agrees. Population is the denominator;
discrimination is a separate question and this module does not answer it.

Exit: 0 every guard sweeps its population · 1 a gap, a vacuous subject, a bad
pin or a bad exemption · 3 no register, or a population command that could not
run (never reported as 0).

Manifest shape:

    population:
      register: qa/guards.yml

And the register:

    version: 1
    guards:
      - id: act11-count-reporting-routes
        check: C6
        claims: "a route that iterates a collection and reports a count reports its failures too"
        population:
          derived_from: ast
          cmd: "python3 scripts/qa/pop_count_routes.py"
          count: 11                      # exact; raise it in the commit that raises it
        subject:
          cmd: "python3 scripts/guards/act11.py --subjects"
        exemptions:
          - member: "app/api/legacy.py::export_csv"
            reason: "deleted in the 2026-10 cutover; no caller since 09-02"
            evidence: docs/checker-calibration-ledger.md
            review_by: 2026-10-15
"""
from __future__ import annotations

import datetime as dt
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import warrant

#: How a population may be derived: by asking what a thing IS. Every one of
#: these reads a structure — a parse tree, the app's own route table, the
#: schema, an explicit enumeration, the filesystem, or the REQUIREMENT PROSE
#: the project already maintains. What is NOT here is the whole point: a
#: population chosen by what things are CALLED is the defect this module exists
#: for, so `names`, `grep`, `regex` and `convention` are refused by name rather
#: than by omission, with the reason printed.
#:
#: `requirement_text` is a text sweep and is admitted anyway, which looks like
#: an exception and is not. The refusal is on deriving a population from what
#: the CODE happens to be called; the spec is the other side of the question,
#: and a population read out of prose the project maintains GROWS BY ITSELF
#: when a row is added — which a hand-written tuple cannot. GEN-03 is why it is
#: here: "no action fails while the screen looks as though it succeeded" was an
#: aggregate row whose parts were listed by hand, and ACT-11 — a bulk action
#: that answered {"updated": 50} having written none — was not on the list. The
#: aggregate could have gone green with the principle's own defect live, and
#: its guard would have agreed, not by being wrong but because the row was not
#: one of the things it was looking at. Swept from the requirement text instead
#: ("every row whose wording talks about failing, erroring or succeeding is a
#: part of GEN-03 or is answered with the reason it is a different question"),
#: it names ACT-11 and FRM-13 by id.
DERIVATIONS = ("ast", "route_table", "schema", "enumeration", "filesystem", "requirement_text")
REFUSED = {
    "names": "ACT-11: the corpus was routes whose PATH contained batch|bulk; the property was routes that iterate a collection",
    "naming": "a naming heuristic is the defect, not a derivation",
    "grep": "a regex also matches the docstring that explains the rename — derive by structure",
    "regex": "FRM-10: `\\bcan_\\b` cannot match can_edit_field, and matched nothing, and read as clean",
    "convention": "a convention is what the example happened to follow",
}
EXEMPTION_KEYS = ("member", "reason", "evidence", "review_by")
SHRUNK_KEYS = ("reason", "evidence", "date")


@dataclass
class Set_:
    """One side of a guard: the members a command printed, or why it could not."""
    members: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class Row:
    id: str
    check: str
    claims: str
    population: int = 0
    subject: int = 0
    missing: list[str] = field(default_factory=list)      # in the population, never examined
    stray: list[str] = field(default_factory=list)        # examined, outside the declared population
    exempted: int = 0
    problems: list[str] = field(default_factory=list)     # why the row is red
    unrunnable: bool = False                              # a command exited non-zero: did not run


def read_members(root: Path, cmd: str, *, timeout: float = 120.0) -> Set_:
    """Run `cmd` in `root` and take one member per non-empty, non-comment line.

    No shell. A register is a tracked file in the project's own repo, at the
    same trust as its Makefile — but a shell also turns a member containing a
    space into two, which is a silent narrowing of exactly the kind measured
    here, so the argv is split once and passed through.
    """
    try:
        p = subprocess.run(shlex.split(cmd), cwd=root, capture_output=True, text=True, timeout=timeout)
    except (OSError, ValueError, subprocess.SubprocessError) as ex:
        return Set_(error=f"{cmd!r} could not run: {ex}")
    if p.returncode != 0:
        tail = (p.stderr or p.stdout or "").strip().splitlines()[-1:] or [""]
        return Set_(error=f"{cmd!r} exited {p.returncode}: {tail[0][:200]}")
    members = [l.strip() for l in p.stdout.splitlines()]
    return Set_(members=sorted({m for m in members if m and not m.startswith("#")}))


def judge_exemption(ex, root: Path, today: dt.date) -> str:
    """"" when the exemption stands; otherwise why it does not.

    One contract, in `qabench.warrant`: four files had written it out four
    times, and a contract with four copies is four contracts."""
    return warrant.judge(ex, root, today, subject="member", label="exemption")


def judge_pin(pinned, actual: int, shrunk, root: Path) -> str:
    """The ratchet. Exact, because only an exact pin can catch a narrowing."""
    if not isinstance(pinned, int):
        return (f"population.count is {pinned!r}, not a number — the population is {actual}; "
                "pin it, or a corpus can be narrowed back to a naming heuristic with nothing red")
    if actual == pinned:
        return ""
    if actual > pinned:
        return (f"the population grew {pinned} → {actual}; raise population.count in the same commit "
                "(a pin that lags cannot detect the fall back)")
    if not isinstance(shrunk, dict):
        return (f"the population FELL {pinned} → {actual} with no `shrunk:` — this is what re-keying a "
                "corpus on a naming heuristic looks like from the outside")
    lacking = [k for k in SHRUNK_KEYS if not shrunk.get(k)]
    if lacking:
        return f"the population fell {pinned} → {actual}; `shrunk:` lacks {', '.join(lacking)}"
    ev = shrunk["evidence"] if isinstance(shrunk["evidence"], list) else [shrunk["evidence"]]
    absent = [e for e in ev if not (root / str(e).split("::")[0]).exists()]
    if absent:
        return f"the population fell {pinned} → {actual}; `shrunk.evidence` does not exist: {', '.join(absent)}"
    return f"the population fell {pinned} → {actual} and `shrunk:` explains it — set population.count to {actual}"


def judge(spec: dict, root: Path, today: dt.date, *, run=read_members) -> Row:
    """One guard: run both sides, compare by member, apply the four rules."""
    row = Row(id=str(spec.get("id") or "?"), check=str(spec.get("check") or ""), claims=str(spec.get("claims") or ""))
    if not spec.get("id"):
        row.problems.append("a guard with no `id:` — a finding nobody can look up")
    if not row.check:
        row.problems.append("no `check:` — every guard serves one of C1–C12, or it is runtime with no owner")
    if not row.claims:
        row.problems.append("no `claims:` — the one sentence the population is the population OF")

    pop_spec = spec.get("population") or {}
    sub_spec = spec.get("subject") or {}
    derived = str(pop_spec.get("derived_from") or "")
    if derived in REFUSED:
        row.problems.append(f"population.derived_from: {derived!r} is refused — {REFUSED[derived]}")
    elif derived not in DERIVATIONS:
        row.problems.append(f"population.derived_from must be one of {', '.join(DERIVATIONS)}, not {derived!r}")
    if not pop_spec.get("cmd") or not sub_spec.get("cmd"):
        row.problems.append("a guard names both a population.cmd and a subject.cmd, or it is a claim about itself")
        return row

    pop, sub = run(root, pop_spec["cmd"]), run(root, sub_spec["cmd"])
    if pop.error or sub.error:
        row.unrunnable = True
        row.problems.append(pop.error or sub.error)
        return row

    row.population, row.subject = len(pop.members), len(sub.members)
    exemptions = spec.get("exemptions") or []
    for ex in exemptions:
        problem = judge_exemption(ex, root, today)
        if problem:
            row.problems.append(problem)
    excused = {str(e.get("member")) for e in exemptions if isinstance(e, dict) and not judge_exemption(e, root, today)}

    if not pop.members:
        row.unrunnable = True
        row.problems.append(f"{pop_spec['cmd']!r} enumerated NOTHING — a population of nothing cannot show that "
                            "anything was swept; exclude the guard by declaration or fix the enumeration")
        return row

    missing = [m for m in pop.members if m not in set(sub.members)]
    row.exempted = len([m for m in missing if m in excused])
    row.missing = [m for m in missing if m not in excused]
    row.stray = [m for m in sub.members if m not in set(pop.members)]
    stale = sorted(excused - set(missing))

    if not sub.members:
        row.problems.append(f"the guard examined NOTHING against a population of {row.population} — a detector "
                            "matching nothing is indistinguishable from a clean tree (FRM-10)")
    if row.missing:
        shown = ", ".join(row.missing[:8]) + (f" … +{len(row.missing) - 8}" if len(row.missing) > 8 else "")
        row.problems.append(f"{len(row.missing)} of {row.population} never examined: {shown}")
    if row.stray:
        shown = ", ".join(row.stray[:8]) + (f" … +{len(row.stray) - 8}" if len(row.stray) > 8 else "")
        row.problems.append(f"{len(row.stray)} examined but outside the declared population — the population "
                            f"expression is narrower than the guard: {shown}")
    for m in stale:
        row.problems.append(f"exemption {m!r} is stale: the guard now examines it — delete the entry")
    pin = judge_pin(pop_spec.get("count"), row.population, pop_spec.get("shrunk"), root)
    if pin:
        row.problems.append(pin)
    return row


def run_population(root: Path, cfg: dict, *, today: dt.date | None = None, run=read_members) -> dict:
    today = today or dt.date.today()
    reg_path = root / cfg["register"]
    doc = yaml.safe_load(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else None
    guards = (doc or {}).get("guards") or []
    rows = [judge(g, root, today, run=run) for g in guards]

    # The completeness half. A check the manifest calls `implemented` with no
    # registered guard is the state every row above was found in: evidence that
    # exists, and no statement of what it claims to cover.
    mpath = root / "qa" / "manifest.yml"
    manifest = (yaml.safe_load(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}) or {}
    implemented = sorted(cid for cid, spec in (manifest.get("checks") or {}).items()
                         if isinstance(spec, dict) and spec.get("status") == "implemented")
    covered = {r.check for r in rows}
    return {
        "register": str(reg_path),
        "guards": len(rows),
        "rows": [r.__dict__ for r in rows],
        "red": [r.__dict__ for r in rows if r.problems],
        "unrunnable": [r.__dict__ for r in rows if r.unrunnable],
        "unregistered": [c for c in implemented if c not in covered],
    }


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def run(argv: list[str], *, today: dt.date | None = None) -> int:
    root = Path(_arg(argv, "--repo", ".")).resolve()
    mpath = root / "qa" / "manifest.yml"
    doc = yaml.safe_load(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    cfg = (doc or {}).get("population")
    if not cfg or not cfg.get("register"):
        print(f"no `population:` block with a `register:` in {mpath} — no guard states the population it "
              "claims over (exit 3)", file=sys.stderr)
        return 3
    if not (root / cfg["register"]).exists():
        print(f"{cfg['register']} does not exist — nothing measured (exit 3)", file=sys.stderr)
        return 3
    out = run_population(root, cfg, today=today, run=read_members)
    if "--json" in argv:
        print(json.dumps(out, indent=1, ensure_ascii=False))
    else:
        print(f"POPULATION — {out['guards']} guards in {out['register']}")
        for r in out["rows"]:
            mark = "RED " if r["problems"] else "ok  "
            print(f"  {mark}{r['id']:38} {r['check']:4} {r['subject']:>5}/{r['population']:<5} swept"
                  + (f"   ({r['exempted']} exempted)" if r["exempted"] else ""))
            for p in r["problems"]:
                print(f"       {p}")
        for c in out["unregistered"]:
            print(f"  RED  {c} is `implemented` in the manifest and no guard says what population it covers")
    if not out["guards"]:
        print("the register names no guards — treat as did not run (exit 3)", file=sys.stderr)
        return 3
    if out["unrunnable"]:
        print(f"{len(out['unrunnable'])} guard(s) could not run — did not run, not clean (exit 3)", file=sys.stderr)
        return 3
    return 1 if (out["red"] or out["unregistered"]) else 0
