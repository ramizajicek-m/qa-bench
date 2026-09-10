"""The gesture lifter, tested on the shapes that actually broke things.

Each case here is a property the estate has paid for somewhere: Jinja that a
strict parser chokes on, a key that moves when a line is added above it, a
substring match that makes one surface stand in for another, and a population
that improves when the classifier gets worse.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qabench.gestures import (Gesture, NOT_DRIVING, classify_with_js,
                              driven_by_corpus, lift, neutralise_jinja,
                              population, read_corpus)


def write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


# --- Jinja ------------------------------------------------------------------

def test_a_jinja_expression_in_an_attribute_keeps_the_attribute():
    """`{{ }}` collapses to a placeholder rather than vanishing.

    Deleting it would leave `action="/issue//sign"` — a different key for every
    template that happens to interpolate — and dropping the quotes entirely is
    what makes a strict parser call a clean template broken.
    """
    out = neutralise_jinja('<form action="/issue/{{ c.alloc_number }}/sign">')
    assert out == '<form action="/issue/{}/sign">'


def test_a_jinja_statement_is_removed_but_the_markup_survives():
    out = neutralise_jinja('{% if x %}<form method="post" action="/a">{% endif %}')
    assert '<form method="post" action="/a">' in out
    assert "{%" not in out


def test_two_renderings_of_one_control_are_the_same_gesture(tmp_path):
    """The point of the placeholder: one control, one key, whatever the row."""
    write(tmp_path, "a.html", '<form method="post" action="/x/{{ a.id }}/go"></form>')
    write(tmp_path, "b.html", '<form method="post" action="/x/{{ b.pk }}/go"></form>')
    ids = {g.selector for g in lift(tmp_path)}
    assert ids == {"form[POST /x/{}/go]"}, ids


# --- what counts ------------------------------------------------------------

def test_a_mutating_form_is_one_gesture_not_two(tmp_path):
    """Its submit button is the same gesture, not a second one."""
    write(tmp_path, "t.html",
          '<form method="post" action="/pay"><button type="submit">Pay</button></form>')
    got = lift(tmp_path)
    assert len(got) == 1 and got[0].kind == "form", got


def test_a_get_form_is_not_in_the_population(tmp_path):
    """A search box changes nothing stored."""
    write(tmp_path, "t.html", '<form method="get" action="/search"><button>Go</button></form>')
    assert population(lift(tmp_path)) == []


def test_a_browser_local_button_is_classified_no_not_unknown(tmp_path):
    """`window.print()` is a real control that stores nothing.

    It must be classifiable OUT LOUD. Leaving it `unknown` would bury the real
    unresolved candidates in noise, which is how a list stops being read.
    """
    write(tmp_path, "t.html", '<button onclick="window.print()">Print</button>')
    got = lift(tmp_path)
    assert got[0].mutates == "no" and "browser-local" in got[0].why


def test_an_unresolved_candidate_stays_in_the_population(tmp_path):
    """The degenerate direction: a count that improves as the classifier worsens.

    If `unknown` were excluded, breaking `classify_with_js` would make every
    project's number fall and look like progress.
    """
    write(tmp_path, "t.html", '<button data-action="wipe">Wipe</button>')
    got = lift(tmp_path)
    assert got[0].mutates == "unknown"
    assert len(population(got)) == 1


def test_the_js_classifier_upgrades_a_button_it_can_resolve(tmp_path):
    write(tmp_path, "t.html", '<button data-action="wipe">Wipe</button>')
    got = classify_with_js(lift(tmp_path), {
        "app.js": "document.querySelector('[data-action=wipe]')"
                  ".addEventListener('click', () => fetch('/api/wipe', {method: 'POST'}))"})
    assert got[0].mutates == "yes"


def test_the_js_classifier_never_downgrades_to_no(tmp_path):
    """It may leave a mutating control unknown; it must never call one safe.

    An overclaim removes a real gesture from the population silently, which is
    the failure the whole module exists to prevent.
    """
    write(tmp_path, "t.html", '<button data-action="wipe">Wipe</button>')
    got = classify_with_js(lift(tmp_path), {"app.js": "// nothing about wipe here"})
    assert got[0].mutates == "unknown"


# --- keys that do not move --------------------------------------------------

def test_the_key_survives_a_line_added_above_it(tmp_path):
    """Anat's line-keyed exemptions broke four times in one morning.

    Every time because something was added ABOVE them — never because the thing
    they pinned changed.
    """
    body = '<form method="post" action="/a/{{ i }}/b"></form>'
    write(tmp_path, "t.html", body)
    before = [g.id for g in lift(tmp_path)]
    write(tmp_path, "t.html", "<p>a new heading</p>\n<div>and a wrapper</div>\n" + body)
    assert [g.id for g in lift(tmp_path)] == before


def test_a_control_with_no_stable_attribute_says_so(tmp_path):
    """A positional key is honest about being fragile rather than silent."""
    write(tmp_path, "t.html", "<button>Unnamed</button>")
    assert "?positional" in lift(tmp_path)[0].selector


# --- coverage ---------------------------------------------------------------

def test_every_static_segment_must_appear_not_merely_one(tmp_path):
    """`/lead` matching `/lead-intake` is how a whole surface reads as covered."""
    g = [Gesture(template="t.html", kind="form", selector="form[POST /admin/users/{}/deactivate]",
                 method="POST", action="/admin/users/{}/deactivate", mutates="yes")]
    assert driven_by_corpus(g, {"a.py": "'/admin/users/'"}) == set()
    assert driven_by_corpus(g, {"a.py": "'/admin/users/' + i + '/deactivate'"}) == {g[0].id}


def test_the_reporter_does_not_drive_what_it_reports(tmp_path):
    """This module's own first run against IGA.

    The consumer test names every undriven control in its docstring, so leaving
    it in the corpus made each one read as driven by the file that reports it
    undriven.
    """
    (tmp_path / "test_every_gesture_is_driven.py").write_text(
        "'''names /admin/users/ and /deactivate'''", encoding="utf-8")
    (tmp_path / "real_test.py").write_text("x = 1", encoding="utf-8")
    corpus = read_corpus([tmp_path])
    assert set(Path(p).name for p in corpus) == {"real_test.py"}
    assert "test_every_gesture_is_driven.py" in NOT_DRIVING


def test_a_corpus_that_walked_nothing_is_empty_not_wrong(tmp_path):
    """It returns nothing rather than raising, so the CALLER can refuse.

    Refusing here would hide the size from the caller; the size is the evidence.
    """
    assert read_corpus([tmp_path / "does-not-exist"]) == {}


# --- the corpus proof lives with the corpus ---------------------------------
#
# There is deliberately NO "run it against a real tree" test here: the fixture
# repo has no templates, so such a test could only ever skip, and a check that
# cannot run reports nothing while looking like a pass. The corpus proof is in
# the consumer, where a real template tree exists — IGA's
# `test_the_sweep_read_a_real_corpus` refuses a run that lifts fewer than 20
# controls or reads fewer than 20 corpus files, and says DID NOT RUN rather
# than reporting a clean repo.
