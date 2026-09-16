"""The gesture lifter, tested on the shapes that actually broke things.

Each case here is a property the estate has paid for somewhere: Jinja that a
strict parser chokes on, a key that moves when a line is added above it, a
substring match that makes one surface stand in for another, and a population
that improves when the classifier gets worse.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qabench.gestures import (Gesture, NOT_DRIVING, classify_with_js,
                              driven_by_corpus, lift, lift_with_scripts,
                              neutralise_jinja, population, read_corpus)


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


# --- inline handlers --------------------------------------------------------

def test_a_handler_in_the_same_template_resolves_the_control(tmp_path):
    """anat wires 907 of its 914 controls in an inline <script>.

    A classifier reading only static/js/ resolved SEVEN of them, so the first
    run reported zero undriven mutating controls — false, and false in the
    reassuring direction.
    """
    write(tmp_path, "t.html",
          '<button id="send">Send</button>'
          '<script>document.getElementById("send")'
          '.addEventListener("click", () => fetch("/api/send", {method: "POST"}))</script>')
    gestures, scripts = lift_with_scripts(tmp_path)
    assert "t.html" in scripts, "the inline script was not captured"
    got = classify_with_js(gestures, dict(scripts))
    assert got[0].mutates == "yes"


def test_a_control_is_not_resolved_by_an_unrelated_template(tmp_path):
    """One page's `save` must not resolve another page's `save`.

    Searching a single global blob is the same substring collision that lets one
    surface stand in for another in the coverage half.
    """
    write(tmp_path, "quiet.html", '<button id="save">Save</button>')
    write(tmp_path, "loud.html",
          '<button id="unrelated">x</button>'
          '<script>document.getElementById("save")'
          '.addEventListener("click", () => fetch("/api/save", {method:"POST"}))</script>')
    gestures, scripts = lift_with_scripts(tmp_path)
    got = {g.template: g for g in classify_with_js(gestures, dict(scripts))}
    assert got["quiet.html"].mutates == "unknown", (
        "a handler in loud.html resolved a control in quiet.html")


def test_a_script_body_is_not_mistaken_for_a_control(tmp_path):
    """Script text is data, not markup: nothing inside <script> is a gesture."""
    write(tmp_path, "t.html",
          '<script>var s = "<button data-action=ghost>not real</button>";</script>')
    assert lift(tmp_path) == []


def test_classifying_a_large_estate_does_not_take_minutes():
    """A checker nobody will wait for is a checker nobody runs.

    The first version concatenated the shared script blob once PER CONTROL and
    did not finish in ten minutes on anat (914 controls, 12 MB of corpus). The
    blob is now built once per template. This pins the shape rather than a
    wall-clock number, which would be a fixture about this machine.
    """
    import time
    gestures = [Gesture(template=f"t{i}.html", kind="button",
                        selector=f"button[id=b{i}]", mutates="unknown")
                for i in range(400)]
    big = {"shared.js": "x = 1;\n" * 80_000}
    started = time.monotonic()
    classify_with_js(gestures, big)
    assert time.monotonic() - started < 20, (
        "classification is rebuilding the shared blob per control again")


def test_the_population_is_unique_by_id(tmp_path):
    """A generator counting a list and a consumer counting a set must agree.

    They did not: my8200's `library_tags.html` renders one form twice, so the
    register froze a ceiling of 60 while the guard measured 59 — and that gap is
    exactly the room a new undriven control needs to slip through. A mutation
    adding one did not breach the ratchet. The id IS the key; two rows sharing
    one are the same control.
    """
    write(tmp_path, "t.html",
          '<form method="post" action="/x/{{ a }}/go"></form>'
          '<form method="post" action="/x/{{ b }}/go"></form>')
    pop = population(lift(tmp_path))
    assert len(pop) == 1, f"the same control counted {len(pop)} times"
    assert len(pop) == len({g.id for g in pop}), "list and set disagree"


# --- the population the review found missing (2026-09-12) --------------------
#
# An adversarial review of the register in six repos found five confirmed
# defects in what this module counts as a control and what it counts as driven.
# Each test below is one of them, and each was watched red against the code as
# it stood before the fix.


def test_a_form_with_no_method_but_an_id_is_a_candidate(tmp_path):
    """THE DOMINANT SHAPE, and it was invisible.

    A form emitted a row only when its method was POST/PUT/PATCH/DELETE. anat's
    admin is SPA-style: 75 form tags, 7 with a mutating method, 68 without, and
    58 of those carry an id and are submitted by `fetch(..., {method:'POST'})`
    from an inline handler. So the way that product mostly changes state was not
    in the population at all — not undriven, ABSENT.

    It is `unknown`, not `yes`: markup alone cannot tell a JS-posted form from a
    genuine GET. The classifier decides, and unknown stays in the population.

    Mutation: with `"lifted": method in MUTATING_METHODS` this returns [].
    """
    write(tmp_path, "t.html",
          '<form id="portal-invite-form"><button>Send</button></form>')
    pop = population(lift(tmp_path))
    assert [g.id for g in pop] == ["t.html::form[id=portal-invite-form]"]
    assert pop[0].mutates == "unknown"


def test_a_plain_get_search_form_is_still_not_a_candidate(tmp_path):
    """And the button inside it is not one either.

    The pair matters: if the form is not a row, its submit must be swallowed all
    the same, or every search box on the site arrives as an unresolved control
    needing a reason. The stated limit is that a JS-submitted form with NO
    stable attribute is invisible — nothing selects it, so there is no key.
    """
    write(tmp_path, "t.html",
          '<form method="get" action="/search"><button>Go</button></form>')
    assert population(lift(tmp_path)) == []


def test_a_formaction_submit_is_its_own_control(tmp_path):
    """It posts somewhere its parent form never does.

    `<button type=submit formaction="/admin/x/{}/delete">` inside a SAVE form
    was swallowed as "the form above already IS this gesture". tharros had three
    such DELETEs and my8200 two, all with live routes, none in the population.

    Mutation: delete the `formaction` branch in `_maybe_button` and only the
    parent form survives.
    """
    write(tmp_path, "t.html",
          '<form method="post" action="/admin/products/{{ id }}/save">'
          '<button type="submit">Save</button>'
          '<button type="submit" formaction="/admin/products/{{ id }}/delete">Delete</button>'
          '</form>')
    ids = sorted(g.id for g in population(lift(tmp_path)))
    assert ids == ["t.html::button[POST /admin/products/{}/delete]",
                   "t.html::form[POST /admin/products/{}/save]"]


def test_hidden_literal_fields_keep_multiplexed_forms_apart(tmp_path):
    """Same route, different operation, and one of them was `delete`.

    my8200's library_tags.html has five forms posting to the same path with a
    hidden `action` of rename / up / down / on-off / delete. They shared one id,
    so driving `rename` reported `delete` as driven. 33 controls collapsed into
    20 ids in that repo alone.

    A Jinja-valued hidden field is NOT used: after neutralisation it is the same
    placeholder in every copy and would distinguish nothing.

    Mutation: drop the `hidden` key from the selector and this returns one id.
    """
    write(tmp_path, "t.html",
          '<form method="post" action="/admin/tags/{{ id }}">'
          '<input type="hidden" name="op" value="rename"></form>'
          '<form method="post" action="/admin/tags/{{ id }}">'
          '<input type="hidden" name="op" value="delete"></form>')
    ids = sorted(g.id for g in population(lift(tmp_path)))
    assert ids == ["t.html::form[POST /admin/tags/{}]{op=delete}",
                   "t.html::form[POST /admin/tags/{}]{op=rename}"]


def test_an_unclosed_form_still_emits_its_row(tmp_path):
    """`{% if %}<form>{% else %}<div>{% endif %}` leaves unbalanced tags.

    The row is emitted at the END tag, so a form that never closes would be
    dropped entirely. Four templates in the estate parse this way.
    """
    write(tmp_path, "t.html",
          '<form method="post" action="/admin/x/go"><button>Go</button>')
    assert [g.id for g in population(lift(tmp_path))] == ["t.html::form[POST /admin/x/go]"]


# --- what counts as DRIVEN --------------------------------------------------

def test_two_unrelated_files_do_not_jointly_drive_one_control(tmp_path):
    """THE MEASURE WAS SATISFIED BY COINCIDENCE.

    The old test asked whether every static SEGMENT appeared somewhere in one
    concatenated blob, each independently. So `/admin/courses/{}/archive` was
    driven by an unrelated public `/archive` page test plus any mention of
    `/admin/courses/`. Measured on IGA: a probe file whose entire content was
    the docstring "posts to /issue/passkeys/1/delete" healed THREE rows at once,
    two of them destructive, because `/delete` is a segment they share.

    Mutation: restore `all(s in blob for s in segs)` and this control reads
    driven.
    """
    write(tmp_path, "t.html",
          '<form method="post" action="/admin/courses/{{ id }}/archive"></form>')
    g = lift(tmp_path)
    corpus = {"a.py": "client.get('/admin/courses/')",
              "b.py": "client.get('/archive')"}
    assert driven_by_corpus(g, corpus) == set()
    assert driven_by_corpus(g, {"c.py": "client.post(f'/admin/courses/{c.id}/archive')"})


def test_a_url_built_by_concatenation_still_counts(tmp_path):
    """The rule must not be so tight that real drivers stop counting.

    Both halves on one line, with anything between them, is how tests write it.
    A guard that refuses the healthy case gets overridden, and then it is gone.
    """
    write(tmp_path, "t.html",
          '<form method="post" action="/admin/users/{{ id }}/deactivate"></form>')
    g = lift(tmp_path)
    for driver in ('client.post("/admin/users/" + uid + "/deactivate")',
                   'client.post(f"/admin/users/{u.id}/deactivate")',
                   'url = "/admin/users/%s/deactivate" % uid'):
        assert driven_by_corpus(g, {"t.py": driver}), driver
    assert not driven_by_corpus(g, {"t.py": '"/admin/users/"\n"/deactivate"'})


def test_a_token_is_not_driven_by_a_longer_id_that_contains_it(tmp_path):
    """anat's `ai-btn` was driven by `#bp-ai-btn`, `#fn-ai-btn`, `#tr-ai-btn`.

    Zero whole-token hits; three other controls' ids. The register said the
    control was covered by the existence of its neighbours.
    """
    write(tmp_path, "t.html", '<button id="ai-btn" onclick="go()">AI</button>')
    g = lift(tmp_path)
    assert driven_by_corpus(g, {"t.py": "page.click('#bp-ai-btn')"}) == set()
    assert driven_by_corpus(g, {"t.py": "page.click('#ai-btn')"})


def test_a_token_is_not_driven_by_the_english_word(tmp_path):
    """`button[id=submit]` was driven by the word "submit" in a sentence.

    The token must carry the mark of a selector or a string literal, or every
    control named after a common verb is covered by prose.
    """
    write(tmp_path, "t.html", '<button id="submit" onclick="go()">Go</button>')
    g = lift(tmp_path)
    assert driven_by_corpus(g, {"t.py": "# then submit the form and wait"}) == set()
    assert driven_by_corpus(g, {"t.py": 'page.click("#submit")'})


# --- the register as a document ---------------------------------------------

from qabench.gestures import (BOILERPLATE_REASONS, integrity, measure,  # noqa: E402
                              pin_disagreements, pin_refs,  # noqa: E402
                              refusals, register_rows)


def _repo(tmp_path, templates: dict, corpus: dict):
    for name, body in templates.items():
        write(tmp_path / "templates", name, body)
    for name, body in corpus.items():
        write(tmp_path / "tests", name, body)
    return tmp_path


def test_a_sweep_that_walked_nothing_refuses(tmp_path):
    """A scan of nothing agrees with everything."""
    _repo(tmp_path, {"t.html": "<p>nothing</p>"}, {"t.py": "pass"})
    with pytest.raises(RuntimeError, match="DID NOT RUN"):
        measure(tmp_path, min_controls=5, min_corpus=1)


def test_a_new_mutating_control_cannot_be_enrolled_by_regenerating(tmp_path):
    """THE HOLE THE TOTAL COULD NOT SEE.

    Drive one unclassified control in the same change that adds an undriven
    DELETE and the total nets down, so a ceiling-only refusal never fires. The
    new row was then enrolled carrying a sentence a GENERATOR wrote — "MUTATING
    and undriven — no test or journey posts to it" — which restates the finding
    instead of deciding anything. Demonstrated live in IGA and in anat's copy:
    ceilings unchanged, guard green, a `/purge` route silently exempted.

    Mutating rows may LEAVE the register by being driven. They may not ENTER it
    by regeneration. A control that must be tolerated is added by hand, with a
    reason a person signs.

    Mutation: delete the `for g in m.mutating_undriven` loop in `refusals` and
    this returns [].
    """
    tmpl = {"a.html": '<form method="post" action="/admin/x/{{ i }}/purge"></form>'
                      '<button id="old-btn" onclick="go()">x</button>'}
    _repo(tmp_path, tmpl, {"t.py": "page.click('#old-btn')  # drives the old one"})
    m = measure(tmp_path, min_controls=1, min_corpus=1)
    old = {"ceiling": 1, "mutating": 0,
           "undriven": [{"id": "gone.html::button[id=x]", "mutates": "unknown",
                         "reason": "written by a person"}]}
    why = refusals(m, old)
    assert any("new MUTATING control" in r and "/admin/x/{}/purge" in r for r in why), why


def test_a_ceiling_that_disagrees_with_its_rows_is_a_number_nobody_measured(tmp_path):
    """A hand-edited ceiling bought five undriven controls with no row.

    `test_the_ceiling_is_not_slack` tolerates a gap of five and nothing compared
    the ceiling to the rows beneath it, so editing `ceiling: 16` to `20` passed
    in four repos.
    """
    _repo(tmp_path, {"a.html": '<button id="b" onclick="go()">x</button>'},
          {"t.py": "pass"})
    m = measure(tmp_path, min_controls=1, min_corpus=1)
    old = {"ceiling": 20, "mutating": 0,
           "undriven": [{"id": "a.html::button[id=b]", "mutates": "unknown",
                         "reason": "r"}]}
    assert any("nobody measured" in c for c in integrity(m, old))


def test_a_row_keeps_the_reason_a_person_wrote(tmp_path):
    """Regeneration must not overwrite a human sentence with boilerplate."""
    _repo(tmp_path, {"a.html": '<button id="b" onclick="go()">x</button>'},
          {"t.py": "pass"})
    m = measure(tmp_path, min_controls=1, min_corpus=1)
    rows = register_rows(m, {"a.html::button[id=b]": "Ofir signs off: demo only"})
    assert rows[0]["reason"] == "Ofir signs off: demo only"
    assert register_rows(m, {})[0]["reason"] in BOILERPLATE_REASONS


def test_regeneration_HEALS_a_row_that_got_driven_rather_than_refusing(tmp_path):
    """Fixing something must not mean fighting the generator.

    An earlier version refused to regenerate when a listed control had become
    driven — so `make gestures` failed on the one outcome the register exists to
    produce. The guard still asserts the register matches the sweep, because a
    stale exemption is how a list stops describing the thing it exempts, but
    that is the reader's job and healing is the writer's.
    """
    _repo(tmp_path, {"a.html": '<button id="b" onclick="go()">x</button>'},
          {"t.py": "page.click('#b')"})
    m = measure(tmp_path, min_controls=1, min_corpus=1)
    old = {"ceiling": 1, "mutating": 0,
           "undriven": [{"id": "a.html::button[id=b]", "mutates": "unknown", "reason": "r"}]}
    assert not [r for r in refusals(m, old) if "now driven" in r], \
        "regeneration must heal a healed row, not refuse"
    assert register_rows(m, {}) == [], "the healed control is gone from the rows"


def test_a_project_whose_controls_are_not_markup_uses_the_same_register(tmp_path):
    """ONE PROGRAM, SIX REPOS. The population source is the only thing that differs.

    ana-log is a React SPA: every button routes through `api.action(category,
    name)` to a single endpoint, so there is no markup to lift and its
    population is the action REGISTRY. That is a better population than markup
    would be — each entry declares `writes` itself rather than leaving a sweep
    to guess from a verb.

    What it must NOT mean is a second guard with a second matcher and a
    different register format, which is what it had: a bespoke copy that had
    already drifted from the other five. A provider keeps the register, the
    ratchets, the refusals and the integrity rules identical, exactly as
    `bench.routes` already works for the page sweep.

    `names` carries the tokens that count as naming a registry entry — the
    declared name and the handler — so ONE matcher serves both populations.

    Mutation: drop `names` from `driven_by_corpus` and the driven one reads
    undriven.
    """
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "t.py").write_text(
        'def test_it():\n    create_shipment(db, payload)\n', encoding="utf-8")

    def provider(root):
        return [
            Gesture(template="app/api/actions.py", kind="action",
                    selector="action[name=shipments.create]", mutates="yes",
                    why="declared writes=True", names=("create_shipment",)),
            Gesture(template="app/api/actions.py", kind="action",
                    selector="action[name=shipments.purge]", mutates="yes",
                    why="declared writes=True", names=("purge_shipment",)),
        ]

    m = measure(tmp_path, corpus_dirs=("tests",), min_controls=1, min_corpus=1,
                population_fn=provider)
    assert len(m.population) == 2
    assert [g.id for g in m.undriven] == ["app/api/actions.py::action[name=shipments.purge]"]
    assert m.mutating == 1
    # and the shared rules apply unchanged
    assert any("new MUTATING control" in r
               for r in refusals(m, {"ceiling": 0, "mutating": 0, "undriven": []}))


def test_a_repo_naming_two_qa_bench_refs_is_reported(tmp_path):
    """One kit, one commit, everywhere the repo names it.

    Three instances in one day: a repo pinning three different refs across its
    workflows and Makefile; another installing with no ref at all on a runner
    holding staging secrets; and a repin sweep that missed
    `requirements-dev.txt`, which is the file CI installs from — so a job ran
    the old kit against the new guard and died on an ImportError, a symptom
    that names a test rather than a pin.

    Mutation: return `found` unconditionally and the agreeing case reports a
    disagreement.
    """
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "ci.yml").write_text("pip install qa-bench@aaaa111\n")
    (tmp_path / "requirements-dev.txt").write_text("qabench @ git+x/qa-bench@bbbb222\n")
    (tmp_path / "doc.md").write_text("example: qa-bench@v0.1.10\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)

    bad = pin_disagreements(tmp_path)
    assert set(bad) == {"aaaa111", "bbbb222", "v0.1.10"}
    assert bad["bbbb222"] == ["requirements-dev.txt"]

    # an example in prose is declared, not silently tolerated
    assert set(pin_disagreements(tmp_path, ignore=("doc.md",))) == {"aaaa111", "bbbb222"}

    # a repo that names NO ref must be visible as such, or a guard over it is
    # vacuous: it would agree with everything by having read nothing.
    assert set(pin_refs(tmp_path)) == {"aaaa111", "bbbb222", "v0.1.10"}

    # and the agreeing case reports nothing at all
    (tmp_path / "requirements-dev.txt").write_text("qabench @ git+x/qa-bench@aaaa111\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    assert pin_disagreements(tmp_path, ignore=("doc.md",)) == {}


# --- named is not pressed ----------------------------------------------------

from qabench import hits as _hits                                    # noqa: E402
from qabench.gestures import (hit_by_recording,                      # noqa: E402
                              judgeable_by_recording)


def test_a_docstring_names_a_control_but_a_recording_does_not(tmp_path):
    """THE WHOLE POINT OF THE STRONGER HALF.

    `driven_by_corpus` counts a mention — a comment saying "posts to
    /admin/x/1/delete" satisfies it, and that is the weakest evidence standard
    of the approaches in the field. A recording of what the suite ACTUALLY sent
    cannot be satisfied that way.

    Mutation: feed the recording the matching request and it is hit.
    """
    write(tmp_path, "t.html",
          '<form method="post" action="/admin/x/{{ i }}/delete"></form>')
    g = lift(tmp_path)
    gid = "t.html::form[POST /admin/x/{}/delete]"

    corpus = {"t.py": '"""this test posts to /admin/x/1/delete."""'}
    assert driven_by_corpus(g, corpus) == {gid}, "the weak half still counts a mention"
    assert hit_by_recording(g, {"GET /admin/x/1/delete"}) == set(), "a GET is not this control"
    assert hit_by_recording(g, {"POST /admin/y/1/delete"}) == set(), "another route is not it"
    assert hit_by_recording(g, {"POST /admin/x/17/delete"}) == {gid}


def test_an_absent_recording_is_unknown_and_never_reported_as_no(tmp_path):
    """A repo that has not opted in is not in a failing state.

    Treating "no recording" as "nothing is hit" would put every control in
    every repo into the worst bucket on the day this ships, which is how a
    guard gets switched off in its first week.
    """
    write(tmp_path, "t.html", '<form method="post" action="/a/b"></form>')
    assert hit_by_recording(lift(tmp_path), set()) == set()
    assert _hits.read(tmp_path / "nope.json") == set()


def test_the_judgeable_subset_is_reportable(tmp_path):
    """A verdict must say how much of the population it could decide.

    Only a form declares a method and a path. A button wired in JS is the
    browser recorder's job, and until that runs its verdict is UNKNOWN — a
    coverage number over the whole population would quietly count those as
    failures.
    """
    write(tmp_path, "t.html",
          '<form method="post" action="/a/b"></form>'
          '<button id="js-only" onclick="go()">x</button>')
    g = lift(tmp_path)
    assert len(population(g)) == 2
    assert judgeable_by_recording(g) == {"t.html::form[POST /a/b]"}


def test_the_recorder_refuses_to_write_an_empty_recording(tmp_path):
    """An empty file is indistinguishable from "the suite drives nothing".

    Written, it would mark every control unhit on the next read and the count
    would leap for a reason that looks like a product regression.
    """
    _hits._seen.clear()
    with pytest.raises(RuntimeError, match="DID NOT RUN"):
        _hits.write(tmp_path / "hits.json")


def test_the_recorder_writes_what_it_saw(tmp_path):
    _hits._seen.clear()
    _hits.record("post", "/admin/x/1/delete", 303, location="/admin/x?deleted=1")
    _hits.record("GET", "/admin/x", 200)
    _hits.record("POST", "/admin/x/2/delete", 403)      # a CSRF refusal probe
    doc = _hits.write(tmp_path / "hits.json")
    assert doc["count"] == 3
    assert _hits.read(tmp_path / "hits.json") == {
        "POST /admin/x/1/delete", "GET /admin/x"}, "a refusal is not an exercise"
    assert "POST /admin/x/2/delete" in _hits.read(tmp_path / "hits.json",
                                                  accepted_only=False)
    _hits._seen.clear()


def test_the_recorder_catches_a_real_httpx_request(tmp_path):
    """Patching `httpx.Client.send` is the claim; this is the proof.

    Starlette's TestClient subclasses httpx.Client, so one patch covers every
    suite in the estate rather than a fixture each project must remember to
    apply — and a fixture nobody applies is the failure this whole program
    keeps finding.
    """
    httpx = pytest.importorskip("httpx")
    _hits._seen.clear()
    _hits._installed = False
    assert _hits.install()

    def handler(request):
        return httpx.Response(204)

    with httpx.Client(transport=httpx.MockTransport(handler),
                      base_url="http://t") as c:
        c.post("/admin/x/9/delete")
    assert any(r.startswith("POST /admin/x/9/delete 204") for r in _hits._seen)
    _hits._seen.clear()


def test_a_refused_request_is_not_an_exercise_of_the_control(tmp_path):
    """MEASURED ON A LIVE REPO, WITHIN MINUTES OF THE RECORDER WORKING.

    IGA's register listed six destructive admin controls as driven by nothing.
    The first recording said all six were posted to — and the poster was
    `test_every_field_is_accounted_for`, which walks the route table posting to
    every route WITHOUT a CSRF token and with required fields missing, asserting
    each refuses. The route is reached; nothing has ever successfully deleted
    anything.

    Counting that as a hit would have replaced a measure that UNDERCOUNTS with
    one that OVERCOUNTS, and that is the worse direction: an undercount leaves a
    to-do, an overcount retires it.

    Mutation: drop the status filter in `read` and the refusal counts.
    """
    write(tmp_path, "t.html",
          '<form method="post" action="/admin/x/{{ i }}/delete"></form>')
    g = lift(tmp_path)
    gid = "t.html::form[POST /admin/x/{}/delete]"
    _hits._seen.clear()
    _hits.record("POST", "/admin/x/1/delete", 403)       # the CSRF probe
    _hits.write(tmp_path / "h.json")
    assert hit_by_recording(g, _hits.read(tmp_path / "h.json")) == set()

    _hits.record("POST", "/admin/x/1/delete", 303,
                 location="/admin/x?saved=1")            # a real delete
    _hits.write(tmp_path / "h.json")
    assert hit_by_recording(g, _hits.read(tmp_path / "h.json")) == {gid}
    _hits._seen.clear()


def test_a_control_that_is_named_but_never_accepted_gets_its_own_ratchet(tmp_path):
    """TWO REGISTERS, because they are two different failures.

    A control can be named by six tests and never once have been ACCEPTED by
    the app. my8200 had sixteen of those and they were not obscure: marking an
    invoice paid, receiving goods against a purchase order, moving stock,
    cancelling a customer order. Every one was credited as driven because a
    test mentioned its URL.

    Mixing them into the undriven list would let a repo work down the cheap
    half and call it progress, so `unhit_mutating` ratchets separately.

    Mutation: drop the `if m.recorded` block in `refusals` and this returns [].
    """
    write(tmp_path / "templates", "t.html",
          '<form method="post" action="/admin/pay/{{ i }}/paid"></form>')
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "tests" / "t.py").write_text(
        'client.post(f"/admin/pay/{x}/paid")\n', encoding="utf-8")

    refused = {"POST /admin/pay/1/paid"}          # touched, but only refusals
    m = measure(tmp_path, corpus_dirs=("tests",), min_controls=1, min_corpus=1,
                recording=set())                  # nothing accepted
    m.recorded = True
    assert m.undriven == [], "the weak measure is satisfied: a test names the URL"
    assert [g.id for g in m.unhit_mutating] == ["t.html::form[POST /admin/pay/{}/paid]"]

    why = refusals(m, {"ceiling": 0, "mutating": 0, "undriven": [],
                       "unhit_mutating": 0, "unhit": []})
    assert any("never been accepted" in r for r in why), why

    # and with the request accepted, it leaves
    ok = measure(tmp_path, corpus_dirs=("tests",), min_controls=1, min_corpus=1,
                 recording={"POST /admin/pay/1/paid"})
    assert ok.unhit_mutating == []


def test_without_a_recording_the_hit_verdict_is_unknown_not_clean(tmp_path):
    """Refusing on an unknown teaches people to pass a flag to get past it."""
    write(tmp_path / "templates", "t.html",
          '<form method="post" action="/a/b"></form>')
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "tests" / "t.py").write_text("pass\n", encoding="utf-8")
    m = measure(tmp_path, corpus_dirs=("tests",), min_controls=1, min_corpus=1)
    assert m.recorded is False
    assert m.unhit_mutating == []
    assert not [r for r in refusals(m, {"ceiling": 1, "mutating": 1,
                                        "undriven": [{"id": "t.html::form[POST /a/b]",
                                                      "mutates": "yes", "reason": "r"}],
                                        "unhit_mutating": 0, "unhit": []})
                if "accepted" in r]


def test_a_directory_of_recordings_is_unioned_per_tier(tmp_path):
    """ONE RECORDING PER TIER, because a suite is not one run.

    anat's unit tier and its integration tier are separate commands. With a
    single hits file the second overwrote the first: the proposal approval was
    driven in INTEGRATION, the register regenerated from the UNIT recording, and
    the control still read as never accepted. Work done looked like no progress,
    which is the fastest way to make somebody stop doing it.

    Per-tier files rather than merge-on-write keeps staleness bounded — a tier's
    run replaces its own file, so a deleted route stops being claimed as hit.

    Mutation: drop the is_dir branch in `read` and the union is empty.
    """
    d = tmp_path / "hits"
    d.mkdir()
    # Both files declare the current format: the union is the subject here, and a
    # fixture that is silently stale would refuse instead of unioning.
    (d / "unit.json").write_text(json.dumps(
        {"format": _hits.FORMAT, "recorded": ["POST /a/b 200\t\t", "POST /refused 403\t\t"]}))
    (d / "integration.json").write_text(json.dumps(
        {"format": _hits.FORMAT, "recorded": ["POST /c/d 303\t/c?saved=1\t"]}))

    assert _hits.read(d) == {"POST /a/b", "POST /c/d"}
    assert _hits.read(d, accepted_only=False) == {
        "POST /a/b", "POST /refused", "POST /c/d"}
    assert _hits.read(tmp_path / "nothing-here") == set()


def test_the_verb_is_read_from_the_handler_not_assumed(tmp_path):
    """A control driven by PUT could never match a recording.

    Every JS-derived gesture was labelled POST, so anat's edit-project-form and
    mark-paid-form — both PUT, with no POST route existing at those paths at all
    — were destined to read as never accepted no matter how well they were
    tested.

    Mutation: restore the POST default and the PUT case fails.
    """
    write(tmp_path, "t.html", '<form id="edit-form"><button>Save</button></form>')
    (tmp_path / "static").mkdir(exist_ok=True)
    (tmp_path / "static" / "app.js").write_text(
        "document.getElementById('edit-form').addEventListener('submit', async () => {\n"
        "  await fetch(`/api/projects/${id}`, { method: 'PUT', body: b });\n"
        "});\n", encoding="utf-8")
    g, inline = lift_with_scripts(tmp_path)
    js = dict(inline)
    js["app.js"] = (tmp_path / "static" / "app.js").read_text()
    g = classify_with_js(g, js)
    row = [x for x in g if x.selector == "form[id=edit-form]"][0]
    assert row.method == "PUT", f"the verb was read as {row.method}"
    assert row.action == "/api/projects/{}"
    assert hit_by_recording(g, {"PUT /api/projects/abc"}) == {row.id}
    assert hit_by_recording(g, {"POST /api/projects/abc"}) == set(), \
        "a POST must not satisfy a control that sends PUT"


def test_a_handler_naming_two_urls_yields_no_action_rather_than_the_first(tmp_path):
    """AMBIGUOUS IS NOT A GUESS, and picking one was worse than picking none.

    anat's log-followup handler sits beside promote-to-lead in the same window.
    Taking the first literal labelled the register row with an endpoint the
    control never sends to — so `hit` was measured against the wrong path and the
    row could be wrong in BOTH directions: driven and reported undriven, or
    undriven and reported driven.

    The control stays in the population as unresolved, which is the honest state
    and still owes a test.

    Mutation: take `_HANDLER_URL.search(window)` unconditionally and this row
    gains an action it has no right to.
    """
    write(tmp_path, "t.html", '<form id="two-urls"><button>Go</button></form>')
    (tmp_path / "static").mkdir(exist_ok=True)
    (tmp_path / "static" / "app.js").write_text(
        "document.getElementById('two-urls').addEventListener('submit', async () => {\n"
        "  await fetch('/api/a/log-followup', { method: 'POST' });\n"
        "  await fetch('/api/a/promote-to-lead', { method: 'POST' });\n"
        "});\n", encoding="utf-8")
    g, inline = lift_with_scripts(tmp_path)
    js = dict(inline)
    js["app.js"] = (tmp_path / "static" / "app.js").read_text()
    g = classify_with_js(g, js)
    row = [x for x in g if x.selector == "form[id=two-urls]"][0]
    assert row.mutates == "yes", "it still reaches a mutating call"
    assert row.action == "", f"an ambiguous window produced the action {row.action!r}"
    assert row.id in {x.id for x in population(g)}, "it must stay in the population"
    assert judgeable_by_recording(g) == set(), \
        "a control with no action cannot be judged by a request log, and must say so"


def test_a_body_key_discriminates_controls_that_share_one_path(tmp_path, monkeypatch):
    """A WHOLE PROJECT had nothing to measure without this.

    ana-log dispatches all 55 of its write actions through
    `POST /api/actions/<category>` with `{"function": "<name>", ...}` in the body.
    A path-based recording cannot tell them apart, so its judgeable subset was
    ZERO — the measure said nothing about that repo rather than something weak,
    which is the worse of the two.

    The key is NAMED by the repo, not guessed. A recorder that rummaged for
    something discriminating would invent a different answer per project.

    Mutation: unset the env var and the two calls collapse to one entry.
    """
    httpx = pytest.importorskip("httpx")
    monkeypatch.setenv(_hits.BODY_KEYS_ENV, "function")
    _hits._seen.clear()
    _hits._installed = False
    assert _hits.install()

    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200)),
                      base_url="http://t") as c:
        c.post("/api/actions/intake", json={"function": "receiveCase", "case_id": 1})
        c.post("/api/actions/intake", json={"function": "startUnloading", "case_id": 1})
        c.post("/api/actions/intake", json={"case_id": 1})       # no key: no suffix

    seen = {r.rsplit(" ", 1)[0] for r in _hits._seen}
    assert seen == {
        "POST /api/actions/intake#receiveCase",
        "POST /api/actions/intake#startUnloading",
        "POST /api/actions/intake",
    }, seen
    _hits._seen.clear()


def test_an_unreadable_body_never_fails_the_suite(tmp_path, monkeypatch):
    """A recorder that raises is worse than one that records nothing.

    Bookkeeping must not decide whether a test passes, so a body that is not
    JSON, not a dict, or implausibly large simply does not discriminate.
    """
    httpx = pytest.importorskip("httpx")
    monkeypatch.setenv(_hits.BODY_KEYS_ENV, "function")
    _hits._seen.clear()
    _hits._installed = False
    _hits.install()
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(204)),
                      base_url="http://t") as c:
        c.post("/api/actions/x", content=b"not json at all")
        c.post("/api/actions/y", json=["a", "list", "not", "a", "dict"])
    assert {r.rsplit(" ", 1)[0] for r in _hits._seen} == {
        "POST /api/actions/x", "POST /api/actions/y"}
    _hits._seen.clear()


def test_a_non_form_gesture_that_declares_its_path_is_judgeable(tmp_path):
    """`kind` was never the property that mattered.

    ana-log's population comes from its action registry, so every row is
    kind="action". Keying the matcher on kind=="form" meant a project with 802
    recorded requests and 156 discriminated action calls still reported a
    judgeable subset of ZERO — the measure had the evidence and refused to look
    at it.

    Mutation: restore `g.kind == "form"` and both assertions fail.
    """
    def provider(root):
        return [Gesture(template="app/api/actions.py", kind="action",
                        selector="action[name=intake.receiveCase]",
                        method="POST", action="/api/actions/intake#receiveCase",
                        mutates="yes", why="declared writes=True",
                        names=("receive_case", "receiveCase"))]
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "t.py").write_text("pass\n", encoding="utf-8")
    m = measure(tmp_path, corpus_dirs=("tests",), min_controls=1, min_corpus=1,
                population_fn=provider,
                recording={"POST /api/actions/intake#receiveCase"})
    assert m.judgeable == {"app/api/actions.py::action[name=intake.receiveCase]"}
    assert m.hit == {"app/api/actions.py::action[name=intake.receiveCase]"}


# --- what "the app acted on it" actually means --------------------------------


def test_a_redirect_to_the_login_page_is_not_an_acceptance(tmp_path):
    """MEASURED, NOT IMAGINED — this credited real controls for months.

    On my8200, 2026-09-13:

        POST /admin/crm/2   unauthenticated   ->   303  Location: /login?next=...

    byte-identical in status to a successful form post. With `status < 400` as
    the rule, 42 of my8200's 220 write targets and 78 of tharros' 381 were
    credited ONLY by a 3xx. tharros reporting 103 judgeable / 103 accepted / 0
    never-accepted was a saturated measure, not a covered application.

    A 3xx now earns credit on evidence: a Location that is not a sign-in bounce.

    Mutation: drop the login-path check in `_acted` and the bounce counts.
    """
    assert _hits._acted(303, "/admin/x?saved=1") is True
    assert _hits._acted(303, "/login?next=/admin/crm/2") is False
    assert _hits._acted(302, "/login") is False
    assert _hits._acted(303, "") is False, "a redirect with no Location decides nothing"
    assert _hits._acted(200, "") is True


def test_a_307_never_counts_because_the_body_was_never_read(tmp_path):
    """13 of tharros' write targets were credited ONLY by a 307 or 308.

    Those statuses re-issue the request before the handler reads the body, so the
    control did nothing at all. They were outright false hits, and no Location
    makes them true.

    Mutation: let 307 fall through to the generic 3xx branch and it passes.
    """
    assert _hits._acted(307, "/admin/accessory-fulfilment/x") is False
    assert _hits._acted(308, "/admin/anything") is False


def test_a_third_party_sharing_a_path_cannot_credit_a_control(tmp_path, monkeypatch):
    """my8200's own recording carries six Google Cloud Storage rows.

        DELETE /storage/v1/b/bucket/o/daily/old.gz 204

    The recorder keyed on the path alone, so any third party a test happens to
    call could credit a control that shares its path. Hosts are DECLARED by the
    repo — guessing which host is "the app" is how a measure invents a different
    rule per project.

    Mutation: drop the host filter in `read` and the foreign row is returned.
    """
    f = tmp_path / "unit.json"
    f.write_text(json.dumps({"recorded": [
        "DELETE /storage/v1/b/bucket/o/old.gz 204\t\tstorage.googleapis.com",
        "POST /admin/thing 200\t\tapp.my8200.com",
    ]}))
    assert _hits.read(f) == {"DELETE /storage/v1/b/bucket/o/old.gz",
                             "POST /admin/thing"}, "undeclared: everything is kept"

    monkeypatch.setenv(_hits.HOSTS_ENV, "app.my8200.com")
    assert _hits.read(f) == {"POST /admin/thing"}


def test_an_older_recording_is_a_DID_NOT_RUN_for_accepted_not_a_zero(tmp_path):
    """This test used to assert the opposite, and the reasoning was wrong.

    It said an old recording "reports NOTHING accepted rather than everything"
    because "silent optimism is the failure to avoid here". Pessimism is not the
    answer to optimism — both are silence. Reporting zero accepted is a CLAIM,
    and it manufactured a false finding on IGA on 2026-09-13: a pin bump alone
    turned 3 never-accepted mutating controls into 20, every one of them a
    control whose recording held a 303 and no Location to judge it by. That is
    indistinguishable from a product regression, and a reader would have gone
    looking for one.

    The third answer is the one the rest of this kit already uses everywhere:
    treat it as DID NOT RUN and say so. Re-record.

    Mutation: replace the raise with `return set()` and this goes red.
    """
    f = tmp_path / "unit.json"
    f.write_text(json.dumps({"recorded": ["POST /admin/legacy"]}))
    with pytest.raises(_hits.StaleRecording):
        _hits.read(f)
    # TOUCHED needs only the path, so it is still answerable — refusing both
    # would delete a real measure to protect another one.
    assert _hits.read(f, accepted_only=False) == {"POST /admin/legacy"}


def test_the_three_counts_are_reported_separately(tmp_path):
    """NEVER TOUCHED, TOUCHED-BUT-REFUSED, ACCEPTED — and they are not the same.

    The estate reported two counts and collapsed the first pair. "Reached and
    refused" means a test is aimed at the control and the app said no; "never
    reached" means nothing has knocked on it at all. The second is the weaker
    position, and a single number hid which was which.

    And ACCEPTED IS NOT CORRECT. A 200 proves the handler did not raise; it says
    nothing about whether the right row changed. That is the journeys' standard
    and it is kept separate on purpose.

    Mutation: make `never_touched` fall back to `hit` and the middle row vanishes.
    """
    def provider(root):
        return [
            Gesture(template="t.html", kind="form", selector="form[POST /a]",
                    method="POST", action="/a", mutates="yes", why="declared"),
            Gesture(template="t.html", kind="form", selector="form[POST /b]",
                    method="POST", action="/b", mutates="yes", why="declared"),
            Gesture(template="t.html", kind="form", selector="form[POST /c]",
                    method="POST", action="/c", mutates="yes", why="declared"),
        ]
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "t.py").write_text("pass\n", encoding="utf-8")

    m = measure(tmp_path, corpus_dirs=("tests",), min_controls=1, min_corpus=1,
                population_fn=provider,
                recording={"POST /a"},                 # accepted
                touched={"POST /a", "POST /b"})        # /b reached and refused
    assert len(m.judgeable) == 3
    assert [g.action for g in m.touched_not_accepted] == ["/b"]
    assert [g.action for g in m.never_touched] == ["/c"]
    assert [g.action for g in m.unhit_mutating] == ["/b", "/c"]


def test_without_a_recording_all_three_counts_are_unknown(tmp_path):
    """An absent recording must not read as "nothing was ever touched"."""
    def provider(root):
        return [Gesture(template="t.html", kind="form", selector="form[POST /a]",
                        method="POST", action="/a", mutates="yes", why="declared")]
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "t.py").write_text("pass\n", encoding="utf-8")
    m = measure(tmp_path, corpus_dirs=("tests",), min_controls=1, min_corpus=1,
                population_fn=provider)
    assert m.recorded is False
    assert m.never_touched == [] and m.touched_not_accepted == [] and m.unhit_mutating == []


# ---------------------------------------------------------------------------
# The header. It carries the three counts and the accepted-is-not-correct
# sentence, because they had lived only in a commit message and a docstring.


def _measurement(recorded=True, hit=(), touched=(), judgeable=(), population=12):
    from qabench.gestures import Gesture, Measurement

    pop = [Gesture(template="t.html", kind="button", selector=f"c{i}", mutates="no")
           for i in range(population - 2)]
    pop += [Gesture(template="t.html", kind="form", selector="d1", mutates="yes"),
            Gesture(template="t.html", kind="form", selector="d2", mutates="yes")]
    q = "t.html::".__add__  # ids are template-qualified
    return Measurement(
        population=pop, corpus_files=30, driven={q("c0")}, undriven=[pop[1]],
        mutating_undriven=[pop[-1]], hit={q(x) for x in hit},
        judgeable={q(x) for x in judgeable}, touched={q(x) for x in touched},
        recorded=recorded)


def test_the_header_reports_the_three_counts_separately():
    """One number lets a repo work down the cheap half and call it progress.

    Mutation: collapse `never_touched` and `touched_not_accepted` into one
    count in `qabench/gestures.py::header` and this goes red.
    """
    from qabench.gestures import header

    m = _measurement(hit={"c0", "c1"}, touched={"c0", "c1", "c2"},
                     judgeable={"c0", "c1", "c2", "d1"})
    assert m.never_touched and m.touched_not_accepted, "the fixture proves nothing"
    text = header(m)
    assert "NEVER TOUCHED" in text
    assert "TOUCHED BUT NEVER ACCEPTED" in text
    # Each count appears as its own figure, and the unjudgeable remainder is
    # named as an unknown rather than folded into a total.
    assert f"{len(m.never_touched)} NEVER TOUCHED" in text
    assert f"{len(m.touched_not_accepted)} TOUCHED BUT NEVER ACCEPTED" in text
    assert f"{len(m.hit)} accepted" in text
    assert "UNKNOWN, not a pass" in text


def test_the_header_says_accepted_is_not_correct():
    """Rami asked for this sentence where it would be read, not in a commit.

    Mutation: delete the `ACCEPTED_IS_NOT_CORRECT` block from `header` and this
    goes red.
    """
    from qabench.gestures import ACCEPTED_IS_NOT_CORRECT, header

    text = header(_measurement(judgeable={"c0"}, hit={"c0"}, touched={"c0"}))
    # Wrapped, so compare word-wise rather than as one string.
    stripped = " ".join(line.lstrip("# ") for line in text.splitlines())
    for phrase in ("ACCEPTED IS NOT CORRECT", "does NOT mean the control did the "
                   "right thing", "STORED ROW"):
        assert phrase in stripped, phrase
    assert ACCEPTED_IS_NOT_CORRECT.split(".")[0] in stripped


def test_an_unrecorded_register_says_unknown_not_none():
    """A repo with no recording must not read as a clean one.

    Mutation: make `header` emit the recorded branch unconditionally and this
    goes red.
    """
    from qabench.gestures import header

    text = header(_measurement(recorded=False))
    assert "NO RECORDING" in text
    assert "must never be read as 'none'" in text
    assert "NEVER TOUCHED" not in text, "an unrecorded sweep cannot report counts"


def test_the_measured_limit_reaches_the_register():
    """anat's 373 unidentified controls belong here, not in a commit message."""
    from qabench.gestures import header

    limits = "373 of 973 controls carry no stable identifier."
    text = header(_measurement(judgeable={"c0"}), limits=limits)
    assert "WHAT THIS MEASURE CANNOT REACH IN THIS REPO" in text
    assert "373 of 973" in text
    # And absent when a repo declares none, rather than an empty heading.
    assert "CANNOT REACH" not in header(_measurement(judgeable={"c0"}))


