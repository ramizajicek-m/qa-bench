"""delta: a tier that is habitually red must still report what is NEW."""
from qabench import delta


def xml(tmp_path, name, cases):
    body = "".join(
        f'<testcase classname="c" name="{n}">{"<failure/>" if s == "F" else "<skipped/>" if s == "S" else ""}</testcase>'
        for n, s in cases.items())
    p = tmp_path / name
    p.write_text(f'<testsuite name="s">{body}</testsuite>')
    return p


def test_new_failures_on_an_already_red_tier_are_named_and_red(tmp_path):
    """ana-log: 33 new failures on a tier already red changed nothing visible."""
    b = xml(tmp_path, "b.xml", {"a": "F", "b": "P", "c": "P"})
    a = xml(tmp_path, "a.xml", {"a": "F", "b": "F", "c": "P"})
    out = []
    assert delta.run(["--before", str(b), "--after", str(a)], echo=out.append) == 1
    assert any("NEW" in line and "::b" in line for line in out)


def test_the_same_red_is_not_news(tmp_path):
    b = xml(tmp_path, "b.xml", {"a": "F", "b": "P"})
    a = xml(tmp_path, "a.xml", {"a": "F", "b": "P"})
    assert delta.run(["--before", str(b), "--after", str(a)], echo=lambda *_: None) == 0


def test_a_failure_that_vanishes_is_red_not_fixed(tmp_path):
    """A failure that disappears usually stopped running rather than started passing."""
    b = xml(tmp_path, "b.xml", {"a": "F", "b": "P"})
    a = xml(tmp_path, "a.xml", {"b": "P"})
    d = delta.compare(delta.read(b), delta.read(a))
    assert d["vanished"] == ["s::c::a"] and d["fixed"] == []
    assert delta.run(["--before", str(b), "--after", str(a)], echo=lambda *_: None) == 1


def test_a_failure_that_passes_is_fixed_and_green(tmp_path):
    b = xml(tmp_path, "b.xml", {"a": "F"})
    a = xml(tmp_path, "a.xml", {"a": "P"})
    assert delta.compare(delta.read(b), delta.read(a))["fixed"] == ["s::c::a"]
    assert delta.run(["--before", str(b), "--after", str(a)], echo=lambda *_: None) == 0


def test_store_first_run_has_no_baseline_then_compares_against_the_last(tmp_path):
    store = tmp_path / "store"
    r1 = xml(tmp_path, "r1.xml", {"a": "F", "b": "P"})
    r2 = xml(tmp_path, "r2.xml", {"a": "F", "b": "F"})
    r3 = xml(tmp_path, "r3.xml", {"a": "F", "b": "F"})
    args = ["--store", str(store), "--name", "browser"]
    assert delta.run(args + ["--after", str(r1)], echo=lambda *_: None) == 3
    assert delta.run(args + ["--after", str(r2)], echo=lambda *_: None) == 1
    assert delta.run(args + ["--after", str(r3)], echo=lambda *_: None) == 0   # b is no longer new


def test_a_duplicate_identity_or_empty_report_is_refused(tmp_path):
    dup = tmp_path / "d.xml"
    dup.write_text('<testsuite name="s"><testcase classname="c" name="x"/><testcase classname="c" name="x"/></testsuite>')
    empty = tmp_path / "e.xml"
    empty.write_text('<testsuite name="s"/>')
    ok = xml(tmp_path, "ok.xml", {"a": "P"})
    assert delta.run(["--before", str(ok), "--after", str(dup)], echo=lambda *_: None) == 3
    assert delta.run(["--before", str(ok), "--after", str(empty)], echo=lambda *_: None) == 3


def test_the_same_title_under_two_playwright_projects_stays_distinct(tmp_path):
    p = tmp_path / "pw.xml"
    p.write_text('<testsuites><testsuite name="chromium"><testcase classname="f" name="t"><failure/></testcase></testsuite>'
                 '<testsuite name="webkit"><testcase classname="f" name="t"/></testsuite></testsuites>')
    assert delta.read(p) == {"chromium::f::t": "failed", "webkit::f::t": "passed"}
