"""warrant — the one contract for a free-text justification that has to earn its keep.

A WARRANT is any entry that says "this thing is excused, and here is why": a
`population` exemption, a `distinct` exemption, a census register entry, and —
the case this module was extracted for — the `reason` on a tracker row that is
`partial` or `absent`.

Every one of them needs the same four things, and the estate has now written
them out four times in four files:

    subject      what is excused (a member, a pair, a row id)
    reason       a sentence a stranger would accept
    evidence     a path in the tree that must EXIST — a reason citing a file
                 that has gone is a reason nobody has read since it went
    review_by    a date, and past it the warrant is red

One copy, because a contract with four copies is four contracts. The estate
learned this with `test_qa_conformance.py`, which was a template copied into six
repos and drifted into six meanings of `implemented`.

A JUSTIFICATION MAY NOT CONTAIN A POINTER THAT CAN MOVE INDEPENDENTLY OF THE
CLAIM. This replaces "reasons go stale", which is both weaker and unactionable —
it tells you to re-read everything, which nobody does. Three instances from one
pass, none careless, all true when written:

    PRF-06 cited STA-01 as absent, and STA-01 was implemented days later by the
           same programme. A ROW ID is a pin.
    SEC-02 claimed "nothing to test against" for hidden-versus-disabled, while
           two guards test it and one states the policy in its own docstring.
           A CLAIM ABOUT ANOTHER FILE'S CONTENTS is a pin.
    Eleven SCN rows cited `clients/detail.html:12514` for a getUserMedia call.
           It now sits at 12847 — the code did not move, THE FILE GREW ABOVE IT.
           A LINE NUMBER is a pin.

Each drifted silently, because nobody re-reads a justification. The fix is
actionable at the moment of writing rather than at some later audit: A CITATION
SHOULD BE SOMETHING A SEARCH CAN FIND AGAIN, NOT A COORDINATE. "the voice test
in clients/detail.html" survives the file growing; "clients/detail.html:12514"
does not. A function name over a line, a route path over a router index, a
test's name over its position.

This is the same family as keying a ratchet on function names rather than
path:LINE, which this estate learned after four failures in one morning where a
guard fired because something was ADDED ABOVE it. That lesson was learned for
guards and never carried to prose — and the prose is worse, because a drifted
ratchet goes red and gets looked at, while a drifted justification stays green
and gets believed.

So `evidence:` is refused when it is a line coordinate. A row id can be checked
(the table holds the target: see `judge_claims`), a claim about a file's
contents can sometimes be checked, and a line number cannot be checked at all —
but it can be AVOIDED, which is cheaper.

THERE IS NO STALENESS RULE HERE, AND THE MEASUREMENT IS WHY. On 2026-09-20 a
tracker row (SEC-02) was found asserting a gap that was already half closed: its
reason said the admin templates mix hidden and disabled "with NOTHING TO TEST
AGAINST", while a test containing an explicit policy statement and driving both
directions had existed for a while. The row carried a target date, and anyone
planning work would have planned against it.

The obvious mechanism is a last-verified date with a staleness window. It was
written here, opt-in and with no default, pending the number — and then the
number arrived and refuted it. Age of every partial/absent reason in that
tracker, by git blame on the reason line:

    0-1 day     8
    2-7 days   22
    8-30 days   0
    31-90 days  0
    >90 days    0

The oldest justification in the file is THREE DAYS; the tracker is three days
old with 275 commits since. There is no tail to separate, so there is no shape
to site a window on — and both confirmed defects sit in the youngest possible
band. SEC-02's reason was false within three days of being written. PRF-06
asserts STA-01 is absent; STA-01 was implemented days later, during the same
programme. An age-keyed window would have flagged NEITHER, at any threshold.

Not because the threshold would be wrong: because AGE IS NOT THE MECHANISM.
These reasons did not decay, they were OVERTAKEN. The tree moves faster than the
prose describing it, and a justification about a fast-moving codebase can be
wrong the week it is written. So the staleness half was deleted rather than left
switched off — a rule nobody can defend when it fires is worse than no rule, and
one sitting unused with a docstring saying "pending a measurement" is an
invitation to site it badly later. The measurement is in; the answer is no.

WHAT LOOKS MECHANISABLE IS NARROWER, AND HAS NOT EARNED ITS PLACE YET: a
justification that asserts ANOTHER ROW'S STATUS is not prose, it is a claim
about a value the table already holds, and it can be verified on every run at
zero cost. Over the same 109 rows there are 8 such mentions. ONE is genuinely
wrong — PRF-06 says STA-01 is absent and STA-01 is implemented, a blocker that
has since been built, so the next person starts by building a loading indicator
that already exists. One is correctly passed. One was a PHANTOM of the
extractor, retracted within the hour, and the other five it refused. One real
finding in a carefully maintained file three days old is still a rate worth
having; two was not the rate, and the difference is the detector's own error.

The general case — "is this reason still true" — stays unmechanisable and should
stay that way. A keyword pass over those same reasons produced two phantoms that
had to be withdrawn, both reasons describing a deliberate state rather than a
gap. A re-read against the code is the control, a person does it, and the
cross-reference scan is the one part of that re-read a machine can do.

"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

#: `path/to/file.ext:1234` — a coordinate. `path/to/file.py::test_name` is not
#: one: `::` is the estate's convention for naming a member, which a search
#: finds again after the file grows.
_LINE_COORDINATE = re.compile(r"(?<!:):\d+(?::\d+)?\s*$")

#: The four fields, in the order a reader needs them. `subject` is named by the
#: caller, because a population exempts a member and `distinct` exempts a pair.
REQUIRED = ("reason", "evidence", "review_by")


def judge(entry, root: Path, today: dt.date, *, subject: str = "member", label: str = "exemption") -> str:
    """"" when the warrant stands; otherwise the one sentence saying why not.

    There is no staleness argument, deliberately: see the module docstring. The
    date that matters is `review_by`, which a warrant sets for ITSELF and which
    says when a re-read is due. It does not make the re-read happen, and on the
    measured data it would not even have made these overdue.
    """
    if not isinstance(entry, dict):
        return f"{label} {entry!r} is not a mapping with {subject}, {', '.join(REQUIRED)}"
    who = entry.get(subject)
    if not who:
        return f"{label} lacks {subject}: {entry!r}"
    lacking = [k for k in REQUIRED if not entry.get(k)]
    if lacking:
        return f"{label} {who!r} lacks {', '.join(lacking)}"

    evidence = entry["evidence"] if isinstance(entry["evidence"], list) else [entry["evidence"]]
    coordinates = [e for e in evidence if _LINE_COORDINATE.search(str(e))]
    if coordinates:
        return (f"{label} {who!r} cites a LINE COORDINATE: {', '.join(map(str, coordinates))}. A line number is a "
                "pointer that moves independently of the claim — eleven rows citing "
                "clients/detail.html:12514 drifted to 12847 because the file grew ABOVE the code, which did not "
                "move. Cite something a search can find again: a function name over a line, a route path over a "
                "router index, a test's name over its position")
    absent = [e for e in evidence if not (root / str(e).split("::")[0]).exists()]
    if absent:
        return (f"{label} {who!r}: evidence does not exist: {', '.join(absent)} — a reason citing a file that "
                "has gone is a reason nobody has read since it went")
    try:
        due = dt.date.fromisoformat(str(entry["review_by"]))
    except ValueError:
        return f"{label} {who!r}: review_by {entry['review_by']!r} is not a date"
    if due < today:
        return f"{label} {who!r} expired {due} — re-verify the reason against the code, or close the gap"

    return ""


#: THE MEASURED CASE FOR REFUSING RATHER THAN ATTRIBUTING, which this kit
#: asserted all day on anecdote before anyone put a number under it. ONE corpus
#: — 109 tracker rows, 8 mentions of another row carrying a status word —
#: measured BOTH WAYS, which is stronger than comparing two passes:
#:
#:     STRICT (the status word attaches to the id as its SUBJECT, present tense)
#:         resolved 1 · refused 7 · wrong 1 · phantoms 0
#:     LOOSE (proximity only, a status word within 45 characters of an id)
#:         resolved 8 · refused 0 · wrong 2
#:
#:     attributions the strict parser DECLINED TO INVENT:            7
#:     of those, extra "findings" the loose parser reports:          1
#:     of that one, how many were real:                              0
#:
#: So: seven attributions declined, of which the loose parser would have
#: reported exactly one as a defect, and that one was a phantom — a sentence
#: reading "the one thing that was missing is now supplied by the PRT-03 work",
#: which asserts nothing about PRT-03's status and which the extractor's own
#: author had written that morning. Refusal cost nothing and bought the removal
#: of a false finding. Precision 1.0 strict against 0.5 loose.
#:
#: NOT OVERSOLD, in the words of the person who took the measurement: the loose
#: parser's other six attributions were all CORRECT passes. The strict parser is
#: not better because those six were dangerous. It is better because the loose
#: one cannot tell which of the eight it is competent to judge, and the one it
#: got wrong is the one that cost.
#:
#: THE FOUR NUMBERS TRAVEL TOGETHER — 8 claims · 1 resolved · 1 wrong · 7
#: refused — and so does the sentence that goes with them: IT FOUND A GENUINE
#: DEFECT NOTHING ELSE WOULD HAVE FOUND, AT ZERO FALSE-POSITIVE COST, AND IT
#: CANNOT SEE SEVEN OF EIGHT CLAIMS. Precision known and perfect; recall unknown
#: and probably poor. Without that sentence the first reader of "0 phantoms"
#: believes the tracker's prose has been validated when seven eighths of it has
#: never been looked at — which is this whole week's lesson pointed at our own
#: fix.
CLAIM_KEYS = ("row", "cites", "asserts")


def judge_claims(claims, statuses: dict, *, unresolved: int, unresolved_pin=None) -> list[str]:
    """Every way a table's cross-references disagree with the table itself.

    A justification that asserts ANOTHER ROW'S STATUS is not prose: it is a
    claim about a value the table already holds, and it can be verified on every
    run at zero cost. PRF-06 said STA-01 was absent and STA-01 was implemented;
    it is implemented, so the next person starts by building a loading indicator
    that already exists. (The second instance first reported alongside it,
    PRT-08 citing PRT-03, was retracted as a phantom of the extractor: see the
    measurement above. One real finding in 8 mentions, not two.)

    This is the JUDGING half only. Extraction stays in the project, where the
    vocabulary lives and where all the risk is; six projects share the four
    lines that compare, not the parser that guesses.

    A claim whose blocker is OUTSIDE the table — a ticket, another repo, a
    person, a vendor — is unresolvable by construction and belongs in the
    project's own declared exclusions, never in `claims` and never read as clean.
    """
    out: list[str] = []
    for c in claims:
        if not isinstance(c, dict) or any(not c.get(k) for k in CLAIM_KEYS):
            out.append(f"claim {c!r} lacks one of {', '.join(CLAIM_KEYS)}")
            continue
        actual = statuses.get(str(c["cites"]))
        if actual is None:
            out.append(f"{c['row']} cites {c['cites']}, which this table does not hold — a cross-reference to "
                       "something outside the table is unresolvable by construction and is excluded by "
                       "declaration, not by being compared to nothing")
        elif str(actual) != str(c["asserts"]):
            out.append(f"{c['row']} justifies itself by saying {c['cites']} is {c['asserts']!r}; {c['cites']} is "
                       f"{actual!r} — a blocker that has since been built, and the next person plans around it")
    if unresolved_pin is None:
        out.append(f"the extractor refused {unresolved} claim(s) and nothing pins that number — an unresolved "
                   "share that is not asserted is a share that can quietly grow")
    elif unresolved != unresolved_pin:
        out.append(f"the extractor refused {unresolved} claim(s), pinned at {unresolved_pin}. Fewer refusals is "
                   "not automatically better: it is what disabling the confidence filter looks like, and that is "
                   "how phantoms get attributed. Move the pin in the commit that moves the parser")
    return out