def test_the_header_never_cuts_a_word():
    """Rami's standing rule. A register nobody can read is one nobody reads."""
    from qabench.gestures import header

    m = _measurement(hit={"c0"}, touched={"c0", "c1"}, judgeable={"c0", "c1", "d1"})
    text = header(m, limits="A" * 30 + " " + "B" * 40 + " short tail.")
    words = " ".join(line.lstrip("#").strip() for line in text.splitlines()).split()
    assert "A" * 30 in words and "B" * 40 in words, "a word was split across lines"
    assert all(len(line) <= 80 for line in text.splitlines()), "a line ran long"


def test_the_register_doc_carries_the_three_counts_as_data():
    """A count in a comment cannot be asserted by a guard; one in the doc can.

    Mutation: remove `never_touched` or `touched_not_accepted` from
    `register_doc` and this goes red.
    """
    from qabench.gestures import register_doc

    m = _measurement(hit={"c0"}, touched={"c0", "c1"},
                     judgeable={"c0", "c1", "c2", "d1"})
    doc = register_doc(m, {})
    assert doc["never_touched"] == len(m.never_touched)
    assert doc["touched_not_accepted"] == len(m.touched_not_accepted)
    assert doc["accepted"] == len(m.hit)
    # And they must actually differ here, or the fixture proves nothing.
    assert doc["never_touched"] and doc["touched_not_accepted"]
    assert doc["never_touched"] != doc["touched_not_accepted"]
    # The two sum to the unaccepted judgeable half — the invariant that makes
    # splitting them safe rather than just more numbers.
    assert doc["never_touched"] + doc["touched_not_accepted"] == (
        doc["judgeable"] - doc["accepted"])


