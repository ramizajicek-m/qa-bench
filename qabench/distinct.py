"""distinct — a guard that asserts only SHAPE passes over any corruption that preserves shape.

    python -m qabench distinct            # the `distinct:` block of qa/manifest.yml
    python -m qabench distinct --json

WHY. On 2026-09-20 a row of anat's UI tracker was demoted with a `str.replace`
over the whole file, keyed on the LAST SENTENCE of that row's reason. Twenty-one
other rows end with the same sentence, because an earlier gap pass had written
identical bookkeeping into all of them. So SEC-01, ACT-03, LST-07, MSG-01 and
eighteen more silently acquired NAV-08's reason — each then claiming the sidebar
mark moves to the sub-item inside a client — and the file went to staging.

Every test over that tracker stayed green: 109 rows present, every requirement
verbatim, every implemented row naming a collectable test, every partial
carrying a reason and a target. THE STRUCTURE WAS PERFECT AND THE CONTENTS WERE
FALSE. Every assertion was about shape; none was about whether a row's reason
belongs to that row.

This is not the narrow-corpus class the rest of this kit's instruments address.
That guard was COMPLETE. It swept every row and asserted the right things about
each one, and none of those things could see a reason that had been pasted in
from somewhere else. A data guard that asserts only shape will pass over any
corruption that preserves shape.

AND THE PART THAT DEFEATS A PROCESS FIX. The author had committed, one hour
earlier in the same batch, a message whose whole subject was that a bulk edit is
verified by reading one changed line and never by counting matches — and then
verified this edit by counting matches, which were right. The rule was not
forgotten. It was applied to the cheapest surface to look at. Any fix that
assumes people forget the rule will miss this one.

THE THRESHOLD IS MEASURED, NEVER CHOSEN, which is what makes the check hold:
in that table the longest innocent overlap between two rows' free text is 219
characters, and the leak was 1012. Four hundred is therefore a real floor — a
person cannot accidentally write four hundred identical characters into two rows
and a global replace cannot avoid it. Every run prints the measurement for the
table in front of it, pinned or not, so the number comes from the data rather
than from a session's taste — and an unpinned table is told what to pin. A pin
at or below the measured overlap is refused with both numbers printed, because
a threshold that the table already exceeds cannot fire before the table does.

WHAT IT CANNOT SEE, stated: a corruption that is SHORT. Two rows whose reasons
differ only in a sentence are invisible here and always will be — the sliding
window is what makes the check certain, and certainty costs sensitivity. This
catches the bulk edit, which is the one that hits twenty-one rows at once.

Exit: 0 no pair shares more than the pin · 1 a pair does, or a pin that the
table's own overlap already exceeds · 3 no table, a row source that could not
run, or fewer than two rows (a distinctness check over one row decides nothing).

Manifest shape:

    distinct:
      tables:
        ui-standard:
          rows: "python3 scripts/qa/tracker_rows.py"   # prints JSON [{id, text}, ...]
          max_shared: 400                               # measured: longest innocent overlap is 219
          exemptions:
            - pair: [GEN-01, GEN-02]
              reason: "both quote the same standard clause verbatim, by decision"
              evidence: qa/decisions.yml
              review_by: 2026-12-01
"""
from __future__ import annotations

import datetime as dt
import json
import shlex
import subprocess
import sys
from pathlib import Path

import yaml

from . import warrant

EXEMPTION_KEYS = ("pair", "reason", "evidence", "review_by")


def read_rows(root: Path, cmd: str, *, timeout: float = 120.0) -> tuple[list[dict], str]:
    """([{id, text}], "") or ([], why it could not be read)."""
    try:
        p = subprocess.run(shlex.split(cmd), cwd=root, capture_output=True, text=True, timeout=timeout)
    except (OSError, ValueError, subprocess.SubprocessError) as ex:
        return [], f"{cmd!r} could not run: {ex}"
    if p.returncode != 0:
        tail = (p.stderr or p.stdout or "").strip().splitlines()[-1:] or [""]
        return [], f"{cmd!r} exited {p.returncode}: {tail[0][:200]}"
    try:
        rows = json.loads(p.stdout)
    except ValueError as ex:
        return [], f"{cmd!r} did not print JSON: {ex}"
    if not isinstance(rows, list) or any(not isinstance(r, dict) or "id" not in r or "text" not in r for r in rows):
        return [], f"{cmd!r} must print a list of objects with `id` and `text`"
    return [{"id": str(r["id"]), "text": str(r["text"])} for r in rows], ""


def _windows(text: str, k: int) -> set[str]:
    return {text[i:i + k] for i in range(len(text) - k + 1)}


def shared_at(rows: list[dict], k: int) -> list[tuple[str, str, str]]:
    """Every (id_a, id_b, passage) where two rows share a run of exactly k chars.

    A SLIDING window, not a prefix or a line: a leak lands mid-reason, and a
    check anchored to a boundary would step straight over the one that happened.
    """
    if k < 1:
        return []
    seen: dict[str, str] = {}
    out: list[tuple[str, str, str]] = []
    for row in rows:
        for w in _windows(row["text"], k):
            first = seen.get(w)
            if first is None:
                seen[w] = row["id"]
            elif first != row["id"]:
                out.append((first, row["id"], w))
    return out


