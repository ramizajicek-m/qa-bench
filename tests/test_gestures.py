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


def test_a_control_that_got_driven_must_leave_the_register(tmp_path):
    """A stale exemption is how a list stops describing the thing it exempts."""
    _repo(tmp_path, {"a.html": '<button id="b" onclick="go()">x</button>'},
          {"t.py": "page.click('#b')"})
    m = measure(tmp_path, min_controls=1, min_corpus=1)
    old = {"ceiling": 1, "mutating": 0,
           "undriven": [{"id": "a.html::button[id=b]", "mutates": "unknown", "reason": "r"}]}
    assert any("now driven, remove it" in r for r in refusals(m, old))


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