def test_the_register_doc_keeps_a_reason_somebody_wrote():
    """A regeneration must not overwrite a human's sentence with a generated one."""
    from qabench.gestures import register_doc

    m = _measurement(judgeable={"c0"}, hit={"c0"}, touched={"c0"})
    mine = "Meir signs off: this one is driven from the handset, not the suite."
    old = {"undriven": [{"id": m.undriven[0].id, "reason": mine}]}
    doc = register_doc(m, old)
    assert doc["undriven"][0]["reason"] == mine


def test_the_summary_reports_three_numbers_not_one():
    """What a person reads in the terminal after `make gestures`.

    Mutation: drop `never_touched` from `summary_lines` and this goes red.
    """
    from qabench.gestures import summary_lines

    m = _measurement(hit={"c0"}, touched={"c0", "c1"},
                     judgeable={"c0", "c1", "c2", "d1"})
    text = " ".join(summary_lines(m))
    assert "never touched" in text
    assert "touched but never accepted" in text
    assert "accepted" in text
    assert "MUTATING never accepted" in text

    unrecorded = " ".join(summary_lines(_measurement(recorded=False)))
    assert "UNKNOWN here, not clean" in unrecorded
    assert "never touched" not in unrecorded


def test_the_manifest_block_carries_the_counts_and_the_caveat():
    """Gap 2's manifest half, generated so it cannot rot.

    Mutation: drop `caveat` from `manifest_coverage` and this goes red.
    """
    from qabench.gestures import COVERAGE_KEYS, manifest_coverage

    m = _measurement(hit={"c0"}, touched={"c0", "c1"},
                     judgeable={"c0", "c1", "c2", "d1"})
    cov = manifest_coverage(m, limits="373 of 973 carry no identifier.")
    for key in COVERAGE_KEYS:
        assert key in cov, key
    assert "ACCEPTED IS NOT CORRECT" in cov["caveat"]
    assert cov["limits"] == "373 of 973 carry no identifier."
    assert cov["never_touched"] == len(m.never_touched)
    assert cov["touched_not_accepted"] == len(m.touched_not_accepted)
    assert cov["mutating_never_accepted"] == len(m.unhit_mutating)