def longest_shared(rows: list[dict], *, cap: int | None = None) -> tuple[int, list[tuple[str, str, str]]]:
    """(the longest run any two rows share, the pairs that share it).

    Binary search on the window length: sharing a run of k implies sharing every
    shorter run, so the property is monotone and the search is exact.
    """
    hi = cap if cap is not None else max((len(r["text"]) for r in rows), default=0)
    lo, best, pairs = 0, 0, []
    while lo <= hi:
        mid = (lo + hi) // 2
        if mid == 0:
            break
        hit = shared_at(rows, mid)
        if hit:
            best, pairs, lo = mid, hit, mid + 1
        else:
            hi = mid - 1
    return best, pairs


def judge_exemption(ex, root: Path, today: dt.date) -> str:
    """The shared warrant contract, plus the one thing that is this module's
    own: a pair is exactly two row ids."""
    if isinstance(ex, dict) and ex.get("pair") is not None and (
            not isinstance(ex["pair"], list) or len(ex["pair"]) != 2):
        return f"exemption pair {ex['pair']!r} must be exactly two row ids"
    problem = warrant.judge(ex, root, today, subject="pair", label="exemption")
    return problem


def judge_table(name: str, spec: dict, root: Path, today: dt.date, *, read=read_rows) -> dict:
    out = {"table": name, "rows": 0, "max_shared": spec.get("max_shared"), "measured": None,
           "offenders": [], "problems": [], "unrunnable": False}
    if not spec.get("rows"):
        out["problems"].append("no `rows:` command — nothing to compare")
        out["unrunnable"] = True
        return out
    rows, why = read(root, spec["rows"])
    if why:
        out["problems"].append(why)
        out["unrunnable"] = True
        return out
    out["rows"] = len(rows)
    if len(rows) < 2:
        out["problems"].append(f"{len(rows)} row(s) — a distinctness check over fewer than two decides nothing")
        out["unrunnable"] = True
        return out

    exemptions = spec.get("exemptions") or []
    for ex in exemptions:
        problem = judge_exemption(ex, root, today)
        if problem:
            out["problems"].append(problem)
    excused = {frozenset(map(str, e["pair"])) for e in exemptions
               if isinstance(e, dict) and isinstance(e.get("pair"), list) and len(e["pair"]) == 2
               and not judge_exemption(e, root, today)}

    pin = spec.get("max_shared")
    kept = [r for r in rows]
    # Measure over the pairs nobody has excused, so an exempted pair cannot
    # raise the measured floor and hide the next leak behind itself.
    measured, _ = longest_shared(kept) if not excused else _measure_excluding(kept, excused)
    out["measured"] = measured

    if not isinstance(pin, int):
        out["problems"].append(
            f"`max_shared` is not pinned. The longest passage two rows of this table share is {measured} "
            f"characters; pin a number above it, with that measurement in the comment — a threshold chosen "
            "rather than measured is a threshold nobody can defend when it fires")
        return out
    if measured >= pin:
        offenders = [(a, b, w) for a, b, w in shared_at(kept, pin) if frozenset((a, b)) not in excused]
        out["offenders"] = [{"a": a, "b": b, "chars": len(w), "passage": w[:120]} for a, b, w in offenders[:20]]
        out["problems"].append(
            f"{len(offenders)} pair(s) share {pin}+ characters of free text (longest run here: {measured}). "
            "A person cannot accidentally write that much identical prose into two rows and a global replace "
            "cannot avoid it, so each pair is one of two things: a LEAK, which the data must lose, or innocent, "
            "which an exemption must name with its reason. The pin must end up ABOVE the table's longest "
            "innocent overlap, or it cannot fire before the table does and it will be switched off in a week")
    return out


def _measure_excluding(rows: list[dict], excused: set) -> tuple[int, list]:
    """The longest shared run over pairs nobody has excused."""
    lo, hi, best = 0, max((len(r["text"]) for r in rows), default=0), 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if mid == 0:
            break
        hit = [t for t in shared_at(rows, mid) if frozenset((t[0], t[1])) not in excused]
        if hit:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best, []


def run_distinct(root: Path, cfg: dict, *, today: dt.date | None = None, read=read_rows) -> dict:
    today = today or dt.date.today()
    tables = cfg.get("tables") or {}
    rows = [judge_table(n, s or {}, root, today, read=read) for n, s in sorted(tables.items())]
    return {"tables": rows,
            "red": [r for r in rows if r["problems"] and not r["unrunnable"]],
            "unrunnable": [r for r in rows if r["unrunnable"]]}


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def run(argv: list[str], *, today: dt.date | None = None) -> int:
    root = Path(_arg(argv, "--repo", ".")).resolve()
    mpath = root / "qa" / "manifest.yml"
    doc = (yaml.safe_load(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}) or {}
    cfg = doc.get("distinct")
    if not cfg or not cfg.get("tables"):
        print(f"no `distinct:` block with `tables:` in {mpath} — no table edited programmatically declares "
              "that its rows must stay distinct (exit 3)", file=sys.stderr)
        return 3
    out = run_distinct(root, cfg, today=today)
    if "--json" in argv:
        print(json.dumps(out, indent=1, ensure_ascii=False))
    else:
        for t in out["tables"]:
            mark = "RED " if t["problems"] else "ok  "
            print(f"  {mark}{t['table']:28} {t['rows']:>4} rows · longest shared run {t['measured']} "
                  f"· pin {t['max_shared']}")
            for p in t["problems"]:
                print(f"       {p}")
            for o in t["offenders"]:
                print(f"       {o['a']} ≡ {o['b']}  {o['chars']} chars: {o['passage']!r}")
    if out["unrunnable"]:
        return 3
    return 1 if out["red"] else 0
