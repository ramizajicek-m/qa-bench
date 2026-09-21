"""fixpop: a fix commit names the other sites with its shape, or the search that found none."""
import subprocess

from qabench import fixpop


def test_a_fix_without_a_population_is_refused():
    assert fixpop.judge_message("fix: keep a hand-picked tier\n\nbody")


def test_a_fix_naming_its_sites_passes():
    assert fixpop.judge_message("fix: keep a hand-picked tier\n\nPopulation: fee field (fixed), quote tier (guarded)\n") == ""


def test_none_needs_the_search():
    assert fixpop.judge_message("fix: x\n\nPopulation: none\n")
    assert fixpop.judge_message("fix: x\n\nPopulation: none (searched)\n")
    assert fixpop.judge_message("fix: x\n\nPopulation: none (searched: rg '\\.value =' static/)\n") == ""


def test_placeholders_name_nothing():
    for v in ("n/a", "-", "TBD", "", "?"):
        assert fixpop.judge_message(f"fix: x\n\nPopulation: {v}\n"), v


def test_a_non_fix_commit_is_not_asked_unless_require_all():
    assert fixpop.judge_message("feat: add a page\n") == ""
    assert fixpop.judge_message("feat: add a page\n", require_all=True)


def test_fix_forms_are_recognised_and_merges_skipped():
    for s in ("fix(auth): x", "hotfix: x", "Fix the fee", "fix!: x", "bugfix: x"):
        assert fixpop.judge_message(s + "\n"), s
    assert fixpop.judge_message("Merge branch 'fix/x'\n") == ""


def test_comment_lines_do_not_count_as_the_trailer():
    assert fixpop.judge_message("fix: x\n\n# Population: a, b\n")


def test_range_mode_reads_git_and_advisory_exits_zero(tmp_path):
    def git(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    git("init", "-q")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "base")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "fix: y")
    out = []
    assert fixpop.run(["--repo", str(tmp_path), "--range", "HEAD~1..HEAD"], echo=out.append) == 1
    assert fixpop.run(["--repo", str(tmp_path), "--range", "HEAD~1..HEAD", "--advisory"], echo=out.append) == 0
    assert fixpop.run(["--repo", str(tmp_path), "--range", "nope..HEAD"], echo=out.append) == 3


def test_msg_mode(tmp_path):
    m = tmp_path / "MSG"
    m.write_text("fix: x\n\nPopulation: none (searched: rg foo app/)\n")
    assert fixpop.run(["--msg", str(m)], echo=lambda *_: None) == 0
    assert fixpop.run(["--msg", str(tmp_path / "missing")], echo=lambda *_: None) == 3
