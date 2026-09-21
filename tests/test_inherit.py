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
    assert inherit.run([str(f), "--property", "routes that iterate a collection", "--words"], echo=lambda *_: None) == 1
    assert inherit.run([str(f), "--property", "routes that iterate a collection"], echo=lambda *_: None) == 0
    assert inherit.run([str(f), "--property", "batch or bulk routes", "--words"], echo=lambda *_: None) == 0
    assert inherit.run([str(f), "--property", ""], echo=lambda *_: None) == 3
    assert inherit.run([str(tmp_path / "missing.py"), "--property", "x"], echo=lambda *_: None) == 3


def test_an_assertion_message_is_prose_not_a_selector():
    src = 'def test_x():\n    assert ok, "bulk"\n'
    assert inherit.unexplained(src, "routes that iterate a collection", {}, python=True) == []


def test_code_vocabulary_is_matched_before_stemming_too():
    """`files` stems to `fil`, which is not code vocabulary; `files` is."""
    assert inherit.unexplained('X = "files"\n', "anything at all", {}, python=True) == []


WINDOW_BEFORE = '''
def dialogs(s, ms):
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(s)
        out.append("data-dialog-close" in s[m.start():end])
    return out
'''
WINDOW_AFTER = WINDOW_BEFORE.replace("ms[i + 1].start() if i + 1 < len(ms) else len(s)", "_extent(s, m.start())")

INVARIANT_BEFORE = '''
import pytest, re
@pytest.mark.parametrize("name", ["A", "B"])
def test_a_marking_dialog_really_publishes(name):
    hosts = "\\\\n".join(_source(h) for h in HOSTS)
    completion = re.search(rf"<{name}.*?onDone", hosts)
    assert completion
    assert "publish" in hosts
'''
INVARIANT_AFTER = INVARIANT_BEFORE.replace('assert "publish" in hosts', 'assert "publish(" in _callback_of(name, hosts)')


def test_the_window_is_the_one_anat_shipped_and_the_walk_is_not():
    """anat 4eba1e09: the extent of dialog i ended at dialog i+1's start; 17 reported against 18 by nesting."""
    assert [k for _, k, _ in inherit.methods(WINDOW_BEFORE)] == ["window"]
    assert inherit.methods(WINDOW_AFTER) == []


def test_the_invariant_assertion_is_the_one_ana_shipped_and_the_scoped_one_is_not():
    """ana 7a6a1b7b^: `"publish" in hosts` passed for every dialog because one dialog in the file publishes."""
    assert [k for _, k, _ in inherit.methods(INVARIANT_BEFORE)] == ["invariant"]
    assert inherit.methods(INVARIANT_AFTER) == []


def test_an_exception_captured_from_the_parameter_carries_it():
    src = '''
import pytest
@pytest.mark.parametrize("field", ["a", "b"])
def test_x(field):
    with pytest.raises(ValueError) as e:
        make(field)
    assert field in str(e.value)
    assert "final_price_agreed" in str(e.value)
'''
    assert inherit.methods(src) == []


def test_a_span_ending_at_the_same_match_is_the_element_not_a_window():
    src = 'def f(s, ms, i):\n    return "x" in s[ms[i].start():ms[i].end()]\n'
    assert inherit.methods(src) == []


def test_a_fixed_case_test_whose_assertions_are_all_invariant_is_a_different_shape():
    src = '''
import pytest
@pytest.mark.parametrize("name", ["A", "B"])
def test_x(name):
    assert "publish" in CORPUS
'''
    assert inherit.methods(src) == []


def test_a_fixture_navigated_with_the_parameter_carries_it():
    """Without this the estate run flagged 973 assertions, nearly all browser tests asserting on `page`."""
    src = '''
import pytest
@pytest.mark.parametrize("path", ["/a", "/b"])
def test_x(page, path):
    page.goto(path)
    assert path
    assert "Saved" in page.content()
'''
    assert inherit.methods(src) == []


def test_fixed_offset_and_text_search_windows_are_the_same_method():
    """anat-qa: the first version was keyed on `ms[i + 1].start()` and saw 1 of 59+ in anat."""
    fixed = 'def f(src, i):\n    call = src[i:i + 120]\n    assert "x" in call\n'
    found = 'def f(src, a):\n    assert "x" in src[a:src.find("</form>", a)]\n'
    assert [k for _, k, _ in inherit.methods(fixed)] == ["window"]
    assert [k for _, k, _ in inherit.methods(found)] == ["window"]


def test_invariant_is_opt_in_on_the_command_line(tmp_path):
    f = tmp_path / "t.py"
    f.write_text(INVARIANT_BEFORE)
    assert inherit.run([str(f), "--property", "a dialog publishes name hosts completion onDone source HOSTS"],
                       echo=lambda *_: None) == 0
    assert inherit.run([str(f), "--property", "a dialog publishes name hosts completion onDone source HOSTS",
                        "--invariant"], echo=lambda *_: None) == 1


def test_regex_escapes_paths_and_short_numbers_are_not_selector_words():
    """ana-qa: `bheight` from \\bmaxHeight, `modul` from node_modules, `02` from a phone number."""
    src = 'A = r"\\bmaxHeight\\b|\\bheight\\s*:"\nB = "node_modules/x"\nC = "02-9999999"\n'
    found = dict(inherit.unexplained(src, "max height", {}, python=True))
    assert not any(w.startswith("b") and w[1:] in ("height", "max") for w in found)
    assert "modul" not in found and "path:node_modules/x" in found
    assert "02" not in found
    assert "146" in dict(inherit.unexplained('P = r"(\\d+) of 146"\n', "a count equals its source", {}, python=True))


def test_a_skip_after_a_timeout_names_a_cause_it_cannot_know():
    """anat: 'no rows — a DATA blocker' on a page that had no such table at all."""
    src = """
import pytest
def test_x(page):
    page.goto('/admin/gifts')
    try:
        page.wait_for_selector('#t tbody tr', timeout=12000)
    except PlaywrightTimeout:
        pytest.skip('no rows on the test stack - a DATA blocker')
"""
    assert [k for _, k, _ in inherit.methods(src)] == ["diagnosing-skip"]
    fixed = src.replace("    try:", "    page.wait_for_selector('#t')\n    try:").replace(
        "except PlaywrightTimeout:\n        pytest.skip", "except PlaywrightTimeout:\n        pytest.skip")
    other = src.replace("except PlaywrightTimeout:", "except ValueError:")
    assert inherit.methods(other) == []


def test_a_broad_catch_that_discriminates_before_skipping_is_the_right_shape():
    """anat conftest: reads the error text, skips only on named causes, re-raises the rest."""
    good = """
import pytest
def f():
    try:
        g()
    except Exception as e:
        if "Connection" in str(e):
            pytest.skip("unreachable")
        raise
"""
    bad = good.replace('        if "Connection" in str(e):\n            pytest.skip("unreachable")\n        raise',
                       '        pytest.skip("no data yet")')
    assert inherit.methods(good) == []
    assert [k for _, k, _ in inherit.methods(bad)] == ["diagnosing-skip"]


def test_a_clean_run_names_the_shapes_it_looked_for(tmp_path):
    f = tmp_path / "t.py"
    f.write_text("def test_x():\n    assert 1\n")
    out = []
    assert inherit.run([str(f), "--property", "anything"], echo=out.append) == 0
    assert any("looked for:" in o and "not that the file has no such defect" in o for o in out)
