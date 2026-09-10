"""A deploy skipped for an unchanged build is not a deployment that is behind.

2026-09-10, three projects in one day. IGA's main moved to three commits
touching only `.github/`, `docs/` and `tests/`; my8200's to six whose whole diff
is `CLAUDE.md` and one file under `docs/`. Railway skipped both staging deploys
— correctly, the build input was unchanged — and each night then waited sixteen
times for a SHA nothing would ever deploy and failed, taking `bench` and
`promote` with it. `stages/smoke.py` made the same strict comparison, so every
project carried the shape whether its own workflow did or not.

That third instance is why the logic is here rather than copied again.

The refusals matter more than the permission: a check that cannot fail is worth
nothing, so every direction in which the claim does NOT hold is pinned below.
"""
from __future__ import annotations

import subprocess

import pytest

from qabench.deployable import (
    UNDEPLOYABLE_PREFIXES,
    deployable_changes,
    is_undeployable,
    running_this_code,
)


def _git(*args, cwd=None):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)


@pytest.fixture
def repo(tmp_path):
    """A real repository. The whole question is what `git diff` says between two
    real trees, so the fixture builds trees rather than faking a diff — a fake
    would agree with whatever this module already believes."""
    d = tmp_path / "r"
    d.mkdir()
    _git("init", "-q", cwd=d)
    _git("config", "user.email", "t@t", cwd=d)
    _git("config", "user.name", "t", cwd=d)
    (d / "app.py").write_text("x = 1\n")
    (d / "docs").mkdir()
    (d / "docs" / "note.md").write_text("one\n")
    _git("add", "-A", cwd=d); _git("commit", "-qm", "base", cwd=d)
    base = _git("rev-parse", "HEAD", cwd=d).stdout.strip()
    return d, base


def _commit(d, rel, body, msg):
    p = d / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    _git("add", "-A", cwd=d); _git("commit", "-qm", msg, cwd=d)
    return _git("rev-parse", "HEAD", cwd=d).stdout.strip()


def test_a_docs_only_gap_is_running_this_code(repo):
    """my8200's incident in miniature: the only change is markdown.

    Mutation: drop '.md' from UNDEPLOYABLE_SUFFIXES — red.
    """
    d, base = repo
    tip = _commit(d, "docs/note.md", "two\n", "docs")
    ok, why = running_this_code(base, tip, cwd=str(d))
    assert ok, why
    assert "no deployable change" in why


def test_a_ci_and_tests_gap_is_running_this_code(repo):
    """IGA's incident: workflows and tests only."""
    d, base = repo
    _commit(d, ".github/workflows/ci.yml", "on: push\n", "ci")
    tip = _commit(d, "tests/test_x.py", "def test_x(): pass\n", "tests")
    ok, why = running_this_code(base, tip, cwd=str(d))
    assert ok, why


def test_one_real_source_change_in_the_gap_still_refuses(repo):
    """The half that must keep working. A single app file alongside the docs is
    enough — staging really is behind.

    Mutation: return [] from deployable_changes — red.
    """
    d, base = repo
    _commit(d, "docs/note.md", "two\n", "docs")
    tip = _commit(d, "app.py", "x = 2\n", "code")
    ok, why = running_this_code(base, tip, cwd=str(d))
    assert not ok
    assert "app.py" in why


def test_a_commit_off_the_line_is_refused(repo):
    """Running something that is not an ancestor is worse than being behind, and
    must never be waved through by the undeployable rule."""
    d, base = repo
    _git("checkout", "-q", "-b", "other", base, cwd=d)
    other = _commit(d, "docs/x.md", "z\n", "other branch")
    _git("checkout", "-q", "-", cwd=d)
    tip = _commit(d, "docs/note.md", "three\n", "main side")
    ok, why = running_this_code(other, tip, cwd=str(d))
    assert not ok and "not an ancestor" in why


def test_an_unresolvable_commit_is_did_not_run(repo):
    d, base = repo
    ok, why = running_this_code("0" * 40, base, cwd=str(d))
    assert not ok
    assert "not an ancestor" in why or "DID NOT RUN" in why


def test_an_empty_deployed_commit_is_did_not_run(repo):
    """`/health` answering with no commit field. Prefix matching on an empty
    string matches everything, which is how an unreachable deployment reads as
    agreement."""
    d, base = repo
    ok, why = running_this_code("", base, cwd=str(d))
    assert not ok and "DID NOT RUN" in why


def test_no_git_at_all_is_did_not_run(tmp_path):
    """The kit runs inside whatever checkout the project gives it, including a
    shallow one or none. Silence there must not read as agreement."""
    ok, why = running_this_code("a" * 40, "b" * 40, cwd=str(tmp_path))
    assert not ok
    assert "not an ancestor" in why or "DID NOT RUN" in why


def test_identical_and_abbreviated_shas_agree(repo):
    """/health serves 12 characters; QA_EXPECT_SHA is 40."""
    d, base = repo
    assert running_this_code(base, base, cwd=str(d))[0]
    assert running_this_code(base[:12], base, cwd=str(d))[0]


def test_the_undeployable_set_excludes_anything_that_can_run():
    """A wrong entry HIDES a real deploy gap. `scripts/` is deliberately absent:
    my8200 runs scripts/daily.py and scripts/apply_migrations.py in production."""
    assert set(UNDEPLOYABLE_PREFIXES) == {".github/", "docs/", "tests/"}
    for p in ("app/main.py", "scripts/daily.py", "requirements.txt",
              "Dockerfile", "qa/manifest.yml", "migrations/001.sql"):
        assert not is_undeployable(p), f"{p} can change what runs"
    for p in (".github/workflows/ci.yml", "docs/a.html", "tests/test_a.py", "CLAUDE.md"):
        assert is_undeployable(p)


def test_deployable_changes_says_none_rather_than_empty_when_it_cannot_look(tmp_path):
    """None and [] must stay distinguishable at the boundary — [] means "looked,
    found nothing", None means "could not look"."""
    assert deployable_changes("a" * 40, "b" * 40, cwd=str(tmp_path)) is None


def test_an_ancestor_whose_diff_cannot_be_read_is_did_not_run(repo, monkeypatch):
    """The branch every other test walks past.

    A mutation that made `changed is None` return True SURVIVED the whole file:
    the no-git case exits earlier, at the ancestor check, so nothing ever
    reached this line. That is the partial-vacuity shape — the branch existed,
    read as covered, and was not.

    Reaching it needs merge-base to SUCCEED and the diff to FAIL, which is a
    real state (a shallow clone can hold the ancestry graph and not the trees).
    Forced here at the one seam, so the assertion is about this module's
    behaviour rather than about git's.
    """
    from qabench import deployable

    d, base = repo
    tip = _commit(d, "docs/note.md", "two\n", "docs")

    real = deployable._git

    def only_diff_fails(*args, **kw):
        if args and args[0] == "diff":
            return 1, ""
        return real(*args, **kw)

    monkeypatch.setattr(deployable, "_git", only_diff_fails)
    ok, why = running_this_code(base, tip, cwd=str(d))
    assert not ok, "a diff that could not be read was reported as agreement"
    assert "DID NOT RUN" in why, why
