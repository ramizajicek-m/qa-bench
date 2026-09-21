"""elements — counting a class NAME counts its mentions, not its instances.

    python -m qabench elements CLASS [--repo DIR] [--glob 'templates/**/*.html'] [--json]

A class name lives in its own CSS rule, in the JS that toggles it, and in prose
about it. anat-qa counted `.sticky-head` by grep (16) and by element (12) one
morning, wrote the distinction down, and eight hours later counted tab sets the
grep way, reported two where fleet.html has one, and used it to contradict
another session's corrected row — a contradiction manufactured by the
measurement, holding two rows from landing. Knowing a shape and being reliable
about it are different properties; a one-line check that runs every time beats
a lesson learned twice.

So this prints BOTH numbers for a class: ELEMENTS that carry it (parsed markup,
Jinja neutralised the way `gestures` does it, so `class="a {{ x }} b"` still
yields a and b) and raw MENTIONS of the name in the same files. A population
keyed on a class uses the element count; the gap is the noise, and printing it
is the only warning a grep ever gives.

Exit: 0 read · 3 no file matched.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .gestures import neutralise_jinja


def _tag_pattern(cls: str) -> re.Pattern:
    return re.compile(r"<[A-Za-z][\w-]*\b[^<>]*?\bclass\s*=\s*([\"'])(?:(?!\1).)*?(?<![\w-])"
                      + re.escape(cls) + r"(?![\w-])(?:(?!\1).)*\1", re.S)


def count(text: str, cls: str) -> tuple[int, int]:
    """(elements carrying the class, raw mentions of the name).

    An element is ANY tag whose class attribute carries the name, wherever the tag is written — in the
    markup or in a JS string that builds markup (`'<table class="settings-table sticky-head">'`). The first
    version used an HTML parser, which skips script content and stopped partway through a 15,000-line
    template: it found 3 of anat's sticky-head tables where the markup holds 12 — the instrument missing
    exactly the script-built elements a load-time sweep misses. Jinja is neutralised first, so
    `class="{{ theme }} sticky-head"` still counts."""
    src = neutralise_jinja(text)
    elements = len(_tag_pattern(cls).findall(src))
    mentions = len(re.findall(rf"(?<![\w-]){re.escape(cls)}(?![\w-])", text))
    return elements, mentions


def run(argv: list[str], *, echo=print) -> int:
    if not argv or argv[0].startswith("-"):
        print("usage: python -m qabench elements CLASS [--repo DIR] [--glob PATTERN]", file=sys.stderr)
        return 3
    cls = argv[0].lstrip(".")
    root = Path(argv[argv.index("--repo") + 1] if "--repo" in argv else ".").resolve()
    pattern = argv[argv.index("--glob") + 1] if "--glob" in argv else "**/*.html"
    files = [f for f in root.glob(pattern) if f.is_file() and "node_modules" not in f.parts]
    if not files:
        print(f"elements: {pattern} matched no files under {root} (exit 3)", file=sys.stderr)
        return 3
    rows = []
    for f in sorted(files):
        e, m = count(f.read_text(encoding="utf-8", errors="replace"), cls)
        if e or m:
            rows.append({"file": str(f.relative_to(root)), "elements": e, "mentions": m})
    te, tm = sum(r["elements"] for r in rows), sum(r["mentions"] for r in rows)
    if "--json" in argv:
        echo(json.dumps({"class": cls, "elements": te, "mentions": tm, "files": rows}, indent=1))
    else:
        echo(f"elements: .{cls} — {te} ELEMENT(S) carry it; the name is MENTIONED {tm} time(s) in {len(rows)} file(s)"
             + (f" — a grep would have said {tm}" if tm != te else ""))
        for r in rows:
            if r["elements"] != r["mentions"]:
                echo(f"  {r['file']}: {r['elements']} element(s), {r['mentions']} mention(s)")
    return 0