def test_an_unrecorded_manifest_block_is_null_not_zero():
    """Zero is a claim. Unknown is not, and the two must not look alike.

    Mutation: make `manifest_coverage` emit `len(...)` unconditionally and this
    goes red, because an unrecorded sweep would then claim zero of everything.
    """
    from qabench.gestures import manifest_coverage

    cov = manifest_coverage(_measurement(recorded=False))
    for key in ("judgeable", "never_touched", "touched_not_accepted", "accepted",
                "mutating_never_accepted"):
        assert cov[key] is None, f"{key} claims {cov[key]!r} with no recording"
    assert "NO RECORDING" in cov["caveat"]


def test_the_manifest_and_the_register_are_held_to_each_other():
    """Two files each internally consistent and disagreeing is the silent one.

    Mutation: make `coverage_disagreements` return `[]` unconditionally and the
    disagreement cases below go red.
    """
    from qabench.gestures import (coverage_disagreements, manifest_coverage,
                                  register_doc)

    m = _measurement(hit={"c0"}, touched={"c0", "c1"},
                     judgeable={"c0", "c1", "c2", "d1"})
    cov, reg = manifest_coverage(m), register_doc(m, {})
    assert coverage_disagreements({"coverage": cov}, reg) == []

    for key, wrong in (("accepted", 99), ("never_touched", 99),
                       ("touched_not_accepted", 99),
                       ("mutating_never_accepted", 99), ("population", 99)):
        broken = dict(cov, **{key: wrong})
        why = coverage_disagreements({"coverage": broken}, reg)
        assert any(key in line for line in why), (key, why)

    assert coverage_disagreements({}, reg), "a missing block must be a failure"
    assert coverage_disagreements(
        {"coverage": dict(cov, caveat="looks fine")}, reg), (
        "a block without the caveat must be a failure — it is the point of it")


