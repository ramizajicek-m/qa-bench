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
    assert "1 ELEMENT" in out[0] and "MENTIONED 3" in out[0] and "`grep -o` would say 3" in out[0]
    assert elements.run(["tab-set", "--repo", str(tmp_path), "--glob", "nothing/*.html"], echo=out.append) == 3


def test_markup_built_in_a_js_string_is_an_element():
    """anat my_day.html builds its sticky-head tables in script; a parser skipping <script> counted none."""
    src = "<script>el.innerHTML = '<table class=\"settings-table sticky-head\"><thead>';</script>"
    assert elements.count(src, "sticky-head") == (1, 1)


def test_jinja_quotes_inside_the_attribute_do_not_end_it():
    """`class="{{ "wide" if w }} sticky-head"` — the inner quotes would end the attribute unless Jinja is neutralised."""
    assert elements.count('<div class="{{ "wide" if w else "" }} sticky-head">', "sticky-head")[0] == 1


def test_three_numbers_for_one_question_are_all_named():
    """anat-qa: 16 substring hits, 13 whole-name mentions, 12 elements — and grep -c counts lines."""
    src = '<script src="/static/js/sticky-head-ing.js"></script>\n<div class="client-sticky-header"></div>\n' \
          '<table class="sticky-head"></table><style>.sticky-head{}</style>\n'
    assert elements.count(src, "sticky-head") == (1, 2)
    assert elements.greps(src, "sticky-head") == (4, 3)


THARROS_CSS = """
/* Shared reveal: sections fade in when scrolled into view. */
.rv { opacity: 0; transform: translateY(22px); }
.rv.in { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) { .fade { opacity: 0; } }
html.js .later { opacity: 0 }
.modal { display: none; }
"""


def test_a_base_rule_of_opacity_zero_is_hidden_until_script_and_conditions_are_not():
    """tharros `.rv { opacity: 0 }`: 49 sections invisible with scripts off; the first version missed it."""
    assert elements.hidden_until_script(THARROS_CSS) == {"rv"}


def test_the_cli_names_the_classes_and_their_templates(tmp_path):
    (tmp_path / "static").mkdir()
    (tmp_path / "static" / "site.css").write_text(THARROS_CSS)
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "track.html").write_text('<section class="rv">handover</section><div class="modal"></div>')
    out = []
    assert elements.run(["--hidden-by-default", "--repo", str(tmp_path)], echo=out.append) == 0
    assert elements.run(["--hidden-by-default", "--repo", str(tmp_path), "--strict"], echo=out.append) == 1
    assert any(".rv: 1 element" in o and "track.html" in o for o in out)
