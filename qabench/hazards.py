"""hazards — shell lines that make an observer report something it did not observe.

    python -m qabench hazards [--repo DIR] [--json] [--advisory]

Reads Makefiles, shell scripts and workflow files (or `hazards: {paths: [...]}`)
for two shapes, each of which reported a false outcome in this estate on
2026-09-21 and each of which the author had already named before writing it:

  SELF-MATCHING LIVENESS. anat rebuilt an orphaned waiter with "exit when the
  landing dies": `pgrep -f "scripts/land.py --batch …"`. The waiter's own command
  line contains that string, so pgrep matched THE WAITER, and "is the landing
  alive?" answered yes for as long as the waiter existed. A `pgrep -f` or
  `ps … | grep` whose pattern is not self-excluding (`[p]ython…`, `grep -v grep`)
  is refused WHERE THE PATTERN CAN BE IN A PARENT'S COMMAND LINE: a Makefile
  recipe (make runs each line as `sh -c "<line>"`), or a line that itself runs
  `sh|bash|zsh -c`. A workflow step or a script file is executed from a file, so
  its own text is not on any command line and pgrep never matches itself — the
  first estate run flagged five such steps in anat, all innocent, which is why
  the scope is this narrow. `ps -p <pid>` names one process and is not a search.

  TRUNCATING THE ONLY COPY. `make land | tail -25` reported a failed gate as
  success (the pipeline's status is tail's), and ana-log piped a backgrounded
  pytest through `tail`, lost the failure detail, and did it again after naming
  it. A test or landing command piped into `head`/`tail` with no `tee` before it
  and no `pipefail` in the file is refused: write the full output to a file and
  read the summary from the file.

  A LATER PUSH KILLS A RUNNING VERDICT. A push-triggered workflow whose group
  is keyed on `github.ref` with `cancel-in-progress: true` cancels the RUNNING
  gate of the previous push, so under steady pushes no gate on that branch ever
  finishes (tharros's and iga's ci.yml until 2026-09-21). Refused.
  What is NOT refused, deliberately: a ref-keyed group that lets a newer PENDING
  run replace an older one. That is batching, which Rami chose on 2026-09-17
  («...it needs to merge with the other branch in the queue so when it is
  cleared both will go together»): the newer commit contains the older, and the
  older's deploy reads SKIPPED = shipped inside the next. This rule was first
  written to refuse that too, and was narrowed the same hour when ana-log's
  tests.yml turned out to hold the decision in writing. `cancel-in-progress` as
  an expression that excludes the deploy branch (`github.ref != 'refs/heads/main'`)
  is the shape to use.

  A SELF-HOSTED DOCKER JOB WHOSE GIT CANNOT READ ITS OWN CHECKOUT. actions/checkout
  marks the workspace safe only in a TEMPORARY global config; on a self-hosted
  Linux (Docker) runner whose workspace ownership differs, every later git call
  exits 128 and a git-backed test reads an EMPTY corpus — green or red at
  random (tharros's test_deploy_drift and iga's kit pin check, 2026-09-21).
  ana-log's tests.yml carried the fix (GIT_CONFIG_COUNT/KEY/VALUE naming
  safe.directory = github.workspace) and four siblings did not. A job on
  `[self-hosted, linux…]` that runs pytest or git without that env, at workflow
  or job level, is refused.

  A REPORT THAT TRUNCATES FROM THE LEFT DROPS THE IDENTIFIER AND KEEPS THE
  PREDICATE. anat's land.py printed a refusal's output as `r.stdout[-800:]`: the
  last 800 CHARACTERS, which begin mid-line, so the one line that mattered read
  `irect-use-of-jinja2.direct-use-of-jinja2: 0 -> 2` — the path and rule
  namespace gone, the delta kept. The count is the part you cannot act on; the
  filename is the part you can. A character tail of a command's output in a
  Python script (`.stdout[-N:]`, `.stderr[-N:]`) is refused: keep whole lines
  (`splitlines()[-N:]`), and elide the middle of a key, never its head.
  SCRIPTS, NOT TESTS, DELIBERATELY — do not "complete" this by extending it to
  tests/. A character tail in an assertion message (`assert rc == 0,
  p.stderr[-800:]`) loses the head of a traceback, but pytest still names the
  test and file; a tail in a script's REPORT loses the only identifier in the
  line. anat has 96 loose-shape sites across scripts/ and tests/ and 10 in
  scripts; the rule is "where the sliced output IS the finding, cut on line
  boundaries", and a check that flagged all 96 would be switched off in a week.

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

DEFAULT_PATHS = ["Makefile", "*.mk", "**/*.sh", ".github/workflows/*.yml", ".github/workflows/*.yaml",
                 "scripts/**/*.py", ".github/delivery-kit/*.py"]
SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__"}
LIVENESS = re.compile(r"""\bpgrep\s+(?:-\w+\s+)*-\w*f\w*\s+(?:-\w+\s+)*(["']?)([^"'\s|;&)]+[^"'|;&)]*)\1"""
                      r"""|\bps\b[^|\n]*\|\s*grep\s+(?:-\w+\s+)*(["']?)([^"'\s|;&)]+)\3""")
RUNNER = re.compile(r"\b(?:pytest|playwright\s+test|vitest|jest|npm\s+(?:run\s+)?test|make\s+[\w-]*"
                    r"(?:test|land|full|tier|night|e2e|check)[\w-]*|qabench\s+(?:nightly|stage))\b")
TRUNC = re.compile(r"\|\s*(?:tail|head)\b")
INLINE = re.compile(r"\b(?:sh|bash|zsh)\s+(?:-\w+\s+)*-\w*c\b")
PS_PID = re.compile(r"\bps\b[^|]*\s-\w*p\b")
CHAR_TAIL = re.compile(r"\.(?:stdout|stderr|output)\s*\[\s*-\s*\d+\s*:\s*\]")
OK = re.compile(r"#\s*hazard-ok:\s*(\S.*)$")


def _paths(root: Path, pats: list[str]) -> list[Path]:
    return sorted({p for pat in pats for p in root.glob(pat) if p.is_file() and not SKIP & set(p.parts)})


def _ref_keyed(path: Path, text: str) -> list[str]:
    """Push-triggered workflow concurrency groups keyed on the ref and not the sha."""
    if ".github/workflows/" not in str(path).replace("\\", "/"):
        return []
    try:
        doc = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return []
    on = doc.get("on", doc.get(True)) or {}
    if not ((isinstance(on, dict) and "push" in on) or on == "push" or (isinstance(on, list) and "push" in on)):
        return []
    groups = [("workflow", doc.get("concurrency"))] + [
        (f"job {n}", (j or {}).get("concurrency")) for n, j in (doc.get("jobs") or {}).items() if isinstance(j, dict)]
    out = []
    for where, c in groups:
        g = c.get("group") if isinstance(c, dict) else c
        cancels = isinstance(c, dict) and c.get("cancel-in-progress") is True
        if isinstance(g, str) and "github.ref" in g and "github.sha" not in g and cancels:
            out.append(f"{where}: concurrency group `{g}` with cancel-in-progress: true — a later push KILLS the "
                       "running gate of the previous one, and under steady pushes no gate finishes. Keep the batching "
                       "and protect the running verdict: cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}")
    return out


def _untrusted_git(path: Path, text: str) -> list[str]:
    if ".github/workflows/" not in str(path).replace("\\", "/"):
        return []
    try:
        doc = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return []

    def trusted(env) -> bool:
        env = env or {}
        return any(str(env.get(f"GIT_CONFIG_KEY_{i}", "")) == "safe.directory" for i in range(8))

    out = []
    for name, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        labels = job.get("runs-on")
        labels = [labels] if isinstance(labels, str) else labels or []
        low = [str(x).lower() for x in labels]
        if "self-hosted" not in low or "linux" not in low:
            continue
        runs = " ".join(str(st.get("run", "")) for st in job.get("steps") or [] if isinstance(st, dict))
        if not re.search(r"\bpytest\b|\bgit\s|qabench\s+(?:fixpop|anchors)|\bmake\s", runs):
            continue
        if trusted(doc.get("env")) or trusted(job.get("env")):
            continue
        out.append(f"job {name}: runs git-backed work on a self-hosted Linux runner without GIT_CONFIG "
                   "safe.directory = ${{ github.workspace }} — checkout's trust does not outlive its step, and git "
                   "then reads an EMPTY corpus at random")
    return out


def scan(root: Path, pats: list[str]) -> dict:
    files = _paths(root, pats)
    out = {"files": len(files), "red": [], "excused": []}
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        pipefail = "pipefail" in text
        for why in _ref_keyed(f, text) + _untrusted_git(f, text):
            (out["excused"] if "hazard-ok:" in text else out["red"]).append(f"{f.relative_to(root)}: {why}")
        recipe = f.name == "Makefile" or f.suffix == ".mk"
        rel = f.relative_to(root)
        if f.suffix == ".py":
            for n, line in enumerate(text.splitlines(), 1):
                m = CHAR_TAIL.search(line)
                if m and not OK.search(line):
                    out["red"].append(f"{rel}:{n}: `{m.group(0)}` keeps the last characters of an output, so its "
                                      "first line starts mid-way and loses the path at its head — keep whole lines")
            continue
        for n, line in enumerate(text.splitlines(), 1):
            code = line.split(" #", 1)[0] if not line.lstrip().startswith("#") else ""
            if not code.strip():
                continue
            found = []
            inline = recipe or bool(INLINE.search(code))
            for m in LIVENESS.finditer(code):
                pat = m.group(2) or m.group(4) or ""
                if not inline or "[" in pat or re.search(r"grep\s+-v\s+grep", code) or PS_PID.search(m.group(0)):
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
    return 1 if out["red"] and "--advisory" not in argv else 0