# ---------------------------------------------------------------------------
# A recording too old to answer the question.


def _rec(tmp_path, rows, fmt=None):
    import json
    doc = {"recorded": rows, "count": len(rows)}
    if fmt is not None:
        doc["format"] = fmt
    p = tmp_path / "hits.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def test_an_old_recording_is_refused_for_the_ACCEPTED_question(tmp_path):
    """Reinterpreting it silently produced a 3 → 20 jump that looked like a defect.

    IGA's committed recording had `POST /admin/courses/create 303` with no
    Location column. `_acted` cannot judge a redirect without one, so it answered
    "not accepted" — and a pin bump alone turned 3 never-accepted mutating
    controls into 20, indistinguishable from a real regression.

    Mutation: drop the `StaleRecording` raise from `qabench/hits.py` and this
    goes red.
    """
    from qabench import hits

    old = _rec(tmp_path, ["POST /admin/courses/create 303", "GET / 200"])
    with pytest.raises(hits.StaleRecording) as refused:
        hits.read(old)
    assert "DID NOT RUN" in str(refused.value)
    assert "re-record" in str(refused.value)


def test_the_TOUCHED_question_is_still_answerable_from_an_old_recording(tmp_path):
    """Refusing both questions would be the over-correction.

    A path is all "has anything ever knocked on this" needs, and that is the
    count the estate uses to separate "nothing is aimed at it" from "reached and
    refused". Making it unavailable would delete a real measure to protect
    another one.

    Mutation: make the raise unconditional (drop `accepted_only and`) and this
    goes red.
    """
    from qabench import hits

    old = _rec(tmp_path, ["POST /admin/courses/create 303", "GET / 200"])
    touched = hits.read(old, accepted_only=False)
    assert "POST /admin/courses/create" in touched
    assert "GET /" in touched


