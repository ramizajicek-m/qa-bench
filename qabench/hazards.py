"""hazards — shell lines that make an observer report something it did not observe.

    python -m qabench hazards [--repo DIR] [--json]

Reads Makefiles, shell scripts and workflow files (or `hazards: {paths: [...]}`)
for two shapes, each of which reported a false outcome in this estate on
2026-09-21 and each of which the author had already named before writing it:

  SELF-MATCHING LIVENESS. anat rebuilt an orphaned waiter with "exit when the
  landing dies": `pgrep -f "scripts/land.py --batch …"`. The waiter's own command
  line contains that string, so pgrep matched THE WAITER, and "is the landing
  alive?" answered yes for as long as the waiter existed. A `pgrep -f` or
  `ps … | grep` whose pattern is not self-excluding (`[p]ython…`, `grep -v grep`)
  is refused.

  TRUNCATING THE ONLY COPY. `make land | tail -25` reported a failed gate as
  success (the pipeline's status is tail's), and ana-log piped a backgrounded
  pytest through `tail`, lost the failure detail, and did it again after naming
  it. A test or landing command piped into `head`/`tail` with no `tee` before it
  and no `pipefail` in the file is refused: write the full output to a file and
  read the summary from the file.

A line can be excused with a trailing `# hazard-ok: <reason>`; the reason is
printed every run. What this does NOT read, stated: two steps joined by a
newline where the second publishes what the first produced (ana-log's ledger
row whose script failed while its commit went ahead). That needs the script's
meaning, not its text, and `set -e` is the control.

Exit: 0 none · 1 some · 3 nothing to read.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

DEFAULT_PATHS = ["Makefile", "*.mk", "**/*.sh", ".github/workflows/*.yml", ".github/workflows/*.yaml"]
SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__"}
LIVENESS = re.compile(r"""\bpgrep\s+(?:-\w+\s+)*-\w*f\w*\s+(?:-\w+\s+)*(["']?)([^"'\s|;&)]+[^"'|;&)]*)\1"""
                      r"""|\bps\b[^|\n]*\|\s*grep\s+(?:-\w+\s+)*(["']?)([^"'\s|;&)]+)\3""")
RUNNER = re.compile(r"\b(?:pytest|playwright\s+test|vitest|jest|npm\s+(?:run\s+)?test|make\s+[\w-]*"
                    r"(?:test|land|full|tier|night|e2e|check)[\w-]*|qabench\s+(?:nightly|stage))\b")
TRUNC = re.compile(r"\|\s*(?:tail|head)\b")
OK = re.compile(r"#\s*hazard-ok:\s*(\S.*)$")


def _paths(root: Path, pats: list[str]) -> list[Path]:
    return sorted({p for pat in pats for p in root.glob(pat) if p.is_file() and not SKIP & set(p.parts)})


def scan(root: Path, pats: list[str]) -> dict:
    files = _paths(root, pats)
    out = {"files": len(files), "red": [], "excused": []}
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        pipefail = "pipefail" in text
        rel = f.relative_to(root)
        for n, line in enumerate(text.splitlines(), 1):
            code = line.split(" #", 1)[0] if not line.lstrip().startswith("#") else ""
            if not code.strip():
                continue
            found = []
            for m in LIVENESS.finditer(code):
                pat = m.group(2) or m.group(4) or ""
                if "[" in pat or re.search(r"grep\s+-v\s+grep", code):
                    continue
                found.append(f"liveness check `{m.group(0).strip()}` matches ITS OWN command line — use a "
                             "self-excluding pattern (`[p]ython.*land.py`) and assert the pid is the process you meant")
            t = TRUNC.search(code)
            r = RUNNER.search(code)
            if t and r and r.start() < t.start() and "tee" not in code[:t.start()] and not pipefail:
                found.append(f"`{code.strip()[:90]}` pipes a test/landing run into {t.group(0).strip('| ')} — the "
                             "exit status is the truncator's and the only copy of the output is cut. Write the full "
                             "output to a file (`… > run.log 2>&1; tail run.log`)")
            if not found:
                continue
            ok = OK.search(line)
            for why in found:
                (out["excused"] if ok else out["red"]).append(
                    f"{rel}:{n}: {why}" + (f" — EXCUSED: {ok.group(1)}" if ok else ""))
    return out


def run(argv: list[str], *, echo=print) -> int:
    root = Path(argv[argv.index("--repo") + 1] if "--repo" in argv else ".").resolve()
    m = root / "qa" / "manifest.yml"
    try:
        doc = (yaml.safe_load(m.read_text(encoding="utf-8")) if m.exists() else {}) or {}
    except (OSError, yaml.YAMLError):
        doc = {}
    pats = ((doc.get("hazards") or {}).get("paths")) or DEFAULT_PATHS
    out = scan(root, pats)
    if not out["files"]:
        print("hazards: no Makefile, shell script or workflow found — nothing read (exit 3)", file=sys.stderr)
        return 3
    if "--json" in argv:
        echo(json.dumps(out, indent=1, ensure_ascii=False))
    else:
        echo(f"hazards: {out['files']} file(s) read · {len(out['red'])} hazard(s) · {len(out['excused'])} excused")
        for r in out["red"]:
            echo(f"  RED  {r}")
        for r in out["excused"]:
            echo(f"  ok   {r}")
    return 1 if out["red"] else 0
