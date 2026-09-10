"""Is the deployment running this code? — not "does it report this SHA".

THREE PROJECTS HIT THIS IN ONE DAY, 2026-09-10, and the third is why this lives
in the kit instead of being copied a third time.

IGA's main moved to three commits touching only `.github/`, `docs/` and
`tests/`. my8200's moved to six whose whole diff is `CLAUDE.md` and one file
under `docs/`. In both cases Railway SKIPPED the staging deploy — correctly, the
build input was unchanged, so there was no new image to ship — and each
project's night then waited sixteen times for staging to report a SHA nothing
would ever deploy, and failed. `bench` and `promote` are `needs:` that job, so
both night lanes and every promotion behind them stopped on changes that cannot
affect what runs, and would have stayed stopped until somebody happened to push
application code.

`stages/smoke.py` made the same strict comparison, so all six projects carried
the shape whether or not their own workflow did.

THE CLAIM is "the deployment I am about to sweep is running this run's code".
SHA equality is a proxy for it. The two come apart exactly when the deployed
commit is an ANCESTOR of the candidate and everything between them is
undeployable — and that is the case this module recognises, refusing every
other:

  * not an ancestor          -> it is running something else, worse than behind
  * a deployable file in the gap -> genuinely behind on code, the real defect
  * cannot compare           -> DID NOT RUN, never silent agreement

UNDEPLOYABLE is deliberately short and conservative: CI definitions, the docs
tree, the test tree, markdown anywhere. `scripts/` is NOT here — my8200 runs
`scripts/daily.py` and `scripts/apply_migrations.py` in production, and IGA's
`scripts/` is on production paths too. A wrong entry hides a real deploy gap,
which is the failure the check exists to prevent, so when in doubt a path stays
OUT.
"""
from __future__ import annotations

import subprocess

#: Path prefixes whose contents cannot change what a deployed service runs.
UNDEPLOYABLE_PREFIXES = (".github/", "docs/", "tests/")
UNDEPLOYABLE_SUFFIXES = (".md",)


def is_undeployable(path: str) -> bool:
    return path.startswith(UNDEPLOYABLE_PREFIXES) or path.endswith(UNDEPLOYABLE_SUFFIXES)


def _git(*args: str, cwd: str | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return p.returncode, p.stdout.strip()


def deployable_changes(deployed: str, candidate: str, *, cwd: str | None = None) -> list[str] | None:
    """Files between the two commits that COULD change what runs.

    None when the comparison could not be made — a missing object, a shallow
    clone, no git at all — which must never be read as "no changes".
    """
    rc, out = _git("diff", "--name-only", f"{deployed}..{candidate}", cwd=cwd)
    if rc != 0:
        return None
    return [p for p in out.splitlines() if p and not is_undeployable(p)]


def running_this_code(deployed: str, candidate: str, *, cwd: str | None = None) -> tuple[bool, str]:
    """(ok, why). `ok` is True only when the deployment is running this code."""
    if not deployed:
        return False, "the deployment did not name a commit — treat as DID NOT RUN"
    if not candidate:
        return False, "no candidate SHA to compare against — treat as DID NOT RUN"
    if candidate.startswith(deployed) or deployed.startswith(candidate):
        return True, f"serving {deployed[:12]}"

    rc, _ = _git("merge-base", "--is-ancestor", deployed, candidate, cwd=cwd)
    if rc != 0:
        return False, (f"serving {deployed[:12]}, which is not an ancestor of "
                       f"{candidate[:12]} — running something else, or the commit "
                       "is not in this checkout")

    changed = deployable_changes(deployed, candidate, cwd=cwd)
    if changed is None:
        return False, (f"cannot compare {deployed[:12]} with {candidate[:12]} here "
                       "— treat as DID NOT RUN, not as agreement")
    if changed:
        head = ", ".join(changed[:4])
        more = f" (+{len(changed) - 4} more)" if len(changed) > 4 else ""
        return False, (f"serving {deployed[:12]}, and the gap to {candidate[:12]} "
                       f"changes deployable files: {head}{more}")
    return True, (f"serving {deployed[:12]}; {candidate[:12]} adds only CI, docs, "
                  "tests and markdown — no deployable change")
