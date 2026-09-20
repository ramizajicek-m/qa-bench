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

WHAT IS MECHANISABLE IS NARROWER AND IS WHERE THE COST LANDS: a justification
that asserts ANOTHER ROW'S STATUS is not prose, it is a claim about a value the
table already holds, and it can be verified on every run at zero cost. Over the
same 109 rows: 8 such cross-references, 2 of them stale — PRF-06 says STA-01 is
absent (implemented), PRT-08 says PRT-03 is missing (implemented). Both encode a
dependency the next person plans around, so the next person starts by building
something that already exists. Two of eight wrong, in a file three days old,
maintained carefully: that is the rate when nothing re-reads.

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
