"""escapes — the defect escape rate and the ODC trigger histogram, estate-wide.

    python -m qabench escapes                      # this repo's ledger (qa/manifest.yml `ledger:`)
    python -m qabench escapes --ledger PATH        # another ledger
    python -m qabench escapes --days 30 --json     # rows as JSON, for another program
    python -m qabench escapes --benchmark PATH     # a seeded-fault benchmark instead of a ledger

WHY THIS IS IN THE KIT. anat computed its escape rate from 2026-09-10 in
scripts/qa_week/gap_analysis.py and the other five projects never did; the
number that says "how much reaches a person" existed in one repo. Lifted here
2026-09-19 so six ledgers are read by one parser and one vocabulary.

DEFECT ESCAPE RATE = defects a person met in production ÷ all ledger defects
(industry: elite teams under 10 %; above 25 % is a structural gap). The ledger
is prose, so `found by` is classified by vocabulary, and the one rule that keeps
the number honest: a row matching NEITHER vocabulary is RED, never silently
internal — the direction that would make the rate read better than it is.

ODC TRIGGER HISTOGRAM. Orthogonal Defect Classification (Chillarege 1992) sorts
escapes by what EXPOSED them — Sequencing, Interaction, Variation, Coverage,
Rare Situation, Side Effect, Hardware/Software Configuration, Lateral
Compatibility, Design Conformance, Language Dependency — rather than by feature. The histogram says
which verification activity is missing; it is the feedback loop that keeps
docs/methodology.md from going stale. A ledger row carries it in a `trigger`
column when it has one; benchmarks/escaped.yml carries it on every row.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

TRIGGERS = ("Sequencing", "Interaction", "Variation", "Coverage", "Rare Situation", "Side Effect",
            "Hardware Configuration", "Software Configuration", "Lateral Compatibility",
            "Design Conformance", "Language Dependency")
SHAPES = {"a": "sequence / second action", "b": "rare data shape", "c": "device / physical",
          "d": "two correct halves", "e": "environment", "f": "genuine UX request",
          "g": "permission / scope", "h": "other"}

#: People who met a defect IN USE — the estate's customers and stakeholders, by
#: first name as the ledgers write them. A project adds its own under
#: `people:` in qa/manifest.yml; these are the names every ledger in the estate
#: already uses, kept here so a fresh clone classifies without configuration.
ESTATE_PEOPLE = ("naomi", "natalia", "nati", "emilio", "mimi", "yael", "israel", "ישראל", "shahar", "שחר",
                 "chilik", "חיליק", "meir", "מאיר", "yehuda", "יהודה", "yanki", "יענקי", "eliezer", "אליעזר",
                 "oren", "gili", "a.n.a", "ana staff", "ran", "ofir", "arie", "arie eshed")
_GENERIC_CUSTOMER = (r"customer|^(?:a|the|one|our) client(?![-\w])|\bcaller\b|the office|the shop|the warehouse"
                     r"|\ba person\b|\bthe reader\b|\bimprovement\b|#\d{3}\b|\bon prod\b|\bin production\b"
                     r"|\bthe picker\b|\bthe driver\b|whatsapp|screenshot|video|\bphoto")
_ON_STAGING = re.compile(r"\bstaging\b", re.I)
_ON_PRODUCTION = re.compile(r"\bprod(?:uction)?\b", re.I)
#: Rami is both: reading a sent email or holding a printed label he met the
#: defect in USE (customer); asking "how do we know it runs?" is process
#: (internal). A Rami row is customer unless it reads as a question.
_RAMI = re.compile(r"\brami\b|\bרמי\b", re.I)
_RAMI_PROCESS = re.compile(r"\?|asking|question|how do we|\bwhy\b", re.I)
INTERNAL_FINDERS = re.compile(
    r"session|review|refuter|bench|sweep|ruff|semgrep|schemathesis|\baxe\b|mutmut|hypothesis"
    r"|coderabbit|\btool\b|triage|\bloop\b|probe|\brun\b|guard|test|walk|register|\bme\b|\bci\b|lane"
    r"|grep|reading|tracing|mutation|derivation|scan|ratchet|check|\bmake\b|notes|writing|noticing"
    r"|counting|fixing|scoping|running|bounding|opening|`|the day itself|\bthe c\d+\b|coordinator"
    r"|panel|analysis|matrix|skill|its own|git status|flip|author|branch|\btier\b|night|portal"
    r"|nothing outside|the first|the same|the other|the work|\bread\b|intake writer|parser|the day\b"
    r"|the unit|the e2e|the walk|runner|nobody|browser|red \w+ job|unit job|\bpass\b|the merged tree"
    r"|heartbeat|stamp|promotion_gate|promot|qualification|\bgate\b|\bgraph\b|quality|audit"
    r"|verification|fixture|integration|github|landing|\breviews?\b|consolidation|\bcommand\b"
    r"|parity|differential|replay|oracle|conformance|explorer|seed"
    # Estate-wide phrasings found on the first read of all six ledgers,
    # 2026-09-19 — every one names OUR activity, none a person in use.
    r"|closing|closure|wiring|building|mutating|acceptance|harness|poller|census|inventory|regression|robustness|conventions|architecture"
    r"|controls?\b|dispatching|acting on|this round|the never-accepted|artifact|trace\b|the sibling"
    r"|\b(?:GEN|NAV|FRM|ACT|MSG|LST|SCN|PRT|STA|MOB|SEC|PRF|ACC|UI)-", re.I)
_HEAD = re.compile(r"^[\s(\d)]*([^,;(—:]*)")


def customer_pattern(people=()) -> re.Pattern:
    names = "|".join(re.escape(p) for p in (*ESTATE_PEOPLE, *people) if p)
    return re.compile(rf"(?:\b(?:{names})\b|{_GENERIC_CUSTOMER})", re.I)


def classify_finder(found_by: str, people=()) -> str | None:
    """'customer' | 'internal' | None (unclassified — the caller makes it red).
    Only the HEAD of the phrase decides (the words before the first comma,
    semicolon, dash or parenthesis): the finder is the subject."""
    head = (_HEAD.match(found_by).group(1) or "").strip() or found_by
    if head.startswith("`"):
        return "internal"
    if _ON_STAGING.search(found_by) and not _ON_PRODUCTION.search(found_by):
        return "internal"          # it never left staging
    if _RAMI.search(head):
        return "internal" if _RAMI_PROCESS.search(found_by) else "customer"
    if customer_pattern(people).search(head):
        return "customer"
    if INTERNAL_FINDERS.search(head):
        return "internal"
    return None


_ROW_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
_SECTION_DATE = re.compile(r"^## (\d{4}-\d{2}-\d{2})")


def ledger_rows(text: str) -> list[dict]:
    """Every defect row of a calibration ledger: {date, found_by, what, defect, trigger}.

    Two table shapes coexist across the estate. The C1–C12 shape carries its
    own date in column 1; the older shape (`| Defect | Found by | …`) carries
    none and takes the date of the `## YYYY-MM-DD` section it sits in. Columns
    are located from each table's HEADER by name, never by position."""
    rows, section_date, found_col, check_col, trig_col, header_dated, ncols = [], None, None, None, None, True, 0
    for line in text.splitlines():
        m = _SECTION_DATE.match(line)
        if m:
            section_date, found_col = m.group(1), None
            continue
        if not line.startswith("|"):
            continue
        cells = [c.strip().replace("\x00", "|")
                 for c in line.strip().strip("|").replace("\\|", "\x00").split("|")]
        low = [c.lower() for c in cells]
        if any("found by" == c for c in low):
            found_col, ncols = low.index("found by"), len(cells)
            header_dated = any("date" in c for c in low)
            check_col = next((i for i, c in enumerate(low) if "check" in c or "owned by" in c), None)
            trig_col = next((i for i, c in enumerate(low) if "trigger" in c), None)
            continue
        if found_col is None or set(cells[0]) <= {"-", " ", ":"}:
            continue
        m = _ROW_DATE.match(cells[0])
        shift = 1 if (m and not header_dated) else 0
        fcol = found_col + shift
        ccol = check_col + shift if check_col is not None else None
        tcol = trig_col + shift if trig_col is not None else None
        if len(cells) > ncols + shift:
            cells = cells[:ncols + shift - 1] + [" | ".join(cells[ncols + shift - 1:])]
        if len(cells) <= fcol:
            continue
        date_s = m.group(1) if m else section_date
        if not date_s:
            continue
        # A row whose check is "—" is not a defect (a rejected approach, a floor
        # recorded for the record); it stays in the ledger and out of the rate.
        check = cells[ccol].strip() if ccol is not None and len(cells) > ccol else "C?"
        trigger = cells[tcol].strip() if tcol is not None and len(cells) > tcol else None
        rows.append({"date": date_s, "found_by": cells[fcol], "what": (cells[1] if m else cells[0])[:120],
                     "defect": not check.startswith("—"), "trigger": trigger or None})
    return rows


