"""anchors: prose that names a place in the code must still point at it."""
import yaml

from qabench import anchors


def repo(tmp_path, prose, pin=None, extra=None):
    (tmp_path / "qa").mkdir(parents=True)
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "catalog.html").write_text(
        "\n".join(f"<p>line {i}</p>" for i in range(1, 11)) + "\n<script>AnatFlash.toast('saved')</script>\n")
    (tmp_path / "docs.md").write_text(prose)
    cfg = {"prose": ["docs.md"]}
    if pin is not None:
        cfg["max_line_citations"] = pin
    cfg.update(extra or {})
    (tmp_path / "qa" / "manifest.yml").write_text(yaml.safe_dump({"anchors": cfg}))
    return tmp_path


def run(root):
    out = []
    return anchors.run(["--repo", str(root)], echo=out.append), out


def test_a_content_anchor_that_resolves_is_clean(tmp_path):
    assert run(repo(tmp_path, 'status shown via catalog.html#"AnatFlash.toast"', pin=0))[0] == 0


def test_a_content_anchor_whose_literal_is_gone_is_red(tmp_path):
    """tharros D12: comments said break-inside: avoid; zero occurrences."""
    code, out = run(repo(tmp_path, 'rows never split: catalog.html#"break-inside: avoid"', pin=0))
    assert code == 1 and any("no longer contains" in o for o in out)


def test_a_citation_whose_quoted_code_moved_away_has_drifted(tmp_path):
    """anat GEN-01: line 261 had become a toast call; the reason still described the old code."""
    code, out = run(repo(tmp_path, "catalog.html:3 writes `statusDiv.textContent` into a div", pin=5))
    assert code == 1 and any("DRIFTED" in o for o in out)


def test_a_citation_whose_quoted_code_is_still_there_is_clean(tmp_path):
    assert run(repo(tmp_path, "catalog.html:10 calls `AnatFlash.toast`", pin=5))[0] == 0


def test_a_citation_past_the_end_is_red(tmp_path):
    assert run(repo(tmp_path, "see catalog.html:900", pin=5))[0] == 1


def test_a_citation_to_a_missing_file_is_red(tmp_path):
    code, out = run(repo(tmp_path, "see templates/gone.html:3", pin=5))
    assert code == 1 and any("no such file" in o for o in out)


def test_a_bare_name_this_repo_lacks_is_unresolved_not_red(tmp_path):
    """ana-log cites `intakeService.ts:302` — the codebase it was ported from, which this cannot read."""
    assert run(repo(tmp_path, "ported from intakeService.ts:302", pin=5))[0] == 0


def test_a_citation_in_backticks_does_not_pair_its_closing_tick_with_the_next(tmp_path):
    assert run(repo(tmp_path, "`catalog.html:3` and `catalog.html:4` agree", pin=5))[0] == 0
    assert run(repo(tmp_path / "b" , "`catalog.html:3` writes `statusDiv.textContent`", pin=5))[0] == 1


def test_line_citations_are_ratcheted_and_an_unpinned_count_is_named(tmp_path):
    code, out = run(repo(tmp_path, "catalog.html:1 and catalog.html:2"))
    assert code == 1 and any("not pinned" in o and "2 line citation" in o for o in out)


def test_the_ratchet_fires_when_a_citation_is_added(tmp_path):
    assert run(repo(tmp_path, "catalog.html:1 and catalog.html:2", pin=1))[0] == 1


def test_no_block_or_no_files_is_did_not_run(tmp_path):
    (tmp_path / "qa").mkdir()
    (tmp_path / "qa" / "manifest.yml").write_text("{}")
    assert run(tmp_path)[0] == 3
    (tmp_path / "qa" / "manifest.yml").write_text(yaml.safe_dump({"anchors": {"prose": ["nothing/*.md"]}}))
    assert run(tmp_path)[0] == 3


def test_a_member_reference_is_not_a_line_citation(tmp_path):
    assert anchors.LINE.findall("tests/test_x.py::test_y and localhost:8000") == []


def test_an_excluded_file_is_not_read(tmp_path):
    root = repo(tmp_path, "see templates/gone.html:3", pin=5, extra={"exclude": ["docs.md"], "prose": ["docs.md", "qa/*.yml"]})
    assert run(root)[0] == 0


def test_advisory_prints_but_exits_zero(tmp_path):
    root = repo(tmp_path, "see catalog.html:900", pin=5)
    out = []
    assert anchors.run(["--repo", str(root), "--advisory"], echo=out.append) == 0 and any("RED" in o for o in out)
