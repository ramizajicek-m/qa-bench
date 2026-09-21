r"""fixpop — a fix that cannot name its population has not finished.

    python -m qabench fixpop --msg .git/COMMIT_EDITMSG        # as a commit-msg hook
    python -m qabench fixpop --range origin/main..HEAD        # in CI, over what is being pushed
    python -m qabench fixpop ... --advisory                   # print, exit 0 — the adoption step

WHY. In July a tester reported that a labour tier picked by hand on anat's
service-call intake was overwritten when the address changed. It was fixed
properly, with her name in the comment. The FEE field beside it, prefilled by
the same kind of function from the same inputs, had the identical defect and sat
for two months. Nothing was wrong with the fix. Nobody asked the one-grep
question — which other sites have this shape? — and every repo in the estate
already had a rule saying to ask it. A rule in a file is not a guard.

So a fix commit carries a trailer naming its population, the same way the
escaped-defects rule names the layer that should have caught it:

    Population: order_form fee, intake fee (fixed); quote tier (already guarded)
    Population: none (searched: rg "\.value = .*catalog" static/ templates/)

`none` is accepted only with `searched:` and the search itself, because a bare
"none" is the claim this exists to stop. "n/a", "-", "tbd" and the like are
refused.

WHAT IS A FIX: the subject matches `fix_subject` (default: a conventional
`fix:` / `fix(scope):` / `hotfix:` prefix, or a subject starting "Fix "). That is
a CONVENTION standing in for the property, which this kit otherwise refuses —
there is no other signal in a commit — so its limit is stated: a fix whose
subject does not say so escapes. A project that wants no escape sets
`require_all: true` and every non-merge commit must carry the trailer.

Exit: 0 every fix names its population · 1 one does not · 3 no message or
unreadable git.

Manifest (optional): fixpop: {fix_subject: "<regex>", require_all: false}
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

DEFAULT_FIX = r"^(?:(?:fix|hotfix|bugfix)(?:\([^)]*\))?!?:|Fix\b|Fixes\b)"
TRAILER = re.compile(r"^Population:[ \t]*(.*)$", re.I | re.M)
EMPTY = re.compile(r"^(?:|n/?a|none\.?|-+|tbd|todo|\?+|nothing|same|see above)$", re.I)
SEARCHED = re.compile(r"searched:\s*(.+)", re.I)


def judge_message(msg: str, *, fix_subject: str = DEFAULT_FIX, require_all: bool = False) -> str:
    """"" when the message is acceptable, else why not."""
    lines = [ln for ln in msg.splitlines() if not ln.startswith("#")]
    subject = next((ln for ln in lines if ln.strip()), "")
    if subject.startswith("Merge ") or subject.startswith("Revert "):
        return ""
    if not require_all and not re.search(fix_subject, subject):
        return ""
    found = TRAILER.findall("\n".join(lines))
    if not found:
        return (f"fix commit {subject[:70]!r} does not name its population. Add a trailer — "
                "`Population: <other sites with this shape> (fixed)` or `Population: none (searched: <how>)`. "
                "anat fixed a hand-picked tier being overwritten and left the fee field beside it with the same "
                "defect for two months, because nobody asked which other sites had the shape")
    text = found[-1].strip()
    if EMPTY.match(text):
        return (f"`Population: {text}` names nothing. Name the other sites, or write "
                "`none (searched: <the search you ran>)` — a bare none is the claim this exists to stop")
    if re.match(r"^none\b", text, re.I):
        how = SEARCHED.search(text)
        if not how or len(how.group(1).strip(" )")) < 6:
            return (f"`Population: {text}` says none without the search. Write `none (searched: <how>)` — "
                    "the search is what makes none a finding rather than an assumption")
    return ""


def _cfg(root: Path) -> dict:
    m = root / "qa" / "manifest.yml"
    try:
        doc = yaml.safe_load(m.read_text(encoding="utf-8")) if m.exists() else {}
    except (OSError, yaml.YAMLError):
        doc = {}
    return (doc or {}).get("fixpop") or {}


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default


def run(argv: list[str], *, echo=print) -> int:
    root = Path(_arg(argv, "--repo", ".")).resolve()
    cfg = _cfg(root)
    kw = {"fix_subject": cfg.get("fix_subject") or DEFAULT_FIX, "require_all": bool(cfg.get("require_all"))}
    advisory = "--advisory" in argv
    msgs: list[tuple[str, str]] = []
    if _arg(argv, "--msg"):
        try:
            msgs.append(("commit", Path(_arg(argv, "--msg")).read_text(encoding="utf-8")))
        except OSError as ex:
            print(f"fixpop: cannot read {_arg(argv, '--msg')}: {ex} (exit 3)", file=sys.stderr)
            return 3
    elif _arg(argv, "--range"):
        try:
            p = subprocess.run(["git", "log", "--format=%H%x00%B%x1e", _arg(argv, "--range")],
                               cwd=root, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError) as ex:
            print(f"fixpop: git could not run: {ex} (exit 3)", file=sys.stderr)
            return 3
        if p.returncode != 0:
            print(f"fixpop: git log {_arg(argv, '--range')} failed: {p.stderr.strip()[:200]} (exit 3)", file=sys.stderr)
            return 3
        for rec in p.stdout.split("\x1e"):
            if "\x00" in rec:
                sha, body = rec.strip("\n").split("\x00", 1)
                msgs.append((sha[:9], body))
    else:
        print("usage: python -m qabench fixpop (--msg FILE | --range A..B) [--advisory]", file=sys.stderr)
        return 3
    bad = [(ref, why) for ref, body in msgs if (why := judge_message(body, **kw))]
    for ref, why in bad:
        echo(f"  {ref}  {why}")
    echo(f"fixpop: {len(msgs)} commit(s) read, {len(bad)} fix(es) without a population"
         + (" — advisory, not failing" if advisory and bad else ""))
    return 0 if advisory or not bad else 1
