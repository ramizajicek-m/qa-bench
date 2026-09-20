r"""population — a guard's SUBJECT is the property's population, not the example's neighbourhood.

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
  STA-02  "an empty screen explains why it is empty and offers the next
          action", swept over `class="empty-state"` plus every AnatEmpty call —
          and the class is what the CONVERSION added. A ratchet drove 75
          hand-rolled empty states to 38 to 0 by moving them onto the helper,
          each conversion adding the class, so the population is exactly THE SET
          OF THINGS ALREADY FIXED. The screen the coordinator found renders
          `<td colspan="7" style="text-align:center">` through the LIST helper,
          which has no action parameter at all, and was never in the ratchet to
          survive it. 75 → 38 → 0 is true and counts the conversion, not the
          surface.
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
     from a clean tree (FRM-10). And its converse, which a live corpus of one
     forced into the open: a guard whose POPULATION may legitimately be empty
     declares a `capability:` command — a self-test on a permanent synthetic
     corpus, proving the detector still detects — and then an empty live scan
     is REPORTED rather than judged. Capability and corpus are two claims, and
     the only honest way to let a live scan find nothing is to prove the
     detector elsewhere. The capability runs on every invocation, not only when
     the corpus is empty, because a detector that quietly stopped detecting
     over a NON-empty corpus is FRM-10 itself.
  3. THE GAP IS NAMED MEMBER BY MEMBER, so "credited to every template alike"
     is impossible to write (FRM-01).
  4. A RATCHET'S FALL PROVES NOTHING ABOUT A POPULATION THE RATCHET DEFINES.
     When the marker a population is keyed on is the one each fix adds, the
     count falls to zero by construction and says nothing about what was never
     in it. The question is always what CAN exhibit the property, never what
     carries the sign of having been handled.
  5. THE POPULATION COUNT IS PINNED AND THE PIN IS EXACT. It may rise in the
     commit that raises it; it may fall only behind `shrunk:` with a reason,
     evidence and a date. A corpus that quietly returns to a naming heuristic
     fails here.

A TRANSFORM IS PART OF THE GUARD, AND A DESTROYED CORPUS REPORTS EXACTLY LIKE A
CLEAN ONE. A guard tripping on the COMMENT that explained a fix was made to
strip comments first — `<!--.*?-->|/\*.*?\*/|^[ \t]*//.*$` with DOTALL — and a
stray `/*` inside a script string found a distant partner, blanking 58 % of one
real file, 73 % of another and 76 % of a third. Two checks had ALREADY been
watched going green over that gutted corpus and recorded as mutations passed.
This is the false-green shape arriving from the direction nobody watches: not
the check, not the oracle, but the NORMALISATION STEP in between, which nobody
thinks of as part of the verdict. Anything that transforms a corpus before the
assertion owes the same proof as the assertion — declare `transform:` with the
size before and after and the shrink you INTENDED, and an unintended shrink is
red. One line, and it would have caught this instantly.

AND THE SELECTION EFFECT UNDERNEATH IT, which is the part worth carrying to
every project: real source has prose in it, and THE PROSE CLUSTERS EXACTLY WHERE
THE DEFECTS WERE, because that is where people stop to explain themselves. So a
text-matching guard is systematically MOST likely to be wrong at the very sites
it was written for. That is not bad luck, it is selection — prose density
correlates with defect history. Two failures in one file in one hour came from
it: the guard above, and a click-handler detector matching
`addEventListener('click', … [^{}]{0,200} … AnatDialog.close(` whose window was
pushed past 200 characters by the three-line comment explaining the fix, so
restoring the defect left the test GREEN and only the mutation found it.

The rule all three collapse into: THE CORPUS A GUARD ASSERTS OVER MUST BE THE
CORPUS A BROWSER OR RUNTIME ACTS ON, transformed as little as possible, with
every transform proving it did not shrink what it touched. Anchor to structure —
a tag, an AST node — rather than cleaning text to make a pattern work. When a
pattern needs the text cleaned to be correct, the pattern is wrong.

REACH IS A DENOMINATOR, AND A DENOMINATOR NEEDS ITS OWN COVERAGE MEASUREMENT.
For every blessed helper, how many call sites go through it? Mechanical,
countable, and nobody was asking. On anat: AnatFlash.toast 987 against one stray
alert(, AnatDate 136 against zero, AnatDialog.open 159 against 8, close 133
against 12, AnatEmpty 50 against 38, and apiFetch 198 against 783 raw fetches —
20 %.

That 20 % would have started a rewrite, and it is wrong. BYPASSING A HELPER IS
NOT THE SAME AS BEING UNCOVERED: anat has three other global fetch wrappers
which between them give every raw call the loading indicator, session activity,
the CSRF header and the 401 bounce; 538 check status themselves; 297 report a
failure to a person; 109 do NEITHER. One hundred and nine is the actionable
number and it is a much smaller, correct piece of work.

So a guard may declare `kind: reach`, and then `complement:` is MANDATORY — the
layers that cover what bypasses the helper, applied in order, with the residue
named as the finding. A reach guard without it is refused the way a population
derived from naming is refused, because a denominator with no
coverage-by-other-means measurement is a verdict without a population, which is
this module's own subject arriving in its own instrument.

Two results from that table worth keeping. Four helpers at 100 % answer "20 % is
inevitable at this scale" — it is not, in the same codebase, at five times the
call volume. And AnatEmpty's 57 % was found COLD by the source audit, hours
after the same gap was found from a browser report on STA-02, with no knowledge
of the first: two independent routes to one finding is the closest thing to
validation this method gets, and it is worth more than any number in the table.

ONE REQUIREMENT MAY HAVE SEVERAL DETECTORS, and then the population is the
REQUIREMENT'S rather than any one detector's. STA-02 — "an empty screen explains
why it is empty and offers the next action" — was guarded by three tests: the
helper renders what/why/next-step (executed in isolation, correct, and proves
nothing about who calls it); every AnatEmpty call passes a `why` (corpus:
AnatEmpty calls); hand-rolled empty states only fall, ceiling zero (corpus:
markup carrying the empty-state class). A list dropping a sentence into a plain
table cell is NEITHER — sanctioned, so not hand-rolled; not AnatEmpty, so never
checked for why and action. Both detectors are individually sound and neither is
blind in a way you could see from its own output, because each population was a
proper subset of the claim and THE UNION OF THE TWO SUBSETS IS STILL A PROPER
SUBSET. So `subject.detectors` takes several commands, the union is compared to
the requirement's population, and a member no detector covers is named.

The detail that generalises beyond that repo: the hand-rolled detector's design
is "anything not going through the blessed helper is suspect", which is a good
design carrying an implicit assumption — that there is ONE blessed helper. The
moment a second sanctioned helper exists with a narrower contract, everything on
the second path is exempt from the first detector by construction and covered by
nothing. A guard defined as "not the approved way" silently grows a hole every
time somebody approves another way.

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
day, both ways, after two retractions: over 8 cross-references in a tracker's
reasons, a strict parser (the status word must attach to the id as its SUBJECT,
present tense) resolves 1 and refuses 7, finding the one genuine defect with no
phantoms; a loose parser (a status word within 45 characters of an id) resolves
all 8 and reports two defects, of which one is false. Seven attributions
declined, one extra "finding" bought by attributing, and that one wrong.
Precision 1.0 against 0.5.

Not oversold: the loose parser's other six attributions were correct passes. The
strict parser is not better because those six were dangerous — it is better
because the loose one cannot tell which of the eight it is competent to judge,
and the one it got wrong is the one that cost. The numbers travel with their
sentence: it found a genuine defect nothing else would have found, at zero
false-positive cost, AND IT CANNOT SEE SEVEN OF EIGHT CLAIMS. Precision known
and perfect; recall unknown and probably poor. A subject command therefore prints only the members the guard
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

THE CORPUS IS WHAT THE MECHANISM CAN SEE, NOT WHAT THE CLAIM COVERS. ACT-07
says "leaving a form with unsaved changes warns, with three choices". Its e2e is
a good test by every standard in this file: it asserts the labels EXACTLY —
["Keep editing", "Discard changes", "Save"] — then clicks each one and checks
its effect, which is not a presence check. What nothing asked is WHICH DIALOGS
REACH THE HELPER. 146 have an id; 133 delegate their close through it; 12 close
directly and were never in anybody's population. The helper is not failing, it
is not reached, and the e2e's fixture is a compliant dialog, so it can only ever
confirm compliance.

That is also the argument for driving a real browser rather than reading better.
The session that closed this row clean had read the code carefully the same
morning and stopped, because the helper WAS correct. Reading source tells you
what a mechanism does; it does not tell you what reaches the mechanism. A
reachability population is the static form of the browser's question, and it is
derivable — but nobody derives it until something asks.

THREE NUMBERS, NOT ONE, when a finding like this is reported: 12 of 146 broken,
7 of those harmful (the rest hold no real fields), and ZERO harm on the one the
browser demonstrated, because that dialog happens to persist every keystroke to
local storage and restore it. The browser picked the least harmful of the twelve.
Report the demonstrated instance, the broken population and the harmful subset,
or the row is prioritised off whichever number was nearest.

A LIVE CORPUS OF ONE IS THE HARD CASE, and it is where `capability:` comes
from. A cross-reference check over a 109-row tracker — does a row justify itself
by asserting another row's status, and is that status still true — found exactly
one real defect. Correct that defect and the scan resolves ZERO: its entire live
corpus is the thing it was written for. A guard whose only comparison disappears
the moment you fix what it found cannot fail afterwards, and an empty corpus
reads exactly like a clean table. The class was real and detectable; the corpus
was one. So the detector's capability is proven on synthetic prose that cannot
go away — a subject-attached stale citation must be caught, a past-tense mention
("the one thing that was missing is now supplied by the PRT-03 work") must not
be, a bare pointer ("the same reasoning as NAV-03") must not be — and the live
scan is then allowed to find nothing without that reading as a pass.

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
        capability:                        # required when the live corpus may be empty
          fires: "python3 scripts/guards/act11.py --selftest-positive"
          silent:                          # REAL near-misses the looser sibling fired on
            - cmd: "python3 scripts/guards/act11.py --selftest past-tense"
              from: qa/ui-standard.md
              was: "the one thing that was missing is now supplied by the PRT-03 work"
            - cmd: "python3 scripts/guards/act11.py --selftest bare-pointer"
              from: qa/ui-standard.md
              was: "the same reasoning as NAV-03, which this follows"
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
#: `reachability` is the sixth and it is not a set of files at all: it is
#: "everything whose path REACHES the guarded mechanism", and its complement is
#: the defect. ACT-07 is the cleanest example this estate has produced —
#: 146 dialogs have an id, 133 route their close through the helper that prompts
#: for unsaved changes, and 12 close directly and never reach it. The helper is
#: CORRECT; the e2e asserts its three labels exactly and clicks each one; the
#: corpus is the entire defect. Derivable from the delegation attribute, with
#: the twelve as exactly the complement.
DERIVATIONS = ("ast", "route_table", "schema", "enumeration", "filesystem", "requirement_text", "reachability")
REFUSED = {
    "names": "ACT-11: the corpus was routes whose PATH contained batch|bulk; the property was routes that iterate a collection",
    "naming": "a naming heuristic is the defect, not a derivation",
    "grep": "a regex also matches the docstring that explains the rename — derive by structure",
    "regex": "FRM-10: `\\bcan_\\b` cannot match can_edit_field, and matched nothing, and read as clean",
    "convention": "a convention is what the example happened to follow",
    # The subtlest one, and the only one that is not obviously a naming
    # heuristic: a population keyed on the marker the FIX adds. It is not the
    # example's name and not a marker the compliant cases happen to share — it
    # is what each case was GIVEN during the conversion, so the population is
    # the set of things already fixed and the ratchet's fall to zero counts the
    # conversion rather than the surface. Ask instead what can EXHIBIT the
    # property: every list render path that branches on a zero-length result,
    # not every element carrying `class="empty-state"`.
    "conversion_marker": "STA-02: the class was added BY the conversion, so the population was the set of "
                         "things already fixed and 75 → 38 → 0 measured the conversion, not the surface",
    "class_attribute": "a class is applied to the cases somebody has already handled; derive what CAN exhibit "
                       "the property instead",
    "marker": "a marker is carried by the compliant cases; the population is the cases that OUGHT to carry it",
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
    #: HOW the population was derived, printed with the numbers. Two sessions
    #: derived the same population the same day and got 17 and 12, both
    #: sincerely — one scanned a text window from one dialog id to the next,
    #: which runs past its own dialog so a neighbour's attribute counted as
    #: compliance; the other traced the close path. Neither number carried
    #: anything saying which to trust. A derived population ships with its
    #: derivation, not just its result.
    derived_from: str = ""
    population: int = 0
    subject: int = 0
    missing: list[str] = field(default_factory=list)      # in the population, never examined
    stray: list[str] = field(default_factory=list)        # examined, outside the declared population
    exempted: int = 0
    problems: list[str] = field(default_factory=list)     # why the row is red
    unrunnable: bool = False                              # a command exited non-zero: did not run
    capability: bool = False                              # a self-test proved the detector still detects
    detectors: dict = field(default_factory=dict)         # name -> members, when a requirement has several
    covered_by: dict = field(default_factory=dict)        # reach guards: layer -> how much of the bypass it covers
    note: str = ""                                        # reported, not judged


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


def judge_transform(t, root: Path, run) -> str:
    """A normalisation step proves it did not gut the corpus, or it is not trusted.

    `before:` and `after:` each print ONE number — bytes, nodes, lines, whatever
    the transform is measured in — and `keeps:` is the fraction that must
    survive, stated because the shrink you intended is a fact you know and the
    shrink you did not is the defect.
    """
    if not isinstance(t, dict) or not t.get("before") or not t.get("after") or t.get("keeps") is None:
        return f"transform {t!r} needs `before:`, `after:` and `keeps:` (the fraction that must survive)"
    name = t.get("name", "transform")
    sizes = []
    for half in ("before", "after"):
        got = run(root, t[half])
        if got.error:
            return f"{name}: {half} could not run: {got.error}"
        try:
            sizes.append(float(got.members[0]))
        except (IndexError, ValueError):
            return f"{name}: {half} did not print a single number"
    before, after = sizes
    if before <= 0:
        return f"{name}: the corpus measured {before} BEFORE the transform — there was nothing to transform"
    kept = after / before
    if kept < float(t["keeps"]):
        return (f"{name} kept {kept:.0%} of the corpus ({after:.0f} of {before:.0f}), declared to keep at least "
                f"{float(t['keeps']):.0%} — a transform that guts its corpus reports EXACTLY like a clean tree, "
                "and every check downstream of it has been passing over nothing")
    return ""


NEAR_MISS_KEYS = ("cmd", "from", "was")


def judge_capability(cap: dict, root: Path) -> list[str]:
    """A capability proves the detector DISCRIMINATES, or it proves nothing.

    `fires:` is the positive. `silent:` is one or more REAL near-misses — a
    sentence, route, element or record that actually exists in the tree and
    that the detector's looser sibling DID fire on. Real, not invented: `from:`
    is a path that must exist, and `was:` quotes the thing itself, so the entry
    cannot drift into a synthetic case somebody wrote to be easy to pass.
    """
    out: list[str] = []
    if not cap.get("fires"):
        out.append("capability lacks `fires:` — the command proving the detector catches its positive case")
    silent = cap.get("silent")
    if not silent:
        out.append("capability has no `silent:` — REFUSED by name, like a population derived from naming. An "
                   "all-positives self-test proves a detector FIRES, never that it DISCRIMINATES (FRM-04: a "
                   "switch tested against the cases in the switch), and over an empty corpus it is "
                   "indistinguishable from a detector that fires on everything")
        return out
    if not isinstance(silent, list):
        return out + ["capability `silent:` must be a list of near-misses"]
    for n in silent:
        if not isinstance(n, dict):
            out.append(f"near-miss {n!r} is not a mapping with {', '.join(NEAR_MISS_KEYS)}")
            continue
        lacking = [k for k in NEAR_MISS_KEYS if not n.get(k)]
        if lacking:
            out.append(f"near-miss {n.get('was', n.get('cmd', '?'))!r} lacks {', '.join(lacking)}")
            continue
        if not (root / str(n["from"]).split("::")[0]).exists():
            out.append(f"near-miss {n['was']!r} says it comes from {n['from']!r}, which does not exist — a "
                       "near-miss must be REAL, out of the tree, not one written to be easy to pass")
    return out


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
    row = Row(id=str(spec.get("id") or "?"), check=str(spec.get("check") or ""),
              claims=str(spec.get("claims") or ""),
              derived_from=str((spec.get("population") or {}).get("derived_from") or "?"))
    if not spec.get("id"):
        row.problems.append("a guard with no `id:` — a finding nobody can look up")
    if not row.check:
        row.problems.append("no `check:` — every guard serves one of C1–C12, or it is runtime with no owner")
    if not row.claims:
        row.problems.append("no `claims:` — the one sentence the population is the population OF")

    kind = str(spec.get("kind") or "sweep")
    if kind not in ("sweep", "reach"):
        row.problems.append(f"kind must be `sweep` or `reach`, not {kind!r}")
    complement = spec.get("complement")
    if kind == "reach" and not complement:
        row.problems.append(
            "a `reach` guard MUST declare `complement:` — REFUSED by name, like a population derived from "
            "naming. A reach number is a DENOMINATOR, and a denominator with no coverage-by-other-means "
            "measurement is a verdict without a population, which is the thing this module exists for. "
            "Measured on anat: apiFetch reaches 198 call sites and 783 bypass it, which reads as 20% and would "
            "have started a rewrite — but three other global fetch wrappers give every raw call the loading "
            "indicator, session activity, the CSRF header and the 401 bounce, 538 of them check status "
            "themselves and 297 report a failure to a person. The actionable number is 109, not 783")
    transforms = spec.get("transform") or []
    cap_spec = spec.get("capability") or {}
    pop_spec = spec.get("population") or {}
    sub_spec = spec.get("subject") or {}
    derived = str(pop_spec.get("derived_from") or "")
    if derived in REFUSED:
        row.problems.append(f"population.derived_from: {derived!r} is refused — {REFUSED[derived]}")
    elif derived not in DERIVATIONS:
        row.problems.append(f"population.derived_from must be one of {', '.join(DERIVATIONS)}, not {derived!r}")
    detectors = sub_spec.get("detectors")
    if detectors and sub_spec.get("cmd"):
        row.problems.append("a subject names `cmd` OR `detectors`, not both")
        return row
    if not pop_spec.get("cmd") or not (sub_spec.get("cmd") or detectors):
        row.problems.append("a guard names both a population.cmd and a subject.cmd (or subject.detectors), or it "
                            "is a claim about itself")
        return row

    if cap_spec:
        problems = judge_capability(cap_spec, root)
        if problems:
            row.problems.extend(problems)
            return row
        for cmd in [cap_spec["fires"]] + [n["cmd"] for n in cap_spec["silent"]]:
            proof = run(root, cmd)
            if proof.error:
                row.problems.append(f"the capability self-test did not pass: {proof.error} — a detector whose "
                                    "self-test cannot run is not proven, whatever its live scan reports")
                row.unrunnable = True
                return row
        row.capability = True

    for t in transforms:
        problem = judge_transform(t, root, run)
        if problem:
            row.problems.append(problem)
            row.unrunnable = "could not run" in problem or "did not print" in problem
            return row

    pop = run(root, pop_spec["cmd"])
    # ONE REQUIREMENT, SEVERAL DETECTORS: the population is the REQUIREMENT'S,
    # and what has to be asserted is that the detectors' corpora COVER it. Two
    # corpora that are each honestly reported can leave a hole neither reports,
    # and nothing in either one's output hints at it — STA-02 was guarded by a
    # sweep of AnatEmpty calls and a ratchet on hand-rolled markup, both sound,
    # and a list dropping a sentence into a plain table cell was neither.
    if detectors:
        named = [(str(d.get("name") or f"#{i}"), d.get("cmd")) for i, d in enumerate(detectors)]
        if any(not c for _, c in named):
            row.problems.append("every detector names a `cmd`")
            return row
        results = {n: run(root, c) for n, c in named}
        first_error = next((r.error for r in results.values() if r.error), "")
        by_detector = {n: set(r.members) for n, r in results.items()}
        sub = Set_(sorted(set().union(*by_detector.values())) if by_detector else [], first_error)
    else:
        by_detector = {}
        sub = run(root, sub_spec["cmd"])
    if pop.error or sub.error:
        row.unrunnable = True
        row.problems.append(pop.error or sub.error)
        return row

    row.population, row.subject = len(pop.members), len(sub.members)
    row.detectors = {n: len(m) for n, m in by_detector.items()}
    exemptions = spec.get("exemptions") or []
    for ex in exemptions:
        problem = judge_exemption(ex, root, today)
        if problem:
            row.problems.append(problem)
    excused = {str(e.get("member")) for e in exemptions if isinstance(e, dict) and not judge_exemption(e, root, today)}

    if not pop.members:
        if row.capability:
            # Reported, not judged. The detector is proven on a corpus that
            # cannot go away, so a live scan of nothing is a fact about the
            # tree rather than a verdict about the guard.
            row.note = (f"live corpus is EMPTY; capability proven by {cap_spec['fires']!r} against "
                        f"{len(cap_spec['silent'])} real near-miss(es). Nothing to compare, and that is "
                        "allowed here precisely because the detector is proven elsewhere")
            return row
        row.unrunnable = True
        row.problems.append(f"{pop_spec['cmd']!r} enumerated NOTHING — a population of nothing cannot show that "
                            "anything was swept. Declare a `capability:` self-test on a corpus that cannot go "
                            "empty, exclude the guard by declaration, or fix the enumeration")
        return row

    missing = [m for m in pop.members if m not in set(sub.members)]
    row.exempted = len([m for m in missing if m in excused])
    row.missing = [m for m in missing if m not in excused]
    row.stray = [m for m in sub.members if m not in set(pop.members)]
    if kind == "reach" and complement and row.missing:
        # BYPASSING A HELPER IS NOT THE SAME AS BEING UNCOVERED. The complement
        # is partitioned by what else covers it, and only the residue is a
        # finding. Reporting the bypass count alone is how a mostly-fine
        # codebase acquires a rewrite ticket.
        residue, layers = list(row.missing), {}
        for layer in complement:
            if not isinstance(layer, dict) or not layer.get("cmd") or not layer.get("name"):
                row.problems.append(f"every `complement:` layer names a `name` and a `cmd`: {layer!r}")
                return row
            got = run(root, layer["cmd"])
            if got.error:
                row.unrunnable = True
                row.problems.append(got.error)
                return row
            covered = set(got.members)
            layers[layer["name"]] = len([m for m in residue if m in covered])
            residue = [m for m in residue if m not in covered]
        row.covered_by = layers
        row.missing = residue
        row.note = (f"reach {row.subject}/{row.population}; of the {row.population - row.subject} that bypass it, "
                    + ", ".join(f"{n} covers {c}" for n, c in layers.items())
                    + f" — leaving {len(residue)} covered by NOTHING, which is the actionable number")
        if not residue:
            row.problems = [p for p in row.problems if "never examined" not in p]
            return row
        row.problems = [p for p in row.problems if "never examined" not in p]
        row.problems.append(f"{len(residue)} of {row.population} are covered by neither the helper nor any "
                            f"declared layer: " + ", ".join(residue[:8]))
    if by_detector and row.missing:
        row.note = ("no detector covers: " + ", ".join(row.missing[:8])
                    + " — each corpus here is honestly reported and the UNION is still a proper subset of the "
                      "requirement. A guard defined as 'anything not the approved way' grows a hole the day "
                      "somebody approves another way")
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
                  + f"  [{r['derived_from']}]"
                  + ("  [capability proven]" if r["capability"] else "")
                  + (f"   ({r['exempted']} exempted)" if r["exempted"] else ""))
            if r["note"]:
                print(f"       {r['note']}")
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
