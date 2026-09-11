"""Tier 4, the portable half: did anything ship without being tested?

WHY ONLY HALF. anat's gap_analysis.py asks two questions, and they fail in
opposite directions: (A) did we build what was actually asked, and (B) did
anything ship untested. Question A reads anat's own request channels --
improvement_requests, internal_emails, WhatsApp, voice calls -- and measured on
one day those carried 159 requests while the ticket queue carried zero. No other
project in the estate has those channels, so A cannot be generalised without
inventing data. It stays where it is.

Question B needs nothing but git and the CI history every project already has,
and it is the mechanical half -- the part that can be a finding rather than a
worklist. That is what this module is.

WHAT IT ASKS, per commit merged in the window:

  1. Did it change code and NOT change any test?   -> shipped untested
  2. Did it ever appear in a GREEN run of the gate workflow?  -> shipped ungated

Both are mechanical. Neither is a judgement about whether the change was good.

WHAT IT DELIBERATELY DOES NOT DO. It does not claim a commit is untested because
the diff has no test file: a refactor covered by existing tests is not untested,
and saying so would make the report cry wolf until nobody read it. It reports the
COUNT and names the commits, and lets the reader judge -- with one exception, a
commit that is both code-only AND never in a green run, which is the shape worth
a finding on its own.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field

# A file is a TEST if any path segment says so. Deliberately broad: the cost of
# missing a test directory is a false "untested" finding, which is the direction
# that destroys trust in the report.
TEST_MARKERS = ("test", "tests", "spec", "specs", "e2e", "__tests__", "conftest.py")
# Not code, so a commit touching only these is not "shipped untested" -- it
# shipped nothing that could break.
NON_CODE_SUFFIXES = (".md", ".txt", ".rst", ".json", ".yml", ".yaml", ".lock",
                     ".png", ".jpg", ".svg", ".pdf", ".csv", ".tsv", ".html")
# Repo plumbing with no suffix, which a suffix test calls code. Found 2026-09-11:
# a commit that only added .gitmodules and a line to CLAUDE.md was reported as
# code shipped untested. One false finding of that kind teaches people to skip
# the report, which costs more than the findings are worth.
NON_CODE_NAMES = (".gitmodules", ".gitignore", ".gitattributes", ".dockerignore",
                  "LICENSE", "CODEOWNERS", ".editorconfig", "VERSION")


def _sh(args: list[str], cwd: str) -> tuple[int, str]:
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def is_test(path: str) -> bool:
    parts = path.replace("\\", "/").lower().split("/")
    if parts and parts[-1] in TEST_MARKERS:
        return True
    return any(seg in TEST_MARKERS or seg.startswith("test_") or seg.endswith("_test.py")
               for seg in parts)


# Editor and agent configuration. Not shipped, and a submodule gitlink under
# .claude/ has no suffix at all, so a suffix test calls it code.
NON_CODE_PREFIXES = (".claude/", ".vscode/", ".idea/", ".devcontainer/")


def is_code(path: str) -> bool:
    p = path.replace("\\", "/")
    if p.startswith(NON_CODE_PREFIXES) or p in (".claude", ".vscode"):
        return False
    if p.split("/")[-1] in NON_CODE_NAMES:
        return False
    return not p.lower().endswith(NON_CODE_SUFFIXES)


@dataclass
class Commit:
    sha: str
    subject: str
    code: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    green_run: str = ""          # url of a green gate run containing it, or ""

    @property
    def code_only(self) -> bool:
        return bool(self.code) and not self.tests


def commits_since(repo: str, since: str, branch: str = "main") -> list[Commit]:
    rc, out = _sh(["git", "log", f"--since={since}", "--first-parent",
                   "--pretty=%H%x1f%s", branch], repo)
    if rc != 0:
        raise RuntimeError(f"git log failed: {out.strip()[:200]}")
    commits = []
    for line in out.strip().splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        rc2, files = _sh(["git", "show", "--name-only", "--pretty=format:", sha], repo)
        if rc2 != 0:
            continue
        c = Commit(sha=sha, subject=subject)
        for f in (x.strip() for x in files.splitlines() if x.strip()):
            if is_test(f):
                c.tests.append(f)
            elif is_code(f):
                c.code.append(f)
        commits.append(c)
    return commits


def green_runs(repo_slug: str, workflow: str) -> set[str]:
    """SHAs that have at least one SUCCESSFUL run of the gate workflow."""
    rc, out = _sh(["gh", "api",
                   f"repos/{repo_slug}/actions/workflows/{workflow}/runs?per_page=100",
                   "--jq", '[.workflow_runs[]|select(.conclusion=="success")|.head_sha]'],
                  cwd=".")
    if rc != 0:
        return set()
    try:
        return set(json.loads(out))
    except Exception:
        return set()


def analyse(repo: str, repo_slug: str, workflow: str, since: str = "1 day ago",
            branch: str = "main") -> dict:
    commits = commits_since(repo, since, branch)
    green = green_runs(repo_slug, workflow)
    for c in commits:
        if c.sha in green:
            c.green_run = c.sha
    code_only = [c for c in commits if c.code_only]
    ungated = [c for c in commits if c.code and not c.green_run]
    # The shape worth a finding: changed code, added no test, and never appeared
    # in a green gate run. Either alone is normal; both together is a gap.
    both = [c for c in commits if c.code_only and not c.green_run]
    return {
        "repo": repo_slug,
        "since": since,
        "commits": len(commits),
        "code_only": [{"sha": c.sha[:12], "subject": c.subject} for c in code_only],
        "ungated": [{"sha": c.sha[:12], "subject": c.subject} for c in ungated],
        "untested_and_ungated": [{"sha": c.sha[:12], "subject": c.subject} for c in both],
        # A window with no commits proves nothing. Say so rather than reporting
        # a clean bill of health for a day nobody worked.
        "discriminating": len(commits) > 0,
    }


def render(result: dict) -> str:
    if not result["discriminating"]:
        return (f"{result['repo']}: no commits in the window ({result['since']}) — "
                f"this is NOT a pass, it is nothing to judge")
    lines = [f"{result['repo']}: {result['commits']} commits since {result['since']}"]
    n = len(result["untested_and_ungated"])
    if n:
        lines.append(f"  FINDING — {n} commit(s) changed code, added no test, and "
                     f"never appeared in a green gate run:")
        for c in result["untested_and_ungated"]:
            lines.append(f"    {c['sha']}  {c['subject'][:70]}")
    lines.append(f"  code without a test change: {len(result['code_only'])} "
                 f"(context, not a finding — existing tests may cover it)")
    lines.append(f"  never in a green gate run:  {len(result['ungated'])}")
    return "\n".join(lines)


def run(argv: list[str]) -> int:
    """CLI entry. Exit 1 when there is a finding, 2 when there was nothing to judge.

    Exit 2 matters: a window with no commits is not a clean bill of health, and a
    Tier 4 that reports success for a day nobody worked is the vacuity this whole
    kit exists to refuse.
    """
    import argparse
    import os

    ap = argparse.ArgumentParser(prog="qabench gap")
    ap.add_argument("--repo", default=os.getcwd())
    ap.add_argument("--slug", required=True, help="owner/name")
    ap.add_argument("--workflow", default="ci.yml", help="the gate workflow file")
    ap.add_argument("--since", default="1 day ago")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    result = analyse(a.repo, a.slug, a.workflow, since=a.since, branch=a.branch)
    print(json.dumps(result, indent=2) if a.json else render(result))
    if not result["discriminating"]:
        return 2
    return 1 if result["untested_and_ungated"] else 0
