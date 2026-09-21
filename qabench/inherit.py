"""inherit — a guard built from an instance inherits the instance's parameters.

    python -m qabench inherited FILE --property "<the property, in words>" [--declared LIT=why ...] [--json]

WHY. Four guards on 2026-09-21, three codebases, each CORRECT and each a guard
for the case rather than the class, because a constant of the case that
prompted it sat inside its selector:

  * anat's route sweep keyed on `batch|bulk` in the path, the names of the routes
    that prompted it; `/api/collections/ai/risk-classify` overwrote fifty risk
    scores with NULL and answered {"updated": 50} outside it.
  * anat's count-drift guard keyed on the denominator `146` of its finding;
    eleven other transcribed counts in the same table carry other denominators.
  * ana's ACT-02 guard keyed on the prop `onDone`; six dialogs publish through
    onPicked, onPlaced, onSplit, onApplied and onCreated.
  * anat's dialog ratchet keyed on `.modal-overlay` and a character window.

The parameter is never STATED as a parameter. Nobody writes "this guard covers
denominator 146"; they write a regex, and the 146 is inside it, so the scope is
a fact about the implementation that nobody claimed and nobody can dispute.

THE TELL, tested against those four before it was written down: a literal in
the selector that is not in the property. Every string and number constant the
guard file carries is split into words and compared with the property stated
in words; each word that the property does not contain is listed, and must be
either added to the property (it IS the scope, so say so) or declared with the
reason it names the property ("modal-overlay: the element every dialog here
renders as"). It found the inherited literal in all four: batch and bulk, 146,
onDone, modal/overlay.

WHAT IT CANNOT SEE, stated, because two of the four also inherited a METHOD:
the character window (anat) and the whole-file containment (ana) are not
literals. Their discriminator is a mutation, per subject: break ONE subject and
confirm that only its parameter goes red. If breaking subject A reddens nothing,
or reddens B too, the assertion is not reading A (ana's BulkEditDialog passed on
its neighbour's publish). `qabench mutate` is the tool for that half.

It is a PROMPT, not a verdict: a legitimate implementation literal is listed
too, and the answer to it is one line of declaration. That line is the point —
it is the sentence "this guard only covers X" that nobody wrote.

Exit: 0 every selector word is in the property or declared · 1 some are not · 3
the file could not be read or no property was given.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

#: Words that are code, not scope. Deliberately short: a word missing from here
#: costs one declaration line, a word wrongly here hides an inherited parameter.
CODE = frozenset("""
the and for not with from into this that are was were has have had any all each per its
def return import true false none null self cls args kwargs str int dict list set tuple len
print path open read text utf json yaml get post put patch delete http https www com api
test tests assert pytest fixture param mark skip xfail root file files line lines name names
python node npm src app lib bin tmp cmd run main index html htm css js jsx ts tsx py md yml
""".split())
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]*|\d{2,}")


def _stem(w: str) -> str:
    w = w.lower()
    for suf in ("ing", "es", "ed", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def _split_camel(w: str) -> list[str]:
    return re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", w) or [w]


def _selector_like(text: str) -> bool:
    """A selector is short and code-shaped; a failure message is prose. The first
    estate run over EVERY constant listed 31–194 words per real guard file, almost
    all of them from assertion messages, and a prompt that long is not read."""
    if REGEXY.search(text):
        return len(text) <= 160
    return len(text.split()) <= 2 and len(text) <= 60


REGEXY = re.compile(r"\\[dwsbB]|[|^$]|\[[^\]]*\]|\(\?|\.\*|\.\+")


def literals(source: str, *, python: bool) -> list[str]:
    """The string and number constants that can SELECT: docstrings, assertion
    messages, f-strings and prose-length strings excluded."""
    out: list[str] = []
    if python:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            python = False
        else:
            docs = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Assert) and node.msg is not None:
                    docs |= {id(n) for n in ast.walk(node.msg)}
                if isinstance(node, ast.JoinedStr):
                    docs |= {id(n) for n in ast.walk(node)}
                if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    body = getattr(node, "body", [])
                    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
                        docs.add(id(body[0].value))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and id(node) not in docs:
                    if isinstance(node.value, str) and _selector_like(node.value):
                        out.append(node.value)
                    elif isinstance(node.value, int) and not isinstance(node.value, bool) and abs(node.value) >= 10:
                        out.append(str(node.value))
            return out
    for m in re.finditer(r"""(["'`])((?:\\.|(?!\1).){1,200})\1|/((?:\\.|[^/\n]){2,120})/[gimsuy]*""", source):
        lit = m.group(2) or m.group(3) or ""
        if _selector_like(lit):
            out.append(lit)
    out += re.findall(r"(?<![\w.])\d{2,}(?![\w.])", source)
    return out


def words(lits: list[str]) -> dict[str, str]:
    """{stem: an example literal it came from}, code vocabulary removed."""
    out: dict[str, str] = {}
    for lit in lits:
        for tok in WORD.findall(lit):
            for part in _split_camel(tok) if not tok.isdigit() else [tok]:
                s = _stem(part)
                if len(s) < 3 and not s.isdigit():
                    continue
                if s in CODE or part.lower() in CODE:
                    continue
                out.setdefault(s, lit[:60])
    return out


def unexplained(source: str, prop: str, declared: dict[str, str], *, python: bool) -> list[tuple[str, str]]:
    """[(word, the literal it came from)] for every selector word the property does not contain."""
    have = {_stem(p) for tok in WORD.findall(prop) for p in (_split_camel(tok) if not tok.isdigit() else [tok])}
    have |= {_stem(w) for w in declared}
    return sorted((w, lit) for w, lit in words(literals(source, python=python)).items() if w not in have)


# --- THE METHOD HALF --------------------------------------------------------
# Two inherited METHODS carry no wrong literal at all, so the scan above cannot
# see them. Both were measured on the real before-states before this was written:
#
#   WINDOW. anat's dialog ratchet (origin/staging blob 4eba1e09) took the extent
#   of dialog i as the span to the START of dialog i+1, `ms[i + 1].start()`, and
#   asked whether `data-dialog-close` was `in` that span. Every literal in the
#   file is right; the span is not the element. voice-test-modal's next overlay
#   is ~13,000 lines below, so its window found a neighbour's attribute: 17
#   reported against 18 by true nesting — a signal of 1 in 146.
#
#   PARAMETER-INVARIANT ASSERTION. ana's ACT-02 (7a6a1b7b^) is parametrised by
#   dialog `name`, and its second assertion, `"publish" in hosts`, never mentions
#   `name`: the right word over the right corpus at the wrong extent, reused from
#   the line above where that extent was correct. It passes for every dialog
#   because ONE dialog in the file publishes.

def _names(node) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _next_match_bound(expr, assigned: dict) -> bool:
    """True when a slice bound is, or was assigned from, the NEXT match's start."""
    seen = [expr]
    if isinstance(expr, ast.Name) and expr.id in assigned:
        seen.append(assigned[expr.id])
    for e in seen:
        for n in ast.walk(e):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("start", "end")
                    and isinstance(n.func.value, ast.Subscript)
                    and isinstance(n.func.value.slice, ast.BinOp) and isinstance(n.func.value.slice.op, ast.Add)):
                return True
    return False