def defect_escape_rate(rows: list[dict], *, today: dt.date, days: int, people=()) -> dict:
    since = today - dt.timedelta(days=days)
    counts, unclassified = {"customer": 0, "internal": 0}, []
    for r in rows:
        try:
            when = dt.date.fromisoformat(str(r.get("date", "")))
        except ValueError:
            unclassified.append(f"{r['date']} (not a date) {r['found_by'][:60]!r}")
            continue
        if when < since or not r.get("defect", True):
            continue
        kind = classify_finder(r["found_by"], people)
        if kind is None:
            unclassified.append(f"{r['date']} {r['found_by'][:60]!r}")
        else:
            counts[kind] += 1
    total = counts["customer"] + counts["internal"]
    return {"days": days, "customer": counts["customer"], "internal": counts["internal"], "total": total,
            "unclassified": unclassified, "rate": (round(counts["customer"] / total, 3) if total else None)}


def trigger_histogram(rows: list[dict]) -> dict:
    """{trigger: n} over rows that carry one; `untagged` counts the rest. A
    trigger outside the ODC vocabulary is a finding, not a bucket."""
    hist, unknown, untagged = Counter(), [], 0
    for r in rows:
        t = r.get("trigger")
        if not t:
            untagged += 1
        elif t in TRIGGERS:
            hist[t] += 1
        else:
            unknown.append(t)
    return {"triggers": dict(hist.most_common()), "untagged": untagged, "unknown": sorted(set(unknown))}


