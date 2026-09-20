"""Run a command against a temporarily mutated file, then put the file back
EXACTLY as it was — whether or not it was committed.

WHY THIS IS IN THE KIT. Every guard in this estate is supposed to be watched red
before it is believed, and the way to watch it is to break the code and run the
test. The obvious way to undo that is `git checkout -- <file>`, and that command
restores HEAD, not the working copy. When the thing you are testing is itself
uncommitted, the restore is a REVERT and it silently eats your work.

anat learned this on 2026-08-23 — two sessions in one evening, one of them twice,
the second time with a warning written into the command — and built
scripts/mutate.sh. eliad copied it. The other five repos and this kit never got
it, so anyone working across the estate hand-rolls `perl -pi` plus a checkout and
meets the same trap. It happened five times on 2026-09-13 in a single session, by
someone who had written the rule down and used the tool correctly four times
first. Care is not the control; the control is that the restore cannot read HEAD.

IT DOES NOT REFUSE A DIRTY TREE, and that was proposed and rejected on
2026-09-20. Working mid-edit is the case this tool exists for; a committed file
was never in danger. What it does instead is SAY SO when the target has
uncommitted changes, because the trap is not this command — it is the
`git checkout --` somebody types after it, out of habit. Two people did exactly
that the same day, in two sessions, each within the hour of writing or reading
the rule: one lost a fix, one lost an edit to a module whose own docstring says
this. The rule that works is the one already written down — commit the
checkpoint BEFORE mutating, never after — and a warning at the moment of the
mutation is where it can still be read.

    python -m qabench mutate <file> '<python expr over s>' -- <command...>
    python -m qabench mutate --record qa/mutations.json <file> '<expr>' -- <command...>
    python -m qabench mutate --replay qa/mutations.json

The expression returns the mutated text, e.g. 's.replace("== 2", "== 1", 1)'.
The command is arbitrary, so this serves a pytest repo and an `npm test` repo
alike. Exit code is the COMMAND's, so 0 means the mutation SURVIVED — your guard
cannot see it — and non-zero means a test caught it. Read it the right way round.

A RECORDED MUTATION CAN OUTLIVE THE CODE IT WAS RECORDED AGAINST, which is why
`--record` and `--replay` exist. A mutation was recorded for "the typed value is
still there" and watched red. Two days later, drafts written per keystroke and
restored on mount landed in the same product — so a remounted subtree now puts
the typing straight back, and applying THE SAME RECORDED MUTATION leaves all
four cases GREEN. The record still reads as evidence; it stopped being able to
fail. Nothing about re-reading the file shows this, and only re-running the
mutation does. So a mutation watched red once is a claim with an expiry nobody
tracks, and treating it as permanent evidence is exactly the "green means
nothing changed" error this kit exists to refuse.

`--replay` re-applies every recorded mutation and is RED when one that was
caught now survives, or when its expression no longer applies at all (a stale
anchor is a stale record, not a pass). The rule the repair generalises to: A
MUTATION MUST DISTINGUISH THE PROPERTY IT CLAIMS FROM A MECHANISM THAT MERELY
PRODUCES THE SAME OBSERVABLE. There, asserting that no restore banner appeared
separated SURVIVED from RESTORED, and the mutation went red on the crossing case
and green on the other — which is its real behaviour.

Its sibling, from the same row: a rotation fixture turned 390x844 into 844x390
while the client asks `max-width: 900` in all three places, so both ends sit on
the same side of every breakpoint and both cases would have passed with every
viewport listener deleted. A FIXTURE THAT VARIES A PARAMETER ACROSS NO THRESHOLD
IS NOT VARYING IT.

Two refusals, both earned:

  * an expression that changes nothing exits 2. A mutation that is a no-op
    proves nothing, and it reads exactly like a guard that failed to fire —
    eliad's battery reported ten dead guards that way, when the truth was that
    ten anchors had drifted and nothing had been mutated at all.

  * the bytecode is purged on restore. `cp -p` gives the restored file the
    backup's size and integer-second mtime; when a mutation is made and undone
    inside one second those match the MUTATED file, and Python's import cache
    accepts the stale .pyc — so the next run judges the mutant while the source
    reads clean. Three agents hit that on 2026-09-06/07 and each blamed the code
    first.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile


def _purge_bytecode(target: pathlib.Path) -> None:
    stem = target.stem
    for cache in target.parent.rglob("__pycache__"):
        for pyc in cache.glob(f"{stem}.*.pyc"):
            try:
                pyc.unlink()
            except OSError:
                pass


def _uncommitted(target: pathlib.Path) -> bool:
    """True when git says this file differs from the index or HEAD. A repo git
    cannot read is NOT reported as clean — the warning is cheap and the silence
    is what costs."""
    try:
        p = subprocess.run(["git", "status", "--porcelain", "--", str(target)],
                           cwd=target.parent, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return False
    return p.returncode != 0 or bool(p.stdout.strip())


def _record_path(argv: list[str], flag: str) -> pathlib.Path | None:
    return pathlib.Path(argv[argv.index(flag) + 1]) if flag in argv and len(argv) > argv.index(flag) + 1 else None


def _load(path: pathlib.Path) -> list[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("mutations", [])
    except (OSError, ValueError):
        return []


def replay(path: pathlib.Path, *, echo=print) -> int:
    """Re-run every recorded mutation. RED when one that was caught now survives.

    A record is a claim with an expiry: the product can grow a mechanism that
    produces the same observable the assertion was watching, and the mutation
    then cannot fail. Re-reading the file never shows that.
    """
    records = _load(path)
    if not records:
        echo(f"mutate --replay: no mutations recorded in {path} — nothing re-run (exit 3). This is the NORMAL "
             "state of a project that has never recorded one, not a configuration fault: REPLAY IS ONLY AS GOOD "
             "AS THE RECORD, and most projects do not have one. A repo with years of 'watched red' claims in "
             "docstrings and commit messages has dated assertions only a person can check — extracting them into "
             "a record is a real piece of work rather than a command, and until it is done there is no rate to "
             "quote, only the claims.")
        return 3
    stale, survived = [], []
    for r in records:
        code = main([r["file"], r["expr"], "--", *r["command"]])
        if code == 2:
            stale.append(r)
            echo(f"  STALE   {r['file']}  {r['expr']}  — the expression no longer applies; a stale anchor is a "
                 "stale record, not a pass")
        elif code == 0 and r.get("verdict") == "caught":
            survived.append(r)
            echo(f"  SURVIVED {r['file']}  {r['expr']}  — recorded as CAUGHT on {r.get('recorded')}, and today "
                 "nothing sees it. The record still reads as evidence and stopped being able to fail")
        else:
            echo(f"  ok      {r['file']}  {r['expr']}")
    echo(f"mutate --replay: {len(records)} recorded, {len(survived)} no longer caught, {len(stale)} stale")
    return 1 if (survived or stale) else 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--replay":
        path = _record_path(argv, "--replay")
        if not path:
            print("mutate --replay: needs a record file", file=sys.stderr)
            return 2
        return replay(path)
    record_to = _record_path(argv, "--record")
    if record_to:
        i = argv.index("--record")
        argv = argv[:i] + argv[i + 2:]
    if len(argv) < 3:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print("usage: python -m qabench mutate [--record RECORD.json] <file> '<expr>' -- <command...>\n"
              "       python -m qabench mutate --replay RECORD.json",
              file=sys.stderr)
        return 2
    path, expr = argv[0], argv[1]
    rest = argv[2:]
    if rest and rest[0] == "--":
        rest = rest[1:]
    if not rest:
        print("mutate: no command to run", file=sys.stderr)
        return 2

    target = pathlib.Path(path)
    if not target.is_file():
        print(f"mutate: no such file: {path}", file=sys.stderr)
        return 2

    dirty = _uncommitted(target)
    original = target.read_bytes()
    text = original.decode("utf-8")
    try:
        import re as _re
        mutated = eval(expr, {"s": text, "re": _re})          # noqa: S307 - a dev tool
    except Exception as exc:                                   # noqa: BLE001
        print(f"mutate: expression failed, file untouched: {exc}", file=sys.stderr)
        return 2
    if not isinstance(mutated, str):
        print("mutate: the expression must return a string", file=sys.stderr)
        return 2
    if mutated == text:
        print("mutate: the expression changed nothing — a mutation that is a "
              "no-op proves nothing, and it reads exactly like a guard that "
              "failed to fire", file=sys.stderr)
        return 2

    if dirty:
        print(f"mutate: {path} has UNCOMMITTED changes. They are safe — the restore below is a byte copy "
              "taken just now, not HEAD. Do NOT run `git checkout -- " + path + "` afterwards: that restores "
              "HEAD and discards them, which is the exact mistake this tool was written for.", file=sys.stderr)
    backup = pathlib.Path(tempfile.mkstemp(prefix="qabench-mutate-")[1])
    backup.write_bytes(original)
    try:
        target.write_text(mutated, encoding="utf-8")
        _purge_bytecode(target)
        try:
            completed = subprocess.run(rest)
        except OSError as exc:
            # A command that cannot even start is not a surviving mutation, and
            # must not be reported as one: exit 0 here would read as "the guard
            # cannot see it". The file is restored either way by the `finally`.
            print(f"mutate: could not run {rest[0]!r}: {exc}", file=sys.stderr)
            return 2
        rc = completed.returncode
        if record_to:
            records = [r for r in _load(record_to)
                       if (r["file"], r["expr"]) != (str(target), expr)]
            records.append({"file": str(target), "expr": expr, "command": rest,
                            "verdict": "caught" if rc != 0 else "survived",
                            "exit": rc, "recorded": dt.date.today().isoformat()})
            record_to.parent.mkdir(parents=True, exist_ok=True)
            record_to.write_text(json.dumps({"mutations": records}, indent=1), encoding="utf-8")
        return rc
    finally:
        # From the BACKUP, never from HEAD. This line is the whole point.
        target.write_bytes(backup.read_bytes())
        os.utime(target, None)
        _purge_bytecode(target)
        try:
            backup.unlink()
        except OSError:
            pass


if __name__ == "__main__":       # pragma: no cover
    raise SystemExit(main())
