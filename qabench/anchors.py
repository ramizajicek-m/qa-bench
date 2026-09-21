"""anchors — a reason citing code must still point at what it says it points at.

    python -m qabench anchors [--repo DIR] [--show] [--json] [--advisory]

WHY. Prose drifts while every test around it stays green, because prose is not
asserted against. Three instances in one day, three repos:

  * anat GEN-01 was `absent` on two concrete grounds — "material_catalog.html:261
    writes a status string into a div" and "no admin screen returns to a list".
    Line 261 had since become a toast call and the second was refuted by another
    row's own evidence. Both grounds false, status unchanged, nothing noticed.
  * tharros D12: a comment in site.css and another in a test both said the
    printed documents use `break-inside: avoid`. Zero occurrences in all four.
  * tharros callback.js: a comment claimed the server's reason is shown; the code
    fell back to a generic "failed".

The general case — does this sentence still describe the code — is semantic, and
this does not pretend to decide it. What IS mechanical is the slice where prose
names a place in the code, and that is what this reads, in every file the
manifest lists (trackers, docs, and source files for their comments):

  1. A CONTENT ANCHOR, `path#"literal"`, must resolve: the file exists and
     contains the literal. This is the form to write. It survives the file
     growing, and it fails the day the thing it names goes away — which is the
     day every sentence resting on it becomes false.
  2. A LINE CITATION, `path.ext:LINE`, is a coordinate that moves independently
     of the claim (`qabench.warrant` refuses it in `evidence:`; this carries the
     rule to prose). Each is resolved and checked: a file that does not exist, or
     a line past its end, is red. When the same line of prose quotes code in
     backticks, that code must still appear within three lines of the cited one,
     or the citation has DRIFTED — that is GEN-01's shape when the author quoted.
     The rest are counted against a pinned ceiling that may only fall: the count
     is printed every run, and an unpinned repo is told the number to pin.

WHAT IT CANNOT SEE, stated: a citation whose words are wrong about a line that
still exists and quotes nothing. `--show` prints every citation beside the
line it now points at, so a person can read them all in one pass; reading is
the only check for that half.

Exit: 0 every anchor resolves, no drift, count at or under the pin · 1 otherwise
· 3 no `anchors:` block, or it matched no files.

Manifest:

    anchors:
      prose: ["docs/ui-standard.md", "qa/*.yml", "static/**/*.js", "app/**/*.py"]
      exclude: ["tests/fixtures/**"]   # files whose paths are made up on purpose
      max_line_citations: 41     # measured 2026-09-21; may only fall
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

EXT = r"(?:py|js|mjs|ts|tsx|jsx|html|jinja2?|css|scss|ya?ml|sql|md|sh|toml|json)"
CONTENT = re.compile(r"""([\w./-]+\.""" + EXT + r""")#"([^"\n]{1,200})\"""")
LINE = re.compile(r"([\w./-]*[\w-]\." + EXT + r"):(\d{1,6})(?![\d:])")
QUOTED = re.compile(r"`([^`\n]{3,80})`")
NEAR = 3


def _files(root: Path) -> list[str]:
    try:
        p = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, timeout=60)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        pass
    skip = {".git", "node_modules", ".venv", "__pycache__"}
    return [str(f.relative_to(root)) for f in root.rglob("*") if f.is_file() and not skip & set(f.parts)]


def resolve(cited: str, files: list[str]) -> tuple[str | None, str]:
    """(repo path, "") or (None, why)."""
    cited = cited.lstrip("./")
    if cited in files:
        return cited, ""
    hits = [f for f in files if f.endswith("/" + cited)]
    if len(hits) == 1:
        return hits[0], ""
    return None, ("ambiguous: " + ", ".join(hits[:4])) if hits else "no such file"