def benchmark_rows(path: Path) -> list[dict]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = doc.get("rows") or []
    for r in rows:
        if isinstance(r.get("date"), dt.date):        # YAML parses a bare date; the ledger path holds strings
            r["date"] = r["date"].isoformat()
        r.setdefault("found_by", r.get("by", ""))
        r.setdefault("defect", r.get("shape") != "f")
    return rows


def _date(r: dict) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(r.get("date", "")))
    except ValueError:
        return None


def _manifest_bits(repo: Path) -> tuple[Path | None, list[str]]:
    path = repo / "qa" / "manifest.yml"
    if not path.exists():
        return None, []
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ledger = doc.get("ledger")
    return (repo / ledger if ledger else None), [str(p) for p in (doc.get("people") or [])]


def _arg(argv: list[str], flag: str, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def run(argv: list[str], *, today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    repo = Path(_arg(argv, "--repo", ".")).resolve()
    ledger, people = _manifest_bits(repo)
    ledger = Path(_arg(argv, "--ledger", ledger)) if (_arg(argv, "--ledger") or ledger) else None
    days = int(_arg(argv, "--days", 30))
    bench = _arg(argv, "--benchmark")
    out: dict = {"source": None}
    if bench:
        rows = benchmark_rows(Path(bench))
        out["source"] = str(bench)
        # A benchmark is a corpus, not a recent window: every row must classify,
        # however old. Under the ledger's 30-day window the oldest rows would
        # drop out of the unclassified check as the file aged, and the command
        # would read 0 unclassified having looked at nothing (robustness review).
        dates = [d for d in (_date(r) for r in rows) if d]
        days = max(days, (today - min(dates)).days + 1) if dates else days
    elif ledger and ledger.exists():
        rows = ledger_rows(ledger.read_text(encoding="utf-8"))
        out["source"] = str(ledger)
    else:
        print(f"no ledger: {'qa/manifest.yml names none' if ledger is None else f'{ledger} is missing'} — nothing measured (exit 3)", file=sys.stderr)
        return 3
    if not rows:
        print(f"{out['source']} parsed to zero rows — nothing measured (exit 3, never read as a pass)", file=sys.stderr)
        return 3
    red = []
    for d in (7, days):
        out[f"{d}d"] = defect_escape_rate(rows, today=today, days=d, people=people)
    unc = out[f"{days}d"]["unclassified"]
    if unc:
        red.append(f"{len(unc)} finder(s) match neither vocabulary — add the phrasing to `people:` in qa/manifest.yml "
                   f"or to qabench.escapes: " + "; ".join(unc[:5]))
    out["triggers"] = trigger_histogram(rows)
    if out["triggers"]["unknown"]:
        red.append("trigger(s) outside the ODC vocabulary: " + ", ".join(out["triggers"]["unknown"]))
    if bench:
        out["shapes"] = dict(Counter(r.get("shape", "?") for r in rows).most_common())
    if "--json" in argv:
        print(json.dumps({**out, "red": red}, indent=1, ensure_ascii=False))
    else:
        print(f"DEFECT ESCAPE RATE — {out['source']} ({len(rows)} rows; a person met it in production ÷ all defects; target under 10 %)")
        for d in (7, days):
            r = out[f"{d}d"]
            pct = "n/a" if r["rate"] is None else f"{r['rate'] * 100:.0f} %"
            print(f"  last {d:3} days: {pct:>5}   customer {r['customer']:3}  internal {r['internal']:3}  total {r['total']:3}")
        t = out["triggers"]
        print(f"ODC TRIGGERS — what exposed the escapes ({t['untagged']} rows untagged)")
        for k, n in t["triggers"].items():
            print(f"  {n:4}  {k}")
        if bench:
            print("SHAPES")
            for k, n in out["shapes"].items():
                print(f"  {n:4}  {k}  {SHAPES.get(k, '')}")
        for line in red:
            print("RED  " + line)
    return 1 if red else 0
