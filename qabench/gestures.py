"""Every control a person can operate, lifted from the templates themselves.

WHY THIS EXISTS. Every enumerator in this estate derives its population from
SOURCE CODE — the mounted route table, an AST walk, or a regex over templates
for URL string literals. So the population is the one the author had in mind,
and the defects live in what the author did not have in mind. The whole of one
week's user-reported defects said the same sentence in their fix: *nothing had
ever driven that button*.

A URL lifter cannot close that. anat's `template_paths.py` scans for `/api/...`
string literals; its own docstring records that the field app's job transition,
notes, materials and photos are "driven but never lifted here", because their
URLs are composed at runtime. The control exists on the page and in no
population.

So this lifts CONTROLS, not URLs: the things a person can press.

PARSED, NOT REGEXED — and tolerant of Jinja. A regex cannot tell an attribute
from text that looks like one, which is how a comment became a value and a
ticket reference became a colour elsewhere in this estate. But a strict XML
parser is worse: `lxml` on a Jinja template fails on `{% if %}` and on unquoted
`{{ }}` inside attributes, and a checker that calls clean templates broken gets
switched off within a day (anat, 2026-08-23: a `node --check` oracle reported 19
clean templates broken because it did not substitute Jinja first). Stdlib
`html.parser` is deliberately lenient; Jinja is neutralised before it runs, and
neutralised in a way that PRESERVES attribute structure rather than deleting it.

It also adds no dependency to six repositories, which `lxml` would.

WHAT COUNTS AS A GESTURE. A control that can change stored state:

  * a `<form>` whose method is POST/PUT/PATCH/DELETE — the form IS the gesture,
    and its submit button is not counted separately;
  * a `<button>`, `[data-action]` or `[onclick]` that is NOT inside such a form
    — a candidate, because whether it mutates depends on its handler.

A candidate whose handler cannot be resolved is reported `unknown` and must be
listed with a reason. It is NEVER silently dropped: an unclassified control is
the exact thing this file exists to stop disappearing. `data-toggle`,
`data-reset` and friends are real controls but change nothing stored, so the
classifier must be able to say so out loud rather than by omission.

KEYS DO NOT MOVE. A gesture's id is its template path plus a stable selector —
an `id`, a `data-action`, a `name`, or the action+method of a form. NEVER a line
number: anat's line-keyed exemptions broke four times in one morning, every time
because something was added ABOVE them, and a drifted line silently exempts
whatever now sits on it.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from html.parser import HTMLParser
from pathlib import Path

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Jinja statements ({% %}) carry no attribute structure and are removed. Jinja
# expressions ({{ }}) very often ARE an attribute's value — `action="/issue/{{
# c.alloc_number }}/sign"` — so they collapse to a single placeholder token
# instead, which keeps the quoting intact and makes two renderings of the same
# control compare equal.
_JINJA_STMT = re.compile(r"\{%.*?%\}", re.S)
_JINJA_EXPR = re.compile(r"\{\{.*?\}\}", re.S)
_JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)
PLACEHOLDER = "{}"


def neutralise_jinja(src: str) -> str:
    """Template source an HTML parser can read, with attribute structure kept.

    `{{ x }}` becomes `{}` rather than vanishing, so `action="/a/{{ i }}/b"`
    stays a quoted attribute and normalises to `/a/{}/b` — the same key
    whichever row rendered it.
    """
    src = _JINJA_COMMENT.sub("", src)
    src = _JINJA_STMT.sub("", src)
    return _JINJA_EXPR.sub(PLACEHOLDER, src)


@dataclass
class Gesture:
    """One control, keyed on something an edit cannot move."""
    template: str
    kind: str                 # "form" | "button" | "action" | "link"
    selector: str             # the stable key within the template
    method: str = ""          # for forms
    action: str = ""          # for forms
    mutates: str = "unknown"  # "yes" | "no" | "unknown"
    why: str = ""
    #: Extra literal tokens that count as NAMING this control, for populations
    #: that are not markup. A template control is named by its id or its action;
    #: a registry entry is named by its declared name or its handler function.
    #: Supplying them here keeps ONE matcher for every project rather than a
    #: second guard with a second rule — which is how ana-log ended up with a
    #: bespoke copy that drifted.
    names: tuple = ()

    @property
    def id(self) -> str:
        return f"{self.template}::{self.selector}"


def _attr(attrs, name):
    for k, v in attrs:
        if k == name:
            return v or ""
    return None


def _stable_selector(tag, attrs) -> tuple[str, str]:
    """(selector, how) — the first attribute an edit is unlikely to move.

    Order matters: an explicit id or data-action is authored deliberately, a
    name is next, and only then do we fall back to a positional key. The
    fallback is the weak one and says so in `how`, because a positional key
    behaves like a line number the moment two controls are reordered.
    """
    for name in ("id", "data-action", "name", "data-testid"):
        got = _attr(attrs, name)
        if got:
            return f"{tag}[{name}={got}]", name
    return "", ""


class _Lifter(HTMLParser):
    """Collects controls, tracking the forms we are inside.

    `convert_charrefs` is left on: entity text does not affect which controls
    exist, and turning it off changes nothing here except noise.
    """

    def __init__(self, template: str):
        super().__init__()
        self.template = template
        self.found: list[Gesture] = []
        #: One record per OPEN form. A form's row is emitted at its END tag, not
        #: its start, because its identity depends on what is inside it — see
        #: `_finish_form`.
        self._forms: list[dict] = []
        self._counter: dict[str, int] = {}
        self._in_script = False
        #: Inline handler source from THIS template. anat wires 907 of its 914
        #: controls in an inline <script>, so a classifier that reads only
        #: static/js/ resolves none of them and every control stays `unknown` —
        #: a population of 900 unknowns is a wall, not a signal.
        self.scripts: list[str] = []

    # -- helpers ------------------------------------------------------------
    def _key(self, tag, attrs) -> str:
        sel, how = _stable_selector(tag, attrs)
        if sel:
            return sel
        # No stable attribute. Use an occurrence index and mark it, so the
        # register shows which keys are fragile rather than pretending they
        # are not.
        n = self._counter.get(tag, 0)
        self._counter[tag] = n + 1
        return f"{tag}#{n}?positional"

    def _open_form(self):
        return self._forms[-1] if self._forms else None

    # -- tags ---------------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self._in_script = True
            return

        if tag == "form":
            method = (_attr(attrs, "method") or "GET").upper()
            sel, _ = _stable_selector(tag, attrs)
            self._forms.append({
                "method": method,
                "action": _attr(attrs, "action") or "",
                "selector": sel,
                "mutating": method in MUTATING_METHODS,
                #: Hidden fields carrying a LITERAL value. Five forms posting to
                #: the same route with hidden action=rename/up/down/delete are
                #: five controls, not one; without this they share an id and
                #: driving `rename` reports `delete` as driven. Found on my8200,
                #: where 33 controls collapsed into 20 ids and one of the hidden
                #: values was `delete`.
                "hidden": [],
                #: Whether this form will produce a row of its own. When it will
                #: not, its submit buttons must be lifted instead of swallowed.
                "lifted": method in MUTATING_METHODS or bool(sel),
            })
            return

        form = self._open_form()

        if tag == "input":
            if (_attr(attrs, "type") or "").lower() == "hidden" and form is not None:
                name, value = _attr(attrs, "name"), _attr(attrs, "value")
                # A value built by Jinja is the PLACEHOLDER after neutralisation
                # and distinguishes nothing, so only literals count.
                if name and value and PLACEHOLDER not in value:
                    form["hidden"].append(f"{name}={value}")
            btype = (_attr(attrs, "type") or "").lower()
            if btype in ("button", "image", "submit"):
                self._maybe_button(tag, attrs, btype)
            return

        if tag == "button":
            self._maybe_button(tag, attrs, (_attr(attrs, "type") or "submit").lower())
            return

        if _attr(attrs, "data-action") is not None or _attr(attrs, "onclick") is not None:
            if tag in ("button", "form", "input"):
                return  # already handled
            self.found.append(self._candidate(tag, attrs))

    def _maybe_button(self, tag, attrs, btype):
        """A submit is usually its form; a `formaction` submit never is."""
        form = self._open_form()
        formaction = _attr(attrs, "formaction")
        if formaction:
            # `<button type=submit formaction="/admin/x/{}/delete">` inside a
            # save form posts somewhere ELSE entirely. Swallowing it into the
            # parent hid three DELETEs in tharros and two in my8200 — the
            # routes exist, and the population did not know the buttons did.
            method = (_attr(attrs, "formmethod")
                      or (form or {}).get("method") or "GET").upper()
            sel, _ = _stable_selector(tag, attrs)
            self.found.append(Gesture(
                template=self.template, kind="form",
                selector=sel or f"{tag}[{method} {formaction}]",
                method=method, action=formaction,
                mutates="yes" if method in MUTATING_METHODS else "unknown",
                why=f"<{tag} formaction> submits to {formaction}, not to its form"))
            return
        if btype == "submit" and form is not None:
            # Either the form above IS this gesture, or the form is a plain GET
            # search box with nothing to intercept it — in both cases the button
            # is not a separate control.
            #
            # THE LIMIT, stated: a form with no method, no id, no name and no
            # data-* attribute that is nonetheless submitted from JS is invisible
            # to this lifter, and so is its button. Nothing selects it, so there
            # is no key to give it. Giving such a form an id is the fix, and that
            # is also what a Playwright locator would need.
            return
        self.found.append(self._candidate(tag, attrs))

    def _candidate(self, tag, attrs) -> Gesture:
        onclick = _attr(attrs, "onclick") or ""
        data_action = _attr(attrs, "data-action")
        mutates, why = "unknown", "handler not resolved from markup alone"
        # The only classification safe to make from markup: a handler whose
        # whole body is a browser-local call changes nothing stored. Anything
        # else needs the JS, which `classify_with_js` supplies.
        if onclick and re.fullmatch(r"\s*(window\.)?(print|close|history\.back)\(\s*\)\s*;?\s*", onclick):
            mutates, why = "no", f"onclick is a browser-local call: {onclick.strip()}"
        elif data_action is None and not onclick:
            mutates, why = "unknown", "a button with no handler in the markup (wired in JS)"
        return Gesture(template=self.template, kind="button" if tag in ("button", "input") else "action",
                       selector=self._key(tag, attrs), mutates=mutates, why=why)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        if self._in_script:
            self.scripts.append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False
        if tag == "form" and self._forms:
            self._finish_form(self._forms.pop())

    def close(self):
        super().close()
        # An UNCLOSED form — `{% if %}<form>{% else %}<div>{% endif %}` becomes
        # unbalanced tags once Jinja is neutralised — must still produce its row.
        # Left open, it also swallowed every later submit in the template.
        while self._forms:
            self._finish_form(self._forms.pop())

    def _finish_form(self, form: dict):
        if not form["lifted"]:
            return
        method, action = form["method"], form["action"]
        # A form's identity is what it DOES — its method, where it posts, and
        # any literal hidden field that decides which operation it is.
        base = form["selector"] or f"form[{method} {action or '(self)'}]"
        if form["hidden"]:
            base += "{" + ",".join(sorted(form["hidden"])) + "}"
        if form["mutating"]:
            mutates = "yes"
            why = f"<form method={method}> submits to {action or 'its own URL'}"
        else:
            # NOT a GET search box: a form with no mutating method but with a
            # stable attribute is the shape a script intercepts. anat has 75
            # form tags and only 7 declare a mutating method; 58 of the other 68
            # carry an id and are submitted by `fetch(..., {method: 'POST'})`.
            # Calling those non-mutating removed the DOMINANT way that product
            # changes state from the population entirely.
            mutates = "unknown"
            why = ("a form with no mutating method but a stable attribute — "
                   "submitted from JS, or a genuine GET; the classifier decides")
        self.found.append(Gesture(
            template=self.template, kind="form", selector=base,
            method=method, action=action, mutates=mutates, why=why))


def lift_template(path: Path, root: Path) -> tuple[list[Gesture], str]:
    """(controls, the template's own inline script source)."""
    rel = str(path.relative_to(root))
    lifter = _Lifter(rel)
    lifter.feed(neutralise_jinja(path.read_text(encoding="utf-8", errors="replace")))
    lifter.close()
    return lifter.found, "\n".join(lifter.scripts)


def lift(template_root: Path, glob: str = "**/*.html") -> list[Gesture]:
    """Every control in every template, sorted so the register is stable."""
    root = Path(template_root)
    out: list[Gesture] = []
    for p in sorted(root.glob(glob)):
        found, _ = lift_template(p, root)
        out.extend(found)
    return sorted(out, key=lambda g: g.id)


def lift_with_scripts(template_root: Path, glob: str = "**/*.html"
                      ) -> tuple[list[Gesture], dict[str, str]]:
    """Controls, plus each template's own inline script keyed by template.

    Use this over `lift` wherever handlers are written inline: it lets the
    classifier look in the RIGHT template rather than in one shared blob, so a
    control named `save` in one page is not resolved by an unrelated `save` in
    another.
    """
    root = Path(template_root)
    out: list[Gesture] = []
    scripts: dict[str, str] = {}
    for p in sorted(root.glob(glob)):
        found, src = lift_template(p, root)
        out.extend(found)
        if src.strip():
            scripts[str(p.relative_to(root))] = src
    return sorted(out, key=lambda g: g.id), scripts


# --- the JS half -----------------------------------------------------------
# A button wired in JS is the majority case and the one a URL lifter misses.
# We resolve it the only way markup allows: find the handler that selects this
# control and ask whether that handler reaches a mutating call.

#: A call that CHANGES something, as opposed to any call at all.
#:
#: The first version matched `fetch(` outright, so every read counted. anat's
#: `ae-refresh`, `ap-refresh` and `next-btn` — a refresh and a pagination
#: button — were reported as MUTATING, and the `mutating` ceiling, which exists
#: to be the number that matters, inherited the overclaim.
#:
#: Demoting an unproven call to `unknown` is safe in the way this module
#: requires: `unknown` stays in the population and still owes a test. What must
#: never happen is calling a mutating control `no`, which would remove it
#: silently, and nothing here does that.
_MUTATING_CALL = re.compile(
    r"""method\s*:\s*['"](POST|PUT|PATCH|DELETE)['"]"""
    r"""|\.(post|put|patch|delete)\s*\("""
    r"""|(apiFetch|axios)\s*\(\s*['"][^'"]*['"]\s*,\s*\{[^}]*method""",
    re.I)


def classify_with_js(gestures: list[Gesture], js_sources: dict[str, str]) -> list[Gesture]:
    """Upgrade `unknown` candidates by reading the scripts that wire them.

    Deliberately conservative in ONE direction: it may leave a mutating control
    `unknown`, and it must never call a mutating control `no`. An overclaim here
    removes a real gesture from the population silently, which is the failure
    this module exists to prevent; an underclaim only leaves a row needing a
    reason.
    """
    shared = "\n".join(v for k, v in js_sources.items() if not k.endswith(".html"))
    # Built ONCE per template, not once per control. The first version
    # concatenated `shared` (12 MB on anat) for each of 907 gestures and did not
    # finish in ten minutes — and a checker nobody will wait for is a checker
    # nobody runs.
    per_template: dict[str, str] = {}

    def blob_for(template: str) -> str:
        if template not in per_template:
            per_template[template] = js_sources.get(template, "") + "\n" + shared
        return per_template[template]

    for g in gestures:
        if g.mutates != "unknown":
            continue
        token = re.search(r"\[(?:data-action|id|name|data-testid)=([^\]]+)\]", g.selector)
        if not token:
            continue
        # The control's OWN template first, then the shared scripts. Searching
        # one global blob lets a `save` in an unrelated page resolve a `save`
        # here — the same substring-collision that makes one surface stand in
        # for another in the coverage half.
        blob = blob_for(g.template)
        needle = re.escape(token.group(1))
        # The handler's neighbourhood: from where the control is selected to the
        # end of that statement block. A window is a blunt instrument, so it is
        # generous and the verdict stays "unknown" when nothing matches — a
        # window that swallows its subject is a documented failure here.
        for m in re.finditer(needle, blob):
            window = blob[m.start():m.start() + 1200]
            if _MUTATING_CALL.search(window):
                g.mutates = "yes"
                g.why = "its handler reaches a mutating call"
                break
    return gestures


# --- the register ----------------------------------------------------------

def population(gestures: list[Gesture]) -> list[Gesture]:
    """The ones that must be driven: mutating, plus every unresolved candidate.

    `unknown` is IN the population on purpose. Excluding it would make the
    number look better every time the classifier got worse, which is the
    degenerate direction — the count would fall for the wrong reason.

    UNIQUE BY ID, and that is not cosmetic. The id IS the control's key, so two
    rows sharing one are the same control (the same form rendered twice in a
    template). While this returned duplicates, a generator counting a list and a
    consumer counting a set disagreed by exactly the number of repeats — on
    my8200, 60 against 59 — and that gap is free slack a new undriven control
    can hide in. It did: a single-control mutation failed to breach the ratchet.
    One definition, so the two cannot drift.
    """
    seen: dict[str, Gesture] = {}
    for g in gestures:
        if g.mutates in ("yes", "unknown") and g.id not in seen:
            seen[g.id] = g
    return list(seen.values())


def uncovered(gestures: list[Gesture], covered_ids: set[str]) -> list[Gesture]:
    return [g for g in population(gestures) if g.id not in covered_ids]


def render(gestures: list[Gesture]) -> str:
    """The register, as stable JSON — one row per control."""
    return json.dumps([asdict(g) for g in sorted(gestures, key=lambda g: g.id)],
                      indent=2, ensure_ascii=False) + "\n"


# --- coverage ---------------------------------------------------------------

def _static_segments(action: str) -> list[str]:
    """The parts of an action a caller must type literally.

    `/admin/users/{}/deactivate` -> ['/admin/users/', '/deactivate']. Query
    strings are dropped: a caller may build them differently and still be
    driving the same control.
    """
    action = action.split("?", 1)[0]
    return [s for s in action.split(PLACEHOLDER) if s.strip("/ ")]


#: How far apart the literal halves of an action may sit and still count as one
#: call. Wide enough for `f"/admin/courses/{c.id}/delete"` and for
#: `"/admin/courses/" + cid + "/delete"`; far too narrow to bridge two unrelated
#: URLs on different lines, which is what made the segments-anywhere test wrong.
_GAP = r"[^\n]{0,120}?"


def _action_pattern(action: str):
    """One regex the whole action must match, in order, on ONE line.

    THE DEFECT THIS REPLACES. The first version asked whether every static
    SEGMENT appeared somewhere in one concatenated blob, each independently.
    `/admin/courses/{}/archive` was therefore "driven" by an unrelated public
    `/archive` page test plus any mention of `/admin/courses/`. Measured on
    IGA, a single probe file whose entire content was the docstring
    "posts to /issue/passkeys/1/delete" healed THREE rows at once — passkeys
    delete, courses delete and documents delete — because `/delete` is a
    segment they share. my8200 had four live examples, two of them destructive:
    `/admin/vouchers/{}/cancel` was satisfied by `/booking/{token}/cancel`.

    A test that drives a control writes that control's URL. Requiring the whole
    path, with the placeholder standing for one run of non-whitespace, asks for
    exactly that and nothing weaker.
    """
    action = action.split("?", 1)[0].rstrip("/")
    parts = [re.escape(p) for p in action.split(PLACEHOLDER)]
    return re.compile(_GAP.join(parts))


def _identifier_pattern(token: str):
    """A bare identifier, bounded. For tokens a PROVIDER chose deliberately.

    A handler function name like `create_shipment` is written bare in the code
    that calls it, so it carries no quote or `#`. It also does not collide with
    prose the way a markup id like `submit` does, which is why the two rules are
    different and the strict one is reserved for ids scraped out of markup.
    """
    return re.compile(r"(?<![\w-])" + re.escape(token) + r"(?![\w-])")


def _token_pattern(token: str):
    """The token as an author writes it in a selector or a string, not as prose.

    Two live failures made this necessary. anat's `button[id=ai-btn]` was
    "driven" by `#bp-ai-btn`, `#fn-ai-btn` and `#tr-ai-btn` with zero
    whole-token hits — a substring of three OTHER controls' ids. And
    `button[id=submit]` was driven by the English word "submit" appearing in a
    sentence. So the token must be bounded at both ends AND carry the mark of a
    selector or a string literal: `#id`, `'id'`, `"id"`, `[data-action=id]`.
    """
    return re.compile(r"""(?:\#|["'\[=])""" + re.escape(token) + r"""(?![-\w])""")


def driven_by_corpus(gestures: list[Gesture], corpus: dict[str, str]) -> set[str]:
    """Ids of gestures some file in `corpus` appears to drive.

    NAMED IS NOT EXECUTED, and this is the known weakness of the measure — a
    mention in a docstring counts. It is still worth having: on its first run
    over IGA it found six mutating admin controls, five of them destructive,
    that no test or journey mentions at all. The stronger claim — that a real
    browser pressed it and the stored row changed — is P5's job, and this
    function is deliberately the weaker half so the two can be reported apart.

    Matching is PER FILE, not over one concatenated blob: the halves of an
    action must be in the same file and on the same line, or two unrelated
    tests jointly "drive" a control neither of them has heard of.
    """
    out: set[str] = set()
    pop = population(gestures)
    forms = [(g, _action_pattern(g.action)) for g in pop if g.kind == "form" and g.action]
    tokens = []
    for g in pop:
        if g.kind == "form" and g.action:
            continue
        # BOTH, not either: a registry entry is named by its handler (a bare
        # identifier in the code that calls it) OR by its declared name (a
        # quoted string in the client call). Requiring only the handler made 29
        # of ana-log's 55 writers read undriven when every one of them is named
        # by a quoted `"cancelTransfer"` — a guard that cannot pass is a guard
        # that gets overridden.
        for tok in g.names:
            tokens.append((g, _identifier_pattern(tok)))
        m = re.search(r"\[(?:data-action|id|name|data-testid)=([^\]{]+)", g.selector)
        if m:
            tok = m.group(1).lstrip(".")
            if tok:
                tokens.append((g, _token_pattern(tok)))
    for text in corpus.values():
        for g, pat in forms:
            if g.id not in out and pat.search(text):
                out.add(g.id)
        for g, pat in tokens:
            if g.id not in out and pat.search(text):
                out.add(g.id)
    return out


def hit_by_recording(gestures: list, hits: set) -> set:
    """Ids of gestures a RECORDED request actually reached.

    The stronger half of the measure. `driven_by_corpus` asks whether any file
    mentions the control; this asks whether the suite, when it ran, sent a
    request the control would have sent. A docstring cannot satisfy it.

    Only form-shaped gestures can be judged here — they declare a method and a
    path. A button wired in JS is answered by the browser recorder, and until
    that has run its verdict is UNKNOWN, which is not the same as "no" and must
    never be reported as one.
    """
    out: set = set()
    if not hits:
        return out
    by_method: dict = {}
    for h in hits:
        method, _, path = h.partition(" ")
        by_method.setdefault(method, []).append(path)
    for g in population(gestures):
        if g.kind != "form" or not g.action:
            continue
        method = (g.method or "GET").upper()
        pat = _action_pattern(g.action)
        for path in by_method.get(method, ()):
            if pat.fullmatch(path) or pat.search(path):
                out.add(g.id)
                break
    return out


def judgeable_by_recording(gestures: list) -> set:
    """Ids a recording COULD decide, so a caller can report the subset size.

    A verdict over a population where only a tenth is judgeable is a different
    claim from one over all of it, and the number has to be stated or the
    reader supplies an optimistic one.
    """
    return {g.id for g in population(gestures) if g.kind == "form" and g.action}


#: Files that TALK ABOUT gestures rather than driving them. A register's own
#: consumer names every undriven control in its failure message and docstring,
#: so leaving it in the corpus makes each one read as driven — by the very file
#: that reports it undriven. Caught on this module's first run against IGA, and
#: it is the same exclusion anat keeps for `template_paths.py`.
NOT_DRIVING = ("test_every_gesture_is_driven.py", "gestures.py")


def read_corpus(paths, glob: str = "**/*.py") -> dict[str, str]:
    """Every file that could drive a gesture, by path.

    Returns the files rather than a blob so a caller can report HOW MANY it
    read. A corpus that walked nothing reports success, so the size is part of
    the result and every caller here refuses a zero.
    """
    out: dict[str, str] = {}
    for base in paths:
        base = Path(base)
        if not base.exists():
            continue
        for p in sorted(base.rglob(glob)):
            if p.name in NOT_DRIVING:
                continue
            out[str(p)] = p.read_text(encoding="utf-8", errors="replace")
    return out


# --- the register, assembled once -------------------------------------------
#
# WHY THIS IS HERE AND NOT IN SIX REPOS. The lift -> merge static JS -> classify
# -> read corpus -> subtract assembly was retyped in every guard fixture and
# every regen script: twelve copies of the same twenty lines. They had already
# drifted — one repo grew two ceilings, floor constants and an integrity test
# while the other five kept none of them — so a fix to the shared idea had to be
# hand-applied in twelve places, which is how five of them stay wrong.

BOILERPLATE_REASONS = (
    "MUTATING and undriven — no test or journey posts to it",
    "handler not resolved from markup or JS; classify it or drive it",
)


@dataclass
class Measurement:
    """What one sweep of a repo found. Carries its own sizes so a caller can
    refuse a sweep that walked nothing rather than reporting a clean repo."""
    population: list
    corpus_files: int
    driven: set
    undriven: list
    mutating_undriven: list
    #: Ids a RECORDING says the app accepted a request for. Empty when no
    #: recording exists, which is UNKNOWN and must never be read as "none".
    hit: set = field(default_factory=set)
    #: Ids a recording could decide at all. A verdict has to say how much of
    #: the population it speaks for, or the reader supplies an optimistic
    #: number.
    judgeable: set = field(default_factory=set)
    #: False when no recording was supplied.
    recorded: bool = False

    @property
    def ceiling(self) -> int:
        return len(self.undriven)

    @property
    def mutating(self) -> int:
        return len(self.mutating_undriven)

    @property
    def unhit_mutating(self) -> list:
        """Mutating controls a recording COULD have decided and did not.

        The strongest claim this kit makes, and the narrowest: the control
        changes something, a request recording can judge it, and no request the
        suite made was ever accepted. `driven_by_corpus` counts a mention and
        says nothing about whether the thing has ever worked.

        Empty when nothing was recorded — an unknown, not a clean bill.
        """
        if not self.recorded:
            return []
        return [g for g in self.population
                if g.mutates == "yes" and g.id in self.judgeable and g.id not in self.hit]


def measure(root, templates="templates", static="static",
            corpus_dirs=("tests", "scripts"),
            min_controls: int = 20, min_corpus: int = 20,
            population_fn=None, recording=None) -> Measurement:
    """One sweep: every control, and which of them something names.

    `population_fn` is how a project whose controls are not in markup joins the
    same program instead of forking it. ana-log is a React SPA: every button
    routes through `api.action(category, name)` to one endpoint, so its
    population is the ACTION REGISTRY — which is better evidence than markup
    would be, since each entry declares `writes` itself. It supplies a provider
    and gets the identical register, the identical rules and the identical
    guard. Before this it had a second guard with a second matcher and a
    different register format, and the two had already drifted apart.

    The contract is the one this kit already uses for `bench.routes`: a
    `module:function` the project names, returning `Gesture` rows.

    `min_controls` / `min_corpus` are a DID-NOT-RUN detector, not a target. A
    scan that walked nothing agrees with everything, so the floors are measured
    per repo and passed in; the failure text says treat it as did not run.
    """
    root = Path(root)
    if population_fn is not None:
        gestures = list(population_fn(root))
    else:
        gestures, inline = lift_with_scripts(root / templates)
        js = dict(inline)      # a control's handler is looked up in ITS template first
        static_dir = root / static
        if static_dir.exists():
            for p in static_dir.rglob("*.js"):
                js[p.name] = p.read_text(encoding="utf-8", errors="replace")
        gestures = classify_with_js(gestures, js)
    corpus = read_corpus([root / d for d in corpus_dirs])
    if len(gestures) < min_controls or len(corpus) < min_corpus:
        raise RuntimeError(
            f"the sweep lifted {len(gestures)} controls from {templates}/ and read "
            f"{len(corpus)} corpus files, under the floors ({min_controls}/"
            f"{min_corpus}). Treat this as DID NOT RUN, not as a clean repo.")
    driven = driven_by_corpus(gestures, corpus)
    pop = population(gestures)
    undriven = sorted((g for g in pop if g.id not in driven), key=lambda g: g.id)
    return Measurement(population=pop, corpus_files=len(corpus), driven=driven,
                       undriven=undriven,
                       mutating_undriven=[g for g in undriven if g.mutates == "yes"],
                       hit=hit_by_recording(gestures, recording or set()),
                       judgeable=judgeable_by_recording(gestures),
                       recorded=bool(recording))


def register_rows(m: Measurement, previous_reasons: dict) -> list:
    """The register's rows, keeping any reason a human has already written."""
    rows = []
    for g in m.undriven:
        reason = previous_reasons.get(g.id) or (
            BOILERPLATE_REASONS[0] if g.mutates == "yes" else BOILERPLATE_REASONS[1])
        rows.append({"id": g.id, "mutates": g.mutates, "reason": reason})
    return rows


def unhit_rows(m: Measurement, previous_reasons: dict) -> list:
    """The second register: controls a recording says have never WORKED.

    Separate from the undriven rows on purpose. A control can be named by six
    tests and still have never once been accepted by the app — my8200 had
    sixteen of those, including marking an invoice paid, receiving goods
    against a purchase order and cancelling a customer order. Those are not
    "undriven"; they are a different and worse thing, and a list that mixed the
    two would let a repo work down the cheap half and call it progress.
    """
    rows = []
    for g in sorted(m.unhit_mutating, key=lambda g: g.id):
        rows.append({"id": g.id,
                     "reason": previous_reasons.get(g.id) or UNHIT_REASON})
    return rows


UNHIT_REASON = ("a recording of the suite shows no request to this control was "
                "ever ACCEPTED — only refusals, or nothing at all")


def refusals(m: Measurement, old: dict) -> list:
    """Why a regeneration must not be written. Empty means go ahead.

    TWO RULES, and the second is the one the review found missing.

      1. A ceiling may only fall. Obvious, and it was there.
      2. A MUTATING control may LEAVE the register and may not ENTER it by
         regeneration — whatever the totals do. Without this, driving one
         unclassified control pays for a new undriven DELETE: the count nets
         down, the refusal never fires, and the new row is enrolled carrying a
         sentence a generator wrote. Demonstrated in IGA and in anat: ceilings
         unchanged, guard green, `/purge` silently exempted with the reason
         "MUTATING and undriven — no test or journey posts to it", which is a
         restatement of the finding rather than a decision about it.

    A genuinely new mutating control that must be tolerated is added BY HAND,
    with a reason a person wrote. That is the point: the cost of exempting a
    destructive control should be a sentence somebody signs.
    """
    out = []
    if not old:
        return out
    listed = {r["id"] for r in old.get("undriven", [])}
    rows_now = {g.id for g in m.undriven}
    for name, now in (("ceiling", m.ceiling), ("mutating", m.mutating)):
        was = old.get(name)
        if was is not None and now > was:
            out.append(f"{name}: {now} undriven, above the recorded {was}. "
                       "Drive it or justify it by hand — regenerating is not how "
                       "a ratchet is raised.")
    for g in m.mutating_undriven:
        if g.id not in listed:
            out.append(
                f"new MUTATING control not in the register: {g.id}\n"
                f"    ({g.why})\n"
                "    A control that changes something and that nothing has ever "
                "pressed is the defect this register exists for. Drive it, or add "
                "the row BY HAND with a reason you are willing to sign.")
    for stale in sorted(listed - rows_now):
        out.append(f"now driven, remove it: {stale}")

    # The second ratchet, and only when a recording exists. Without one the
    # answer is UNKNOWN and refusing on an unknown teaches people to pass a
    # flag to get past it.
    if m.recorded:
        was = old.get("unhit_mutating")
        now = len(m.unhit_mutating)
        if was is not None and now > was:
            out.append(
                f"unhit_mutating: {now} mutating controls have never had a request "
                f"ACCEPTED, above the recorded {was}. Named is not pressed: a "
                "control can be mentioned by six tests and never once have worked.")
        listed_unhit = {r["id"] for r in old.get("unhit", [])}
        for g in m.unhit_mutating:
            if g.id not in listed_unhit and old.get("unhit_mutating") is not None:
                out.append(
                    f"new control that changes something and has never been "
                    f"accepted: {g.id}")
    return out


def integrity(m: Measurement, old: dict, slack: int = 5) -> list:
    """Complaints about the register as a DOCUMENT, independent of the sweep.

    `ceiling` must equal the rows beneath it. Nothing checked that, so a ceiling
    edited by hand from 16 to 20 bought five undriven controls with no row and
    no reason — verified in IGA, tharros, my8200 and eliad, where the slack
    tolerance was the only thing standing in the way and it allows exactly five.
    """
    out = []
    rows = old.get("undriven", [])
    if old.get("ceiling") != len(rows):
        out.append(f"ceiling says {old.get('ceiling')} but {len(rows)} rows are listed — "
                   "a number nobody measured")
    listed_mutating = sum(1 for r in rows if r.get("mutates") == "yes")
    if old.get("mutating") != listed_mutating:
        out.append(f"mutating says {old.get('mutating')} but {listed_mutating} rows "
                   "are marked mutates: yes")
    for r in rows:
        if not str(r.get("reason", "")).strip():
            out.append(f"{r['id']} is listed with no reason")
    for name, live in (("ceiling", m.ceiling), ("mutating", m.mutating)):
        if old.get(name) is not None and old[name] - live > slack:
            out.append(f"{name} is {old[name]} but only {live} are undriven — "
                       f"lower it; a ceiling that far above the count is decoration")
    return out


# --- the pin ----------------------------------------------------------------

#: How this kit is named wherever a project installs it.
_PIN = re.compile(r"qa-bench@([0-9A-Za-z._-]+)")


def pin_refs(root, ignore=()) -> dict:
    """{ref: [tracked files naming it]}. Every ref, so a caller can prove it read some.

    Only TRACKED files are read — a `.venv` full of vendored copies is not the
    repo's claim about anything. `ignore` takes paths whose refs are examples
    rather than installs; each needs its reason where it is declared.
    """
    import subprocess
    root = Path(root)
    files = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                           text=True).stdout.split("\n")
    found: dict = {}
    for rel in files:
        if not rel or rel in ignore:
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except (OSError, IsADirectoryError):
            continue
        for ref in _PIN.findall(text):
            found.setdefault(ref, []).append(rel)
    return found


def pin_disagreements(root, ignore=()) -> dict:
    """Only the refs, when a repo names more than one. `{}` when it agrees.

    THREE TIMES IN ONE DAY, which is a design decision rather than a
    coincidence. A review found one repo pinning qa-bench at three different
    refs across its workflows and Makefile, and another installing it with no
    ref at all on a runner holding staging secrets — beneath a comment
    explaining why a floating pin is forbidden. Then a sweep that repinned the
    workflows and the Makefile missed `requirements-dev.txt`, which is the file
    CI actually installs from, so a job ran the OLD kit against the NEW guard
    and died on an import.

    The failure is quiet in the direction that matters: the pin that is wrong is
    the one nobody looked at, and the symptom arrives as an ImportError in an
    unrelated test rather than as "your pins disagree".
    """
    found = pin_refs(root, ignore)
    return found if len(found) > 1 else {}
