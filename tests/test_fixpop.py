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


def test_git_comment_lines_are_not_the_subject():
    """A commit-msg hook sees git's `#` lines; one above the subject must not hide a fix."""
    assert fixpop.judge_message("# Please enter the commit message\nfix: x\n")


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


RULE = {"paths": ["tests/*"], "trailer": "Answers"}


def test_a_change_to_a_test_must_say_which_row_it_answers():
    """anat: a branch added a guard credited to no row, the day four such rows were found."""
    assert fixpop.judge_answers("feat: guard the window\n", ["tests/unit/test_x.py"], RULE)
    assert fixpop.judge_answers("feat: guard\n\nAnswers: UI-MOB-01\n", ["tests/unit/test_x.py"], RULE) == ""


def test_answers_none_is_cheap_and_accepted():
    assert fixpop.judge_answers("chore: rename a fixture\n\nAnswers: none\n", ["tests/conftest.py"], RULE) == ""


def test_a_change_touching_no_test_is_not_asked():
    assert fixpop.judge_answers("feat: page\n", ["app/main.py"], RULE) == ""
    assert fixpop.judge_answers("feat: page\n", ["tests/x.py"], None) == ""


def test_range_mode_reads_each_commits_files(tmp_path):
    import yaml
    def git(*a):
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=tmp_path, check=True, capture_output=True)
    git("init", "-q")
    (tmp_path / "qa").mkdir()
    (tmp_path / "qa" / "manifest.yml").write_text(yaml.safe_dump({"fixpop": {"answers": RULE}}))
    git("add", "-A"); git("commit", "-q", "-m", "base")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_a(): pass\n")
    git("add", "-A"); git("commit", "-q", "-m", "feat: a guard")
    assert fixpop.run(["--repo", str(tmp_path), "--range", "HEAD~1..HEAD"], echo=lambda *_: None) == 1
    (tmp_path / "tests" / "test_b.py").write_text("def test_b(): pass\n")
    git("add", "-A"); git("commit", "-q", "-m", "feat: b guard\n\nAnswers: none")
    assert fixpop.run(["--repo", str(tmp_path), "--range", "HEAD~1..HEAD"], echo=lambda *_: None) == 0
