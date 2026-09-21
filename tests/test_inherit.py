"""inherited: the four guards of 2026-09-21 that were guards for the case, not the class."""
from qabench import inherit


def test_anat_route_sweep_inherited_batch_and_bulk():
    src = 'import re\nBULKY = re.compile(r"/api/.*(batch|bulk)")\n'
    found = dict(inherit.unexplained(src, "routes that iterate a collection and report a count", {}, python=True))
    assert {"batch", "bulk"} <= set(found)


def test_anat_count_guard_inherited_the_denominator():
    src = 'import re\nPAT = re.compile(r"(\\d+) of 146")\n'
    found = dict(inherit.unexplained(src, "a count copied into the tracker equals its source", {}, python=True))
    assert "146" in found


def test_ana_act02_inherited_the_prop_name():
    src = "const hosts = read(); const m = hosts.match(/<(\\w+Dialog)[^>]*onDone={\\(/g); expect(hosts).toContain('publish')\n"
    found = dict(inherit.unexplained(src, "a dialog that writes a record publishes what it changed", {}, python=False))
    assert "done" in found and "publish" not in found


def test_anat_dialog_ratchet_inherited_the_overlay_class():
    src = 'OVERLAY = ".modal-overlay"\nWINDOW_END = "data-dialog-close"\n'
    found = dict(inherit.unexplained(src, "every dialog whose dismiss would discard typing asks first", {}, python=True))
    assert {"modal", "overlay"} <= set(found)


def test_a_declared_literal_is_answered_and_the_property_words_pass():
    src = 'OVERLAY = ".modal-overlay"\n'
    prop = "every dialog whose dismiss would discard typing asks first"
    assert inherit.unexplained(src, prop, {"modal": "every dialog here renders as one", "overlay": "same element"},
                               python=True) == []


def test_docstrings_are_prose_not_selectors():
    src = '"""Guards batch and bulk routes, historically."""\nX = "collection"\n'
    assert inherit.unexplained(src, "routes that iterate a collection", {}, python=True) == []


def test_cli_exit_codes(tmp_path):
    f = tmp_path / "t.py"
    f.write_text('P = "(batch|bulk)"\n')
    assert inherit.run([str(f), "--property", "routes that iterate a collection"], echo=lambda *_: None) == 1
    assert inherit.run([str(f), "--property", "batch or bulk routes"], echo=lambda *_: None) == 0
    assert inherit.run([str(f), "--property", ""], echo=lambda *_: None) == 3
    assert inherit.run([str(tmp_path / "missing.py"), "--property", "x"], echo=lambda *_: None) == 3