def methods(source: str) -> list[tuple[int, str, str]]:
    """[(line, kind, code)] for the two inherited methods, in a Python guard file."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    out = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        assigned = {t.id: a.value for a in ast.walk(fn) if isinstance(a, ast.Assign)
                    for t in a.targets if isinstance(t, ast.Name)}
        for cmp in [n for n in ast.walk(fn) if isinstance(n, ast.Compare)]:
            if any(isinstance(op, (ast.In, ast.NotIn)) for op in cmp.ops):
                for right in cmp.comparators:
                    if (isinstance(right, ast.Subscript) and isinstance(right.slice, ast.Slice)
                            and right.slice.upper is not None and _next_match_bound(right.slice.upper, assigned)):
                        out.append((cmp.lineno, "window",
                                    "containment over a span that ends at the NEXT match's start — the span is not "
                                    "the element; walk the element's own extent"))
        params = set()
        for d in fn.decorator_list:
            if (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "parametrize"
                    and d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value, str)):
                params |= {x.strip() for x in d.args[0].value.split(",") if x.strip()}
        if not params:
            continue
        # Every argument carries the parameter's effect, not only the parametrised
        # names: a fixture like `page` was navigated WITH the parameter, so an
        # assertion on it is per-subject even though it never names it. Measured:
        # without this the estate run flagged 973 assertions, nearly all browser
        # tests asserting on `page`.
        tainted = set(params) | {a.arg for a in fn.args.args + fn.args.kwonlyargs}
        for _ in range(3):                          # propagate through locals derived from the parameter
            for a in [n for n in ast.walk(fn) if isinstance(n, ast.Assign)]:
                if _names(a.value) & tainted:
                    tainted |= {t.id for t in a.targets if isinstance(t, ast.Name)}
            # `with pytest.raises(...) as e:` whose body used the parameter: `e` carries it.
            for w in [n for n in ast.walk(fn) if isinstance(n, (ast.With, ast.AsyncWith))]:
                if any(_names(b) & tainted for b in w.body):
                    tainted |= {i.optional_vars.id for i in w.items if isinstance(i.optional_vars, ast.Name)}
        asserts = [n for n in ast.walk(fn) if isinstance(n, ast.Assert)]
        per_subject = [a for a in asserts if _names(a.test) & tainted]
        for a in asserts:
            # A CONTAINMENT over a corpus the parameter never touched, BESIDE an
            # assertion that does read the parameter: ana's second assert, reusing
            # the extent the first one needed. A function whose assertions are all
            # invariant is a different shape (a fixed-case test), not this one.
            containment = isinstance(a.test, ast.Compare) and any(isinstance(op, (ast.In, ast.NotIn)) for op in a.test.ops)
            if containment and per_subject and not (_names(a.test) & tainted):
                out.append((a.lineno, "invariant",
                            f"parametrised by {', '.join(sorted(params))}, and this assertion never mentions it — it "
                            "is the same check for every parameter, so one member can satisfy it for all"))
    return sorted(out)


def run(argv: list[str], *, echo=print) -> int:
    if not argv or argv[0].startswith("-") or "--property" not in argv:
        print('usage: python -m qabench inherited FILE --property "<the property, in words>" [--declared LIT=why ...]',
              file=sys.stderr)
        return 3
    path = Path(argv[0])
    prop = argv[argv.index("--property") + 1] if argv.index("--property") + 1 < len(argv) else ""
    if not prop.strip():
        print("inherited: an empty property is the defect this exists for — state it in words (exit 3)", file=sys.stderr)
        return 3
    declared = {}
    for i, a in enumerate(argv):
        if a == "--declared" and i + 1 < len(argv) and "=" in argv[i + 1]:
            k, v = argv[i + 1].split("=", 1)
            declared[k] = v
    try:
        src = path.read_text(encoding="utf-8")
    except OSError as ex:
        print(f"inherited: cannot read {path}: {ex} (exit 3)", file=sys.stderr)
        return 3
    found = unexplained(src, prop, declared, python=path.suffix == ".py")
    how = methods(src) if path.suffix == ".py" else []
    if "--json" in argv:
        echo(json.dumps({"words": [{"word": w, "from": lit} for w, lit in found],
                         "methods": [{"line": n, "kind": k, "why": t} for n, k, t in how]}, ensure_ascii=False, indent=1))
    else:
        echo(f"inherited: {len(found)} selector word(s) in {path.name} that the property does not contain · "
             f"{len(how)} inherited method(s)")
        for n, k, t in how:
            echo(f"  line {n} {k}: {t}")
        for w, lit in found:
            echo(f"  {w:18} from {lit!r}  — the scope, so add it to the property, or declare why it names it")
    return 1 if found or how else 0
