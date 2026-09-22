#!/usr/bin/env python3
"""Release the kit: one version in three files, one commit, one TAG.

    python scripts/release.py 0.1.41 "one line on what changed"

Twenty-two releases, 0.1.18 through 0.1.39, existed only as commits whose
message named the version — the GitHub tags stopped at v0.1.17. Consumers pin
commits (right: a tag can move), but a human reading `qa-bench@306df95d` cannot
say which release that is without a checkout, and `qabench report`'s `kit`
column compares VERSIONS. A release is therefore: bump `__version__`,
`pyproject.toml` and the fixture manifest together, commit, and tag `vX.Y.Z` on
that commit. This script refuses to do fewer than all four.

It refuses while `mutate --replay qa/mutations.json` is not clean. A STALE record is
a guarantee nobody is checking any more: on 2026-09-22 one of three stale records,
re-anchored, survived — `ran --heavy` could drop its lock with the suite green.

It does not push. `git push origin main --tags` is the release; do it once the
kit's own suite is green on the bumped tree.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    ROOT / "qabench" / "__init__.py": r'(__version__ = ")([^"]+)(")',
    ROOT / "pyproject.toml": r'(^version = ")([^"]+)(")',
    ROOT / "tests" / "fixture_repo" / "qa" / "manifest.yml": r'(^\s+version: )(\S+)()',
}


def sh(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def replay_clean() -> bool:
    """Every recorded mutation still applies and is still caught (mutate --replay exits 0)."""
    rc = subprocess.run([sys.executable, "-m", "qabench", "mutate", "--replay", "qa/mutations.json"],
                        cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT)}).returncode
    return rc == 0


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not re.fullmatch(r"\d+\.\d+\.\d+", argv[0]):
        print(__doc__, file=sys.stderr)
        return 2
    version, title = argv
    if sh("git", "status", "--porcelain"):
        print("refusing: the tree is dirty — a release is the bump and nothing else", file=sys.stderr)
        return 1
    if f"v{version}" in sh("git", "tag").split():
        print(f"refusing: v{version} already exists", file=sys.stderr)
        return 1
    if not replay_clean():
        print("refusing: mutate --replay is not clean — re-anchor every STALE record and make every survivor "
              "caught before releasing", file=sys.stderr)
        return 1
    current = None
    for path, pattern in FILES.items():
        text = path.read_text(encoding="utf-8")
        m = re.search(pattern, text, re.M)
        if not m:
            print(f"refusing: no version in {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        if current is None:
            current = m.group(2)
        elif m.group(2) != current:
            print(f"refusing: {path.relative_to(ROOT)} says {m.group(2)}, another file says {current} — "
                  "the three had already drifted; fix by hand first", file=sys.stderr)
            return 1
        path.write_text(re.sub(pattern, rf"\g<1>{version}\g<3>", text, count=1, flags=re.M), encoding="utf-8")
    sh("git", "add", *[str(p) for p in FILES])
    sh("git", "commit", "-q", "-m", f"{version}: {title}")
    sh("git", "tag", "-a", f"v{version}", "-m", f"qabench {version}: {title}")
    print(f"{current} -> {version}: committed and tagged v{version}. Now: run the suite, then git push origin main --tags")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