def test_a_current_recording_is_read_normally(tmp_path):
    """Or the refusal above is just a way of never reading anything."""
    from qabench import hits

    now = _rec(tmp_path, ["POST /admin/x 200\t\tapp.local",
                          "POST /admin/y 303\t/admin/y/7\tapp.local",
                          "POST /admin/z 303\t/login?next=/admin/z\tapp.local"],
               fmt=hits.FORMAT)
    accepted = hits.read(now)
    assert "POST /admin/x" in accepted, "a 2xx must be accepted"
    assert "POST /admin/y" in accepted, "a redirect that is not to a login is accepted"
    assert "POST /admin/z" not in accepted, "a redirect to the login page is a refusal"


def test_the_format_is_inferred_from_the_rows_when_undeclared(tmp_path):
    """Every recording committed before 2026-09-13 declares nothing.

    Guessing from the rows beats assuming the newest: a row with no tab cannot
    carry a Location whatever the file says. And a file that DECLARES an old
    format is taken at its word even if its rows look newer — the declaration is
    the writer's, and the writer knows.
    """
    from qabench.hits import FORMAT, _inferred_format

    assert _inferred_format(["GET /x"]) == 1
    assert _inferred_format(["GET /x 200"]) == 2
    assert _inferred_format(["GET /x 200\t\tapp.local"]) == 3
    # An empty recording cannot be misread, so it is not the thing to refuse —
    # `write` already refuses to create one, and that is where it belongs.
    assert _inferred_format([]) == FORMAT


