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

    python -m qabench mutate <file> '<python expr over s>' -- <command...>

The expression returns the mutated text, e.g. 's.replace("== 2", "== 1", 1)'.
The command is arbitrary, so this serves a pytest repo and an `npm test` repo
alike. Exit code is the COMMAND's, so 0 means the mutation SURVIVED — your guard
cannot see it — and non-zero means a test caught it. Read it the right way round.

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


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 3:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print("usage: python -m qabench mutate <file> '<expr>' -- <command...>",
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
        return completed.returncode
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
