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
from pathlib import Path

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


#: THE MEASURED CASE FOR REFUSING RATHER THAN ATTRIBUTING, which this kit has
#: asserted all day without a number until now. Over the same 109 rows:
#:
#:     mentions of another row carrying a status word (hand scan):  8
#:     what a strict extractor RESOLVES:                            3
#:     what it REFUSES:                                             5
#:     inside the resolved 3:   1 genuinely wrong · 1 correctly passed · 1 PHANTOM
#:
#: Refusing five of eight cost ZERO findings: the one genuine defect (PRF-06
#: citing STA-01 as absent, when STA-01 is implemented) was inside the 3. That is
#: the answer to the standing objection that a confident-only parser
#: under-detects, and it is the half of this measurement that holds.
#:
#: The half that does NOT hold was retracted within the hour by the person who
#: took it. The first reading reported two defects; the second was a phantom the
#: extractor's own author had written the prose for that morning. "The one thing
#: that was missing is now supplied by the PRT-03 work in this same pass"
#: asserts nothing about PRT-03's status — a capability was missing, past tense,
#: and PRT-03's work supplied it — but a status word within 45 characters of an
#: id looked like a claim. ONE IN THREE OF THE RESOLVED CLAIMS WAS FALSE, which
#: is not shippable, and the check is not landing until it is narrowed and
#: re-measured. The defect is TENSE AND GRAMMATICAL ROLE, not window size: "was
#: missing" is not "is missing", and a status word must attach to the id as its
#: SUBJECT rather than sit near it. If narrowing to that also loses the one real
#: finding, the honest conclusion is that this class is not mechanisable either,
#: and that is what gets reported — a guard that cries wolf is switched off, and
#: then nothing guards the real case.
#:
#: So `judge_claims` below is correct and is NOT evidence that anything should
#: be wired to it yet. The four lines that compare were never the risk.
#:
#: The refusals are refused for stateable reasons — a sentence carrying both an
#: open-word and a done-word near the id, or naming two different rows — which is
#: genuine ambiguity rather than parser weakness, and is why the answer is to
#: COUNT them rather than guess. The count is pinned, so the share of the table
#: nothing examines cannot quietly grow, and disabling the confidence filter
#: collapses it and fires the ratchet: the refusal is load-bearing, not decoration.
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