def test_a_written_recording_declares_its_format(tmp_path, monkeypatch):
    """Or the next reader is back to guessing.

    Mutation: drop `"format": FORMAT` from `write` and this goes red.
    """
    import json

    from qabench import hits

    monkeypatch.setattr(hits, "_seen", {"GET /x 200\t\tapp.local"})
    doc = hits.write(tmp_path / "out.json")
    assert doc["format"] == hits.FORMAT
    assert json.loads((tmp_path / "out.json").read_text())["format"] == hits.FORMAT


def test_the_split_is_NOT_MEASURED_rather_than_zero_when_only_accepted_is_given():
    """Two of the three counts were fabricated by a default argument.

    `measure(recording=...)` used to default `touched` to the ACCEPTED set — and
    every consumer passed only `recording`, so `touched_not_accepted` was always
    0 and `never_touched` absorbed both. eliad printed "7 never touched, 0
    touched but never accepted" on 2026-09-13 while its own recording held a
    `403` and a `307 -> /login` for six of the seven: the suite proves the guard
    refuses and has never proved the control works, which is the WORSE of the two
    states and the one that was being hidden.

    In the release that added the three counts. A default argument is enough to
    make a measure agree with itself.

    Mutation: restore `touched or recording` in `measure` and this goes red.
    """
    from qabench.gestures import header, manifest_coverage, register_doc

    m = _measurement(hit={"c0"}, judgeable={"c0", "c1", "c2"})
    m.touched = None                      # a caller that gave only `recording`
    assert not m.split_measured
    assert m.never_touched == [] and m.touched_not_accepted == []

    doc, cov = register_doc(m, {}), manifest_coverage(m)
    for key in ("never_touched", "touched_not_accepted"):
        assert doc[key] is None, f"register {key} claims {doc[key]!r}, not unknown"
        assert cov[key] is None, f"manifest {key} claims {cov[key]!r}, not unknown"
    assert doc["accepted"] == 1, "the accepted count IS measured and must survive"

    # Word-wise: the header wraps, so a sentence is not a contiguous string.
    flat = " ".join(line.lstrip("# ") for line in header(m).splitlines())
    assert "WAS NOT MEASURED" in flat
    assert "They are not zero; they are unknown." in flat
    assert "NEVER TOUCHED (no request" not in flat, "it reported a split it does not have"


def test_the_split_IS_reported_when_both_sets_are_given():
    """Or the guard above is a way of never reporting the split at all."""
    from qabench.gestures import header, manifest_coverage, register_doc

    m = _measurement(hit={"c0"}, touched={"c0", "c1"},
                     judgeable={"c0", "c1", "c2", "d1"})
    assert m.split_measured
    doc, cov = register_doc(m, {}), manifest_coverage(m)
    assert doc["never_touched"] == len(m.never_touched) > 0
    assert doc["touched_not_accepted"] == len(m.touched_not_accepted) > 0
    assert cov["never_touched"] == doc["never_touched"]
    assert "NEVER TOUCHED" in header(m)
    assert "WAS NOT MEASURED" not in header(m)


def test_measure_does_not_infer_the_touched_set_from_the_accepted_one(tmp_path):
    """Through `measure` itself, which is where the default argument lived.

    The test above proves the PROPERTIES are tri-state; it sets `touched` on the
    object and so never exercises `measure`'s signature — and a mutation
    restoring `touched or recording or set()` passed it. This one drives the
    actual path: a caller giving only `recording` must get `touched=None`, and a
    caller giving both must get both.

    Mutation: restore `touched or recording or set()` in `measure` and the first
    assertion goes red.
    """
    tmpl = {"a.html": '<form id="f" method="post" action="/admin/x"></form>'}
    _repo(tmp_path, tmpl, {"t.py": "# names #f"})

    only_accepted = measure(tmp_path, min_controls=1, min_corpus=1,
                            recording={"POST /admin/x"})
    assert only_accepted.touched is None, (
        "measure inferred the touched set from the accepted one — two of the "
        "three counts are then fabricated, which is what eliad reported")
    assert not only_accepted.split_measured
    assert only_accepted.hit, "the accepted set must still be read"

    both = measure(tmp_path, min_controls=1, min_corpus=1,
                   recording={"POST /admin/x"}, touched={"POST /admin/x"})
    assert both.split_measured
    assert both.touched == both.hit, "both sets were given and both were read"


@pytest.mark.parametrize(
    "location,acted,why",
    [
        ("/login?reset=1", True,
         "my8200's password reset: it WORKED and ends at the login page"),
        ("/login?changed=1&ok", True, "any flow that finishes at the login page"),
        ("/login?next=/admin/x", False, "the commonest refusal there is"),
        ("/accounts/login/?next=/x", False, "the same, with a trailing slash"),
        ("/login?next=", False, "a bounce with an empty next is still a bounce"),
        ("/login", False, "a bare bounce to the login page"),
        ("/login/", False, "the same, trailing slash"),
        ("/admin/purchase-orders/1", True, "the thing that was just created"),
        ("", False, "a redirect with no Location decides nothing"),
    ],
)
def test_a_flow_that_ENDS_at_the_login_page_is_not_a_refusal(location, acted, why):
    """A login redirect is a refusal when it carries "come back afterwards".

    The rule was "any redirect to a login path is a refusal", and that is wrong
    for every flow whose SUCCESS ends at the login page. Measured on my8200,
    2026-09-13: `POST /reset/<token>` answered `303 -> /login?reset=1` — the
    password reset worked — and the register reported the control as never once
    accepted. A false negative that reads as a defect, which costs the same as the
    false positive this line of work started from.

    The distinction is the bounce parameter, not the presence of a query:
    `/login?next=/admin/x` is the commonest refusal in the estate and a rule that
    read "has a query" as success would credit every unauthenticated probe.

    Mutation: drop the `BOUNCE_PARAMS` test from `_is_login_bounce` and the
    refusal rows go red; make it `return True` and the success rows do.
    """
    from qabench.hits import _acted

    assert _acted(303, location) is acted, why


def test_a_307_is_still_not_the_app_acting():
    """Unchanged by the above: the body had not been read yet."""
    from qabench.hits import _acted

    assert _acted(307, "/login?reset=1") is False
    assert _acted(308, "/admin/x") is False


def test_each_xdist_worker_writes_its_own_recording(monkeypatch):
    """One path plus many workers means the last to finish wins.

    Every xdist worker is a separate process with its own `_seen`, and every one
    runs `pytest_sessionfinish`. Measured on anat, 2026-09-13: 973 distinct
    requests recorded serially, **61** from the same suite under `-n auto` — one
    worker's share of 13,175 tests. Nothing failed; the register would simply
    have reported hundreds of controls as never accepted, which is the shape of a
    product regression rather than of a lost file.

    Every repo in the estate whose `hits` target inherits `WORKERS ?= auto` was
    recording this way.

    Mutation: make `worker_target` return its argument unchanged and this goes
    red — both workers claim the same path.
    """
    from qabench.hits import worker_target

    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    assert worker_target("qa/hits/unit.json") == "qa/hits/unit.json", (
        "a serial run must keep the plain name, or every committed recording is "
        "orphaned by this change")

    seen = set()
    for w in ("gw0", "gw1", "gw11"):
        monkeypatch.setenv("PYTEST_XDIST_WORKER", w)
        got = worker_target("qa/hits/unit.json")
        assert got != "qa/hits/unit.json", f"{w} would overwrite the shared file"
        assert got.endswith(".json"), got
        assert w in got, got
        seen.add(got)
    assert len(seen) == 3, f"two workers share a path: {seen}"


def test_the_union_reads_per_worker_files_back(tmp_path):
    """The per-worker names are only safe because a DIRECTORY read unions them.

    That is why the fix is a filename rather than a merge protocol with a lock:
    `read()` already had the behaviour this depends on.
    """
    import json

    from qabench import hits

    d = tmp_path / "hits"
    d.mkdir()
    for w, path in (("gw0", "POST /a 200"), ("gw1", "POST /b 200")):
        (d / f"unit.{w}.json").write_text(json.dumps(
            {"format": hits.FORMAT, "recorded": [f"{path}\t\tapp"], "count": 1}))

    assert hits.read(d) == {"POST /a", "POST /b"}, (
        "the per-worker files did not union — a worker's share would be lost at "
        "READ time instead of at write time, which is the same defect moved")


