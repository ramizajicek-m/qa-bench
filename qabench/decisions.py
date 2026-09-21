"""decisions — a ruling that names its own falsifier can be guarded; one that does not, cannot.

    python -m qabench decisions [--repo DIR] [--strict] [--json]

Reads `qa/decisions.yml` (C3, the decision register every project keeps) and
reports each decision that does not say what observation would prove it WRONG,
in a `falsified_by:` field.

WHY. anat's NAV-08 ruled that two sidebar marks — "this page" and "this section
contains it" — may share a tint, and the ruling carried one more sentence: "if
the two styles cannot be made visually distinct at a glance, the ruling is wrong
and should come back." That sentence is why the guard that covers it is good: it
reads computed style on a real page and asserts strong != soft and soft !=
plain — it MECHANISES THE FALSIFIER, where a guard written from the ruling's
conclusion would have checked that a class name is present, and passed on two
marks that render identically, which is the exact failure the ruling feared.

A ruling that says "X is acceptable" is unguardable; one that says "X is
acceptable, and here is the observation that would prove it wrong" hands the
next person a test. It costs one sentence when the judgement is made, while the
author still knows what would change their mind — the only time it is cheap.

The sibling rule from the same row, recorded rather than built because it has no
single artefact to read: WHICH PROPERTIES A COMPARISON READS IS A POPULATION
DECISION. The two marks were identical on backgroundColor, color and fontWeight
— a complete, correct, wrong measurement; they differ on a ::before bar and an
inset ring. Diff the full computed style and report what differs, never assert
equality over a hand-picked list.

Report-only by default: on 2026-09-21 no decision in the estate carried the
field (125 across six repos), and a check that is red on day one is switched off
within a week. `--strict` exits 1 on any decision without it, for a repo that
has adopted it.

Exit: 0 read (or strict and all carry it) · 1 strict and some do not · 3 no register.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

WEAK = ("n/a", "none", "-", "tbd", "todo", "nothing", "never")


def judge(entries: list) -> list[dict]:
    out = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        f = str(e.get("falsified_by") or "").strip()
        if not f or f.lower().rstrip(".") in WEAK or len(f.split()) < 4:
            out.append({"id": str(e.get("id", "?")), "rule": str(e.get("rule") or e.get("decision") or "")[:100],
                        "falsified_by": f})
    return out


def run(argv: list[str], *, echo=print) -> int:
    root = Path(argv[argv.index("--repo") + 1] if "--repo" in argv else ".").resolve()
    path = root / "qa" / "decisions.yml"
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as ex:
        print(f"decisions: cannot read {path}: {ex} (exit 3)", file=sys.stderr)
        return 3
    entries = doc.get("decisions", doc) if isinstance(doc, dict) else doc
    if isinstance(entries, dict):
        entries = [{"id": k, **(v if isinstance(v, dict) else {})} for k, v in entries.items()]
    if not isinstance(entries, list) or not entries:
        print(f"decisions: {path} holds no decisions (exit 3)", file=sys.stderr)
        return 3
    missing = judge(entries)
    if "--json" in argv:
        echo(json.dumps({"decisions": len(entries), "without_falsifier": missing}, ensure_ascii=False, indent=1))
    else:
        echo(f"decisions: {len(entries)} read · {len(missing)} do not say what would prove them wrong")
        for m in missing[:40]:
            echo(f"  {m['id']:14} {m['rule']}")
        if missing:
            echo("  add `falsified_by: <the observation that would show this ruling is wrong>` — the guard is that "
                 "observation, mechanised")
    return 1 if missing and "--strict" in argv else 0
