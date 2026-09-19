"""requirements — the questions asked of the requester BEFORE a surface is built, and a check that they were.

    python -m qabench questions print scan      # the list to put to the requester, for these kinds
    python -m qabench asked                      # qa/requirements.yml: every surface's questions answered or owned
    python -m qabench asked --json

WHY. Blind-coded, 18 of the 121 defects people found in ana-log had one cheapest
catcher: asking the requester, or watching them work, before building (§9 of
docs/methodology.md). An independent seam analysis on 8200-platform missed 14 of
31 for the same reason (§10). No test reaches it — the answer is in a person —
so the mechanism is not a test of the product but a check that the question was
ASKED, of whom, when, and what they said: the printer's paper size AND
orientation, what the label must say, which symbology is already stuck on ten
thousand pallets, whether a rule we fitted to data is the owner's rule.

qa/requirements.yml, one entry per surface:

    surfaces:
      pallet-label:
        kinds: [print, scan]
        where: [app/services/documents.py, web/src/pages/Labels.tsx]   # the files that ARE the surface
        asked_of: Israel (warehouse manager)
        asked_on: 2026-09-16
        answers:
          printer: ZDesigner ZD421, driver default
          orientation: landscape, 100×150 roll       # a person's words, not ours
        open:
          per-sheet: {owner: Rami, review_by: 2026-09-30}

Judged: every question of `always` and of each kind is either answered or open
with an owner and a review date; an open question past its date is red; an
answer with no `asked_of`/`asked_on` is red; an answer that is an assumption
("assumed", "probably", "we think", "TBD") is red — that is how a default
nobody confirmed came to read like a fact. With `--changed-since`, a file
changed in the window that sits under no surface's `where:` is listed: a new
surface nobody asked about.

Exit 0 all answered or owned · 1 a gap · 3 no register (nothing to judge).
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from importlib import resources
from pathlib import Path

import yaml

_ASSUMED = re.compile(r"\b(assum\w*|probably|we think|i think|tbd|todo|guess\w*|unknown|\?\?)\b|^\s*\?\s*$", re.I)


def pack() -> dict:
    return yaml.safe_load(resources.files("qabench.packs").joinpath("questions.yml").read_text(encoding="utf-8"))


def questions_for(kinds: list[str], p: dict | None = None) -> list[dict]:
    p = p or pack()
    unknown = [k for k in kinds if k not in p["kinds"]]
    if unknown:
        raise SystemExit(f"unknown surface kind(s) {unknown}; one of {sorted(p['kinds'])}")
    out, seen = [], set()
    for q in [*p["always"], *(q for k in kinds for q in p["kinds"][k])]:
        if q["id"] not in seen:
            seen.add(q["id"])
            out.append(q)
    return out


def judge(register: dict, today: dt.date, p: dict | None = None) -> list[dict]:
    """[{surface, problem}] — [] when every surface's questions are answered or owned."""
    p = p or pack()
    red = []
    for name, s in sorted((register.get("surfaces") or {}).items()):
        kinds = s.get("kinds") or []
        try:
            qs = questions_for(kinds, p)
        except SystemExit as e:
            red.append({"surface": name, "problem": str(e)})
            continue
        answers, open_ = s.get("answers") or {}, s.get("open") or {}
        if answers and not (s.get("asked_of") and s.get("asked_on")):
            red.append({"surface": name, "problem": "answers with no asked_of / asked_on — whose words are these?"})
        for q in qs:
            a = answers.get(q["id"])
            if a is not None and str(a).strip():
                if _ASSUMED.search(str(a)):
                    red.append({"surface": name, "problem": f"{q['id']}: {str(a)[:60]!r} is an assumption, not an answer — ask, or move it to open"})
                continue
            o = open_.get(q["id"])
            if not o:
                red.append({"surface": name, "problem": f"{q['id']} not asked: {q['q']}"})
                continue
            if not (isinstance(o, dict) and o.get("owner") and o.get("review_by")):
                red.append({"surface": name, "problem": f"{q['id']} open with no owner and review_by"})
                continue
            try:
                if dt.date.fromisoformat(str(o["review_by"])) < today:
                    red.append({"surface": name, "problem": f"{q['id']} open past {o['review_by']} (owner {o['owner']})"})
            except ValueError:
                red.append({"surface": name, "problem": f"{q['id']} review_by {o['review_by']!r} is not a date"})
    return red


def uncovered(root: Path, register: dict, since: str, globs: list[str]) -> list[str]:
    """Files changed in the window, matching the surface globs, under no surface's `where:`."""
    try:
        out = subprocess.run(["git", "-C", str(root), "log", f"--since={since}", "--name-only", "--pretty=format:"],
                             capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    changed = {l.strip() for l in out.splitlines() if l.strip()}
    covered = {str(w) for s in (register.get("surfaces") or {}).values() for w in (s.get("where") or [])}
    surf = {f for f in changed if any(Path(f).match(g) for g in globs) and (root / f).exists()}
    return sorted(f for f in surf if not any(f == c or f.startswith(c.rstrip("/") + "/") for c in covered))


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def run_questions(argv: list[str]) -> int:
    kinds = [a for a in argv if not a.startswith("-")]
    p = pack()
    if not kinds:
        print("kinds: " + ", ".join(sorted(p["kinds"])))
        return 0
    for q in questions_for(kinds, p):
        print(f"- [{q['id']}] {q['q']}")
    return 0


def run_asked(argv: list[str], *, today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    root = Path(_arg(argv, "--repo", ".")).resolve()
    reg_path = root / "qa" / "requirements.yml"
    if not reg_path.exists():
        print(f"no {reg_path} — nothing judged (exit 3). `python -m qabench questions <kind>` prints what to ask.",
              file=sys.stderr)
        return 3
    register = yaml.safe_load(reg_path.read_text(encoding="utf-8")) or {}
    red = judge(register, today)
    since = _arg(argv, "--changed-since")
    new = uncovered(root, register, since, register.get("surface_globs") or []) if since else []
    n = len(register.get("surfaces") or {})
    if "--json" in argv:
        print(json.dumps({"surfaces": n, "red": red, "unasked_new_files": new}, indent=1, ensure_ascii=False))
    else:
        print(f"REQUIREMENTS — {n} surfaces in {reg_path.name}; {len(red)} gap(s)"
              + (f"; {len(new)} changed surface file(s) under no surface" if since else ""))
        for r in red:
            print(f"  RED  {r['surface']:24} {r['problem']}")
        for f in new:
            print(f"  NEW  {f} — which surface is this, and was its requester asked?")
    if not n:
        return 3
    return 1 if (red or new) else 0
