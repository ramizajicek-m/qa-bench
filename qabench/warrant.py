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

WHAT IS DELIBERATELY NOT HERE YET, and why this module holds no policy of its
own. On 2026-09-20 a tracker row (SEC-02) was found asserting a gap that was
already half closed: its reason said the admin templates mix hidden and disabled
"with NOTHING TO TEST AGAINST", while a test containing an explicit policy
statement and driving both directions had existed for a while. The row carried a
target date, and anyone planning work would have planned against it.

THE CLASS: a justification with no expiry and no re-check is prose pretending to
be evidence — a guard that cannot fail, because nothing re-reads it, and it
silently sets other people's plans.

The mechanism that would catch it is a LAST-VERIFIED date with a staleness
window, and the window is a number. This kit's own rule, paid for twice today,
is that a threshold is measured rather than chosen: `distinct`'s 400 characters
stands on a measured innocent overlap of 219, and the peer-stack preflight was
dropped because its measurement turned out to be false. The session that found
SEC-02 is sweeping every partial and absent reason to count how many are stale.
That count is the measurement, and the window waits for it. Until then this
module carries `review_by` — a date each warrant sets for itself, which is a
weaker claim than a cadence and is stated as one.

So: `stale_after_days` has NO DEFAULT. A caller that wants staleness declares
the number and cites where it came from, or does not get the rule.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

#: The four fields, in the order a reader needs them. `subject` is named by the
#: caller, because a population exempts a member and `distinct` exempts a pair.
REQUIRED = ("reason", "evidence", "review_by")


def judge(entry, root: Path, today: dt.date, *, subject: str = "member", label: str = "exemption",
          stale_after_days: int | None = None) -> str:
    """"" when the warrant stands; otherwise the one sentence saying why not.

    `stale_after_days` is opt-in and has no default: see the module docstring.
    When given, a `verified:` date older than the window is red, and a warrant
    with no `verified:` at all is red — an undated re-read is not a re-read.
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

    if stale_after_days is not None:
        verified = entry.get("verified")
        if not verified:
            return (f"{label} {who!r} carries no `verified:` date, and this table declares a staleness window "
                    f"of {stale_after_days} days — an undated re-read is not a re-read")
        try:
            last = dt.date.fromisoformat(str(verified))
        except ValueError:
            return f"{label} {who!r}: verified {verified!r} is not a date"
        age = (today - last).days
        if age > stale_after_days:
            return (f"{label} {who!r} was last verified {last} ({age} days ago, window {stale_after_days}) — "
                    "a justification with no re-check is prose pretending to be evidence, and it sets other "
                    "people's plans while nothing can make it go red")
    return ""
