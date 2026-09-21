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


def greps(text: str, cls: str) -> tuple[int, int]:
    """(raw substring hits — `grep -o`, matching lines — `grep -c`), the two numbers a person actually types.

    THREE numbers answered one question on 2026-09-21: anat-qa measured 16 sticky-head "mentions", this
    tool said 13, and `grep -c` gives neither. 16 counts the substring inside `sticky-heading.js` and
    `client-sticky-header`; 13 counts the name as a whole token; lines count two on one line once. A
    count carries its definition on the same line, so all of them are printed, each named."""
    return text.count(cls), sum(1 for ln in text.splitlines() if cls in ln)


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


_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_MEDIA = re.compile(r"@media[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}")
_OPACITY0 = re.compile(r"(?<![\w-])opacity\s*:\s*0(?:\.0+)?\s*(?:;|!|$)")


def hidden_until_script(css: str) -> set[str]:
    """Classes whose BASE rule sets opacity 0 — invisible until something un-hides them.

    tharros: `.rv { opacity: 0 }` is unconditional and only JS adds `.in`; 49 sections on six customer
    templates, including the door handover card on /track, are chrome plus invisible content with
    scripts off or failed. The STA-07 evidence measured text PRESENCE (source, and Playwright inner_text,
    which counts opacity-0 text) — what is in the DOM, not what is painted. Only the base rule counts:
    a rule inside @media (reduced motion) or scoped by a parent selector is a condition, not the default.
    Comments are stripped first: the first version kept the comment above `.rv` in its selector and
    found nothing on the very case it was built for. opacity only — `display:none` is the ordinary,
    legitimate default of a modal, and flagging it would bury the finding."""
    css = _MEDIA.sub("", _COMMENT.sub("", css))
    out = set()
    for sel, body in re.findall(r"([^{}@]+)\{([^{}]*)\}", css):
        if _OPACITY0.search(body):
            for one in sel.split(","):
                one = one.strip()
                if re.fullmatch(r"\.[\w-]+", one):
                    out.add(one[1:])
    return out


def run(argv: list[str], *, echo=print) -> int:
    if "--hidden-by-default" in argv:
        root = Path(argv[argv.index("--repo") + 1] if "--repo" in argv else ".").resolve()
        css_files = [f for f in list(root.glob("static/**/*.css")) + list(root.glob("web/src/**/*.css"))
                     if "node_modules" not in f.parts]
        tpl = [f for f in root.glob("templates/**/*.html") if f.is_file()]
        css = "\n".join(f.read_text(encoding="utf-8", errors="replace") for f in css_files)
        css += "\n".join(m for f in tpl for m in re.findall(r"<style[^>]*>(.*?)</style>",
                                                             f.read_text(encoding="utf-8", errors="replace"), re.S))
        if not css_files and not tpl:
            print("elements: no stylesheet or template found — nothing read (exit 3)", file=sys.stderr)
            return 3
        found = []
        for cls in sorted(hidden_until_script(css)):
            per = [(str(f.relative_to(root)), count(f.read_text(encoding="utf-8", errors="replace"), cls)[0]) for f in tpl]
            per = [x for x in per if x[1]]
            if per:
                found.append((cls, sum(n for _, n in per), per))
        echo(f"elements: {len(found)} class(es) whose base rule is opacity 0 and that sit on elements — invisible "
             "until a script reveals them; measure each page with JS off by COMPUTED visibility, not by text presence")
        for cls, n, per in found:
            echo(f"  .{cls}: {n} element(s) in {len(per)} template(s): " + ", ".join(f"{f} ({k})" for f, k in per[:6]))
        # Report-only: measured across the estate, tharros's .rv (49 elements, 6 templates) is the finding and
        # the rest are single hover/state reveals (a save badge, a submenu, keyboard hints). --strict to gate.
        return 1 if found and "--strict" in argv else 0

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
        text = f.read_text(encoding="utf-8", errors="replace")
        e, m = count(text, cls)
        raw, lines = greps(text, cls)
        if e or m or raw:
            rows.append({"file": str(f.relative_to(root)), "elements": e, "mentions": m, "substring": raw, "lines": lines})
    te, tm = sum(r["elements"] for r in rows), sum(r["mentions"] for r in rows)
    tr, tl = sum(r["substring"] for r in rows), sum(r["lines"] for r in rows)
    if "--json" in argv:
        echo(json.dumps({"class": cls, "elements": te, "mentions": tm, "substring": tr, "lines": tl, "files": rows},
                        indent=1))
    else:
        echo(f"elements: .{cls} under {pattern} — {te} ELEMENT(S) carry it (the population); the name as a whole "
             f"token is MENTIONED {tm} time(s); `grep -o` would say {tr} (substring, e.g. inside longer names); "
             f"`grep -c` would say {tl} (lines) — in {len(rows)} file(s)")
        for r in rows:
            if len({r["elements"], r["mentions"], r["substring"]}) > 1:
                echo(f"  {r['file']}: {r['elements']} element(s), {r['mentions']} whole-name, {r['substring']} substring")
    return 0