def test_the_per_worker_files_merge_into_one_and_vanish(tmp_path):
    """Per-worker names solve the overwrite; committing them recreates it.

    `-n auto` reads the machine, so a fourteen-core laptop writes `unit.gw0..13`
    and an eight-core runner writes `unit.gw0..7` — leaving six stale files the
    directory union keeps reading as current, indefinitely. A recording whose
    staleness is invisible is the whole defect being fixed today; putting it in
    the filenames would be reintroducing it one layer out.

    Mutation: drop the `f.unlink()` loop and this goes red on the leftovers.
    """
    import json

    from qabench import hits

    d = tmp_path / "hits"
    d.mkdir()
    for w, row in (("gw0", "POST /a 200"), ("gw1", "POST /b 200"), ("gw11", "POST /a 200")):
        (d / f"unit.{w}.json").write_text(json.dumps(
            {"format": hits.FORMAT, "recorded": [f"{row}\t\tapp"], "count": 1}))

    out = hits.merge_workers(str(d / "unit.json"))
    assert out["workers"] == 3
    assert out["count"] == 2, f"duplicates across workers must collapse: {out}"
    assert (d / "unit.json").is_file()
    assert not list(d.glob("unit.gw*.json")), (
        "the per-worker files survived — a later run on a machine with fewer "
        "workers would inherit the extras and read them as current")
    assert hits.read(d) == {"POST /a", "POST /b"}


def test_merging_nothing_is_a_refusal_not_an_empty_file(tmp_path):
    """Absent per-worker files mean serial, or a plugin that never loaded.

    Either way the answer is a sentence, not a zero — writing an empty recording
    would mark every control unhit on the next read.
    """
    import pytest as _pytest

    from qabench import hits

    d = tmp_path / "hits"
    d.mkdir()
    with _pytest.raises(RuntimeError) as e:
        hits.merge_workers(str(d / "unit.json"))
    assert "DID NOT RUN" in str(e.value)
    assert not (d / "unit.json").exists(), "it wrote a file anyway"


def test_raw_browser_lines_fold_into_one_recording(tmp_path):
    """The browser recorder appends; the register reads JSON. This joins them.

    A browser recorder cannot use `write()` — it has no session end it controls,
    and a crashed spec must still leave what it reached behind — so it appends one
    line per response to a `.raw` file. Naming an append-log `.json` would be a
    format lie and `read()` would choke on it.

    Mutation: drop the `f.unlink()` loop and the leftovers assertion goes red;
    remove the no-parts refusal and the empty case does.
    """
    from qabench.hits import FORMAT, fold_raw, read

    (tmp_path / "e2e.browser-gw0.raw").write_text(
        "POST /admin/x 200\t\tapp\nPOST /admin/y 303\t/login?next=/a\tapp\n")
    (tmp_path / "e2e.browser-gw1.raw").write_text(
        "POST /admin/x 200\t\tapp\nPOST /admin/z 303\t/admin/z/7\tapp\n")

    out = fold_raw(str(tmp_path / "e2e.json"))
    assert out["raw_files"] == 2
    assert out["count"] == 3, f"duplicates across workers must collapse: {out}"
    assert out["format"] == FORMAT
    assert not list(tmp_path.glob("*.raw")), "the raw files survived the fold"

    accepted = read(tmp_path)
    assert "POST /admin/x" in accepted, "a 2xx from the browser must count"
    assert "POST /admin/z" in accepted, "a redirect to the new record is accepted"
    assert "POST /admin/y" not in accepted, "a bounce to login is a refusal"


def test_folding_nothing_is_a_refusal(tmp_path):
    """An empty browser recording would mark every control unhit."""
    import pytest as _pytest

    from qabench.hits import fold_raw

    with _pytest.raises(RuntimeError) as e:
        fold_raw(str(tmp_path / "e2e.json"))
    assert "DID NOT RUN" in str(e.value)
    assert not (tmp_path / "e2e.json").exists()

    (tmp_path / "e2e.browser.raw").write_text("\n\n")
    with _pytest.raises(RuntimeError) as e2:
        fold_raw(str(tmp_path / "e2e.json"))
    assert "not one line" in str(e2.value)


@pytest.mark.parametrize(
    "where, location, acted, why",
    [
        ("POST /logout", "/login", True, "signing out and landing on the login page is the logout WORKING"),
        ("POST /logout", "/login/", True, "the same, trailing slash"),
        ("POST /auth/logout", "/auth/login", True, "a declared-shape logout under a prefix"),
        ("POST /logout", "/login?next=/admin", False, "a logout that bounces with 'come back' did not sign anyone out"),
        ("POST /admin/crm/2", "/login", False, "any other control landing on the login page is still a refusal"),
        ("", "/login", False, "no request path decides nothing"),
    ],
)
def test_a_logout_that_lands_on_the_login_page_is_the_logout_working(where, location, acted, why):
    """eliad, 2026-09-14: `POST /logout 303 -> /login` was recorded on every run
    and the register said the control had never once been accepted — through
    two re-records. The bounce rule reads a bare login path as a refusal, which
    is right for every control except the one whose job is to put you there.
    The request path is the evidence. Mutation: drop the `_is_logout` clause in
    `_acted` and the first three rows go red."""
    from qabench.hits import _acted

    assert _acted(303, location, where) is acted, why


def test_a_repo_can_declare_where_it_signs_out(monkeypatch):
    from qabench.hits import _acted
    monkeypatch.setenv("QABENCH_LOGOUT_PATHS", "/bye")
    assert _acted(303, "/login", "POST /bye") is True
    assert _acted(303, "/login", "POST /logout") is False, "declaring replaces the defaults, it does not add to them"


# ── #687: a control we cannot NAME is unmeasured, not undriven ───────────────


def test_a_nameless_control_is_unmeasured_not_undriven(tmp_path):
    """The heart of #687.

    A button with no id, data-action, name or data-testid gets an occurrence
    index for a key. That key moves the moment markup is inserted above it, so
    counting it as "driven by nothing" was wrong in both directions: a control a
    recording HAD driven stopped matching and read as never driven, and the
    shifted index carried the old one's hit record onto a different control.

    Measured on anat: adding one card to a page moved judgeable 125 -> 124 and
    accepted 84 -> 83 while the population stayed at 975 — nothing gained,
    nothing lost, one control simply stopped being recognised.
    """
    _repo(tmp_path,
          {"a.html": '<button id="named" onclick="go()">x</button>'
                     '<button onclick="go()">nameless</button>'},
          {"t.py": "pass"})
    m = measure(tmp_path, min_controls=1, min_corpus=1)
    ids_undriven = {g.id for g in m.undriven}
    ids_unmeasured = {g.id for g in m.unmeasured}
    assert any("named" in i for i in ids_undriven), ids_undriven
    assert any("?positional" in i for i in ids_unmeasured), ids_unmeasured
    assert not any("?positional" in i for i in ids_undriven), (
        "a control the sweep could not name is still counted as driven by "
        "nothing — that is a measurement failure reported as a finding")


def test_the_ceiling_stops_counting_what_it_cannot_name(tmp_path):
    """The practical consequence, and the reason this was urgent: the undriven
    ratchet only falls, and a nameless control cannot be credited to a test — so
    adding one button to a page of nameless controls could not be offset by
    driving one, and the change could not land at all.

    A gate nobody can satisfy teaches people to override it.
    """
    _repo(tmp_path,
          {"a.html": "".join('<button onclick="go()">x</button>' for _ in range(5))},
          {"t.py": "pass"})
    m = measure(tmp_path, min_controls=1, min_corpus=1)
    assert m.ceiling == 0, (
        f"the ceiling still counts {m.ceiling} controls it cannot name")
    assert m.unmeasured_count == 5


def test_a_mutating_control_we_cannot_name_is_not_quietly_exempt(tmp_path):
    """The half that must NOT get easier. A control that changes something and
    cannot even be named is the worst row in the register, not an exempt one —
    so it moves to its own list rather than disappearing.
    """
    _repo(tmp_path,
          {"a.html": '<form method="post" action="/admin/x/purge"></form>'},
          {"t.py": "pass"})
    m = measure(tmp_path, min_controls=1, min_corpus=1)
    nameless_mutators = [g for g in m.unmeasured if g.mutates == "yes"]
    assert nameless_mutators or m.mutating, (
        "a mutating control vanished from both lists — it must be in one of them")
    assert {g.id for g in m.mutating_unmeasured} == {g.id for g in nameless_mutators}


def test_the_register_says_how_much_it_did_not_speak_for(tmp_path):
    """A verdict without its discriminating subset is an optimistic number: the
    reader assumes the rest is fine, and the rest is unknown."""
    from qabench.gestures import register_doc
    _repo(tmp_path,
          {"a.html": '<button id="named" onclick="go()">x</button>'
                     '<button onclick="go()">nameless</button>'},
          {"t.py": "pass"})
    m = measure(tmp_path, min_controls=1, min_corpus=1)
    doc = register_doc(m, {})
    assert doc["unmeasured"] == 1, doc
    assert "unmeasured_mutating" in doc
