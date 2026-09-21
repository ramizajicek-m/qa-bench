"""decisions: a ruling names the observation that would prove it wrong."""
import yaml

from qabench import decisions


def reg(tmp_path, entries):
    (tmp_path / "qa").mkdir(parents=True, exist_ok=True)
    (tmp_path / "qa" / "decisions.yml").write_text(yaml.safe_dump(entries))
    return tmp_path


NAV08 = {"id": "NAV-08", "rule": "the section mark may share the page mark's tint",
         "falsified_by": "the two marks cannot be told apart at a glance on a detail page"}


def test_a_ruling_with_its_falsifier_passes_and_one_without_is_named():
    out = decisions.judge([NAV08, {"id": "D2", "rule": "total at the bottom"}])
    assert [m["id"] for m in out] == ["D2"]


def test_a_placeholder_falsifier_is_no_falsifier():
    for f in ("n/a", "none", "never", "wrong"):
        assert decisions.judge([{"id": "x", "rule": "r", "falsified_by": f}]), f


def test_report_only_by_default_and_strict_on_request(tmp_path):
    root = reg(tmp_path, [NAV08, {"id": "D2", "rule": "total at the bottom"}])
    assert decisions.run(["--repo", str(root)], echo=lambda *_: None) == 0
    assert decisions.run(["--repo", str(root), "--strict"], echo=lambda *_: None) == 1
    assert decisions.run(["--repo", str(reg(tmp_path / "b", [NAV08])), "--strict"], echo=lambda *_: None) == 0


def test_no_register_is_did_not_run(tmp_path):
    assert decisions.run(["--repo", str(tmp_path)], echo=lambda *_: None) == 3
