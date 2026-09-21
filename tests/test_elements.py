"""elements: a class's instances, not its mentions."""
from qabench import elements

FLEET = """
<style>.tab-set { display: flex }</style>
<div class="tab-set" role="tablist"><button class="tab">A</button></div>
<script>document.querySelector('.tab-set').classList.add('ready')</script>
"""


def test_one_element_and_three_mentions():
    """anat-qa: fleet.html had ONE tab set; the class string appeared again in its CSS rule and JS."""
    assert elements.count(FLEET, "tab-set") == (1, 3)


def test_a_class_beside_jinja_is_still_counted():
    assert elements.count('<div class="{{ theme }} sticky-head x">', "sticky-head") == (1, 1)


def test_a_longer_name_is_not_the_class():
    assert elements.count('<div class="sticky-head-row">', "sticky-head") == (0, 0)


def test_the_cli_prints_both_numbers(tmp_path):
    (tmp_path / "fleet.html").write_text(FLEET)
    out = []
    assert elements.run(["tab-set", "--repo", str(tmp_path)], echo=out.append) == 0
    assert "1 ELEMENT" in out[0] and "MENTIONED 3" in out[0] and "a grep would have said 3" in out[0]
    assert elements.run(["tab-set", "--repo", str(tmp_path), "--glob", "nothing/*.html"], echo=out.append) == 3


def test_markup_built_in_a_js_string_is_an_element():
    """anat my_day.html builds its sticky-head tables in script; a parser skipping <script> counted none."""
    src = "<script>el.innerHTML = '<table class=\"settings-table sticky-head\"><thead>';</script>"
    assert elements.count(src, "sticky-head") == (1, 1)


def test_jinja_quotes_inside_the_attribute_do_not_end_it():
    """`class="{{ "wide" if w }} sticky-head"` — the inner quotes would end the attribute unless Jinja is neutralised."""
    assert elements.count('<div class="{{ "wide" if w else "" }} sticky-head">', "sticky-head")[0] == 1