def _read(root: Path, rel: str) -> list[str]:
    try:
        return (root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def scan(root: Path, cfg: dict) -> dict:
    files = _files(root)
    excluded = {str(p.relative_to(root)) for pat in cfg.get("exclude") or [] for p in root.glob(pat)}
    prose = sorted({f for pat in cfg.get("prose") or [] for f in
                    (str(p.relative_to(root)) for p in root.glob(pat) if p.is_file())} - excluded)
    out = {"files": len(prose), "content": [], "citations": [], "unresolved": [], "red": []}
    for src in prose:
        for n, text in enumerate(_read(root, src), 1):
            where = f"{src}:{n}"
            for path, literal in CONTENT.findall(text):
                rel, why = resolve(path, files)
                ok = bool(rel) and literal in "\n".join(_read(root, rel))
                out["content"].append({"at": where, "path": path, "literal": literal, "ok": ok})
                if not ok:
                    out["red"].append(f"{where}: anchor {path}#\"{literal}\" — "
                                      + (why if not rel else "the file no longer contains it") +
                                      ". Every sentence resting on it is now unsupported")
            for m in LINE.finditer(text):
                path, num = m.group(1), m.group(2)
                rel, why = resolve(path, files)
                c = {"at": where, "cited": f"{path}:{num}", "now": None}
                out["citations"].append(c)
                if not rel:
                    # Red only when the path claims to be in THIS repo: its first directory exists here.
                    # A bare `intakeService.ts:302` in a port cites the codebase it came from, which this
                    # cannot read — counted as unresolved, never as drift.
                    top = path.lstrip("./").split("/")[0]
                    if why == "no such file" and "/" in path.lstrip("./") and (root / top).is_dir():
                        out["red"].append(f"{where}: cites {path}:{num} — no such file; a reason citing a file "
                                          "that has gone is a reason nobody has read since it went")
                    else:
                        out["unresolved"].append(f"{where}: {path}:{num} ({why})")
                    continue
                lines = _read(root, rel)
                i = int(num)
                if i < 1 or i > len(lines):
                    out["red"].append(f"{where}: cites {path}:{num} — the file has {len(lines)} lines")
                    continue
                c["now"] = lines[i - 1].strip()[:160]
                window = "\n".join(lines[max(0, i - 1 - NEAR): i + NEAR])
                # Only the code quoted IMMEDIATELY after the citation is what the citation is about: a
                # backtick three clauses later is about something else (the first estate run read every
                # backtick on the line and called 1441 citations drifted, almost none of them real).
                after = text[m.end():]
                if text[:m.start()].count("`") % 2:  # the citation sits inside a code span: leave it first
                    close = after.find("`")
                    after = after[close + 1:] if close >= 0 else ""
                q = QUOTED.search(re.split(r"\. |; | — | \| |, and |\)", after)[0][:80])
                q = q.group(1) if q else None
                # Code, not prose between two spans: no edge spaces, not a bare `:208` range or a sha.
                if (q and q == q.strip() and not LINE.search(q) and path not in q
                        and not re.fullmatch(r":?\d+(?:[-–]\d+)?|[0-9a-f]{7,40}\^?", q)):
                    if q not in window:
                        out["red"].append(f"{where}: cites {path}:{num} beside `{q}`, which is not within {NEAR} "
                                          f"lines of it — the citation has DRIFTED (line {num} now reads "
                                          f"{c['now']!r}). Rewrite it as {path}#\"<literal>\"")
    return out


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default


def run(argv: list[str], *, echo=print) -> int:
    root = Path(_arg(argv, "--repo", ".")).resolve()
    mpath = root / "qa" / "manifest.yml"
    try:
        doc = (yaml.safe_load(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}) or {}
    except (OSError, yaml.YAMLError) as ex:
        print(f"anchors: cannot read {mpath}: {ex} (exit 3)", file=sys.stderr)
        return 3
    cfg = doc.get("anchors")
    if not cfg or not cfg.get("prose"):
        print(f"no `anchors:` block with `prose:` in {mpath} — no prose that cites code is checked (exit 3)",
              file=sys.stderr)
        return 3
    out = scan(root, cfg)
    if not out["files"]:
        print(f"anchors: `prose:` matched no files — nothing was read (exit 3)", file=sys.stderr)
        return 3
    n, pin = len(out["citations"]), cfg.get("max_line_citations")
    if not isinstance(pin, int):
        out["red"].append(f"`max_line_citations` is not pinned. {n} line citation(s) today; pin {n} and let it "
                          "only fall — each one converted to path#\"literal\" is one that can fail when it drifts")
    elif n > pin:
        out["red"].append(f"{n} line citations, pin {pin}: new prose cites a line number. Write path#\"literal\" "
                          "instead — a coordinate moves while the claim does not")
    if "--json" in argv:
        echo(json.dumps(out, indent=1, ensure_ascii=False))
    else:
        ok = sum(c["ok"] for c in out["content"])
        echo(f"anchors: {out['files']} file(s) read · {ok}/{len(out['content'])} content anchors resolve · "
             f"{n} line citation(s), pin {pin}")
        for r in out["red"]:
            echo(f"  RED  {r}")
        if "--show" in argv:
            for c in out["citations"]:
                echo(f"  {c['at']}  {c['cited']}  now: {c['now']!r}")
    # --advisory is the adoption step: print everything, exit 0, until the day-one drift is cleared.
    return 1 if out["red"] and "--advisory" not in argv else 0
