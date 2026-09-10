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
    why: str = ""             # why it is classified that way

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
    """Collects controls, tracking whether we are inside a mutating form.

    `convert_charrefs` is left on: entity text does not affect which controls
    exist, and turning it off changes nothing here except noise.
    """

    def __init__(self, template: str):
        super().__init__()
        self.template = template
        self.found: list[Gesture] = []
        self._form_depth = 0          # >0 while inside any form
        self._mutating_form = 0       # >0 while inside a MUTATING form
        self._counter: dict[str, int] = {}

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

    def handle_starttag(self, tag, attrs):
        if tag == "form":
            self._form_depth += 1
            method = (_attr(attrs, "method") or "GET").upper()
            action = _attr(attrs, "action") or ""
            if method in MUTATING_METHODS:
                self._mutating_form += 1
                sel, _ = _stable_selector(tag, attrs)
                # A form's identity is its action and method — that is what it
                # does, and it survives every cosmetic edit.
                selector = sel or f"form[{method} {action or '(self)'}]"
                self.found.append(Gesture(
                    template=self.template, kind="form", selector=selector,
                    method=method, action=action, mutates="yes",
                    why=f"<form method={method}> submits to {action or 'its own URL'}"))
            return

        if tag == "button":
            btype = (_attr(attrs, "type") or "submit").lower()
            if self._mutating_form and btype == "submit":
                return  # the form above already IS this gesture
            if btype == "submit" and self._form_depth:
                return  # submits a non-mutating (GET) form; the form is the thing
            self.found.append(self._candidate(tag, attrs))
            return

        if _attr(attrs, "data-action") is not None or _attr(attrs, "onclick") is not None:
            if tag in ("button", "form"):
                return  # already handled
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
        return Gesture(template=self.template, kind="button" if tag == "button" else "action",
                       selector=self._key(tag, attrs), mutates=mutates, why=why)

    def handle_endtag(self, tag):
        if tag == "form":
            if self._mutating_form:
                self._mutating_form -= 1
            if self._form_depth:
                self._form_depth -= 1


def lift_template(path: Path, root: Path) -> list[Gesture]:
    """Every control in one template."""
    rel = str(path.relative_to(root))
    lifter = _Lifter(rel)
    lifter.feed(neutralise_jinja(path.read_text(encoding="utf-8", errors="replace")))
    lifter.close()
    return lifter.found


def lift(template_root: Path, glob: str = "**/*.html") -> list[Gesture]:
    """Every control in every template, sorted so the register is stable."""
    root = Path(template_root)
    out: list[Gesture] = []
    for p in sorted(root.glob(glob)):
        out.extend(lift_template(p, root))
    return sorted(out, key=lambda g: g.id)


# --- the JS half -----------------------------------------------------------
# A button wired in JS is the majority case and the one a URL lifter misses.
# We resolve it the only way markup allows: find the handler that selects this
# control and ask whether that handler reaches a mutating call.

_MUTATING_CALL = re.compile(
    r"""(fetch|apiFetch|axios)\s*\([^)]*|method\s*:\s*['"](POST|PUT|PATCH|DELETE)['"]""",
    re.I)


def classify_with_js(gestures: list[Gesture], js_sources: dict[str, str]) -> list[Gesture]:
    """Upgrade `unknown` candidates by reading the scripts that wire them.

    Deliberately conservative in ONE direction: it may leave a mutating control
    `unknown`, and it must never call a mutating control `no`. An overclaim here
    removes a real gesture from the population silently, which is the failure
    this module exists to prevent; an underclaim only leaves a row needing a
    reason.
    """
    blob = "\n".join(js_sources.values())
    for g in gestures:
        if g.mutates != "unknown":
            continue
        token = re.search(r"\[(?:data-action|id|name|data-testid)=([^\]]+)\]", g.selector)
        if not token:
            continue
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
    """
    return [g for g in gestures if g.mutates in ("yes", "unknown")]


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


def driven_by_corpus(gestures: list[Gesture], corpus: dict[str, str]) -> set[str]:
    """Ids of gestures some file in `corpus` appears to drive.

    NAMED IS NOT EXECUTED, and this is the known weakness of the measure — a
    mention in a docstring counts. It is still worth having: on its first run
    over IGA it found six mutating admin controls, five of them destructive,
    that no test or journey mentions at all. The stronger claim — that a real
    browser pressed it and the stored row changed — is P5's job, and this
    function is deliberately the weaker half so the two can be reported apart.

    Every static segment of a form's action must appear, not merely one, or
    `/lead` matches `/lead-intake` and a whole surface reads as covered.
    """
    blob = "\n".join(corpus.values())
    out: set[str] = set()
    for g in population(gestures):
        if g.kind == "form" and g.action:
            segs = _static_segments(g.action)
            if segs and all(s in blob for s in segs):
                out.add(g.id)
            continue
        token = re.search(r"\[(?:data-action|id|name|data-testid)=([^\]]+)\]", g.selector)
        if token and token.group(1) in blob:
            out.add(g.id)
    return out


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
