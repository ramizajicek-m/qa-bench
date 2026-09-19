"""census — every key one layer DECLARES reaches every layer that must CONSUME it.

    python -m qabench census                 # the `census:` block of qa/manifest.yml
    python -m qabench census --json          # the rows, for a test to read
    python -m qabench census --repo DIR      # another checkout (a parent commit, say)

WHY. The largest class of defect people found in ana-log (32 of 121, blind-coded
2026-09-19) was two correct halves that never met: their descriptor declared
`headerBadge: qr`, `hasSelectionModal`, `displayType: link`, `onValueChange`,
and our screens never read them. ana-log already had a key census from
2026-09-09. Measured at the parent of each fix, it failed three ways, and this
module exists to not fail them again:

  1. "MENTIONED ANYWHERE" COUNTED AS READ. `onValueChange` appeared in app/ (the
     server loaded and served it) and so read as consumed, while the browser
     ran none of it. Here a declared key must reach EVERY consumer layer the
     manifest names — the server carrying it is not the client reading it.
  2. THE REGISTER WAS AN UNVERIFIED ESCAPE HATCH. `headerBadge`,
     `hasSelectionModal` and `onValueChange` were each flagged, and each was
     excused by a session with a confident, wrong sentence ("a count badge",
     "ActionDialog already collects it", "IS read"). Here an exemption names the
     layer the key stops at, a reason, an EVIDENCE path that must exist, and a
     `review_by` date; an entry without them, or past its date, is a finding.
     An exemption whose key has since reached every layer is stale and red too.
  3. VALUES WERE NOT KEYS. `displayType: link` and `type: select2` are values of
     keys everybody reads. Keys listed under `values:` are censused per VALUE:
     each declared value must appear as a string literal in each layer.

WHAT IT CANNOT SEE, stated: a token in a layer is evidence the layer names the
key, not that the right screen uses it (a key read on one screen passes for
all). And keys that are ours rather than a descriptor's — an API response field
the client never renders — need the browser, not the source; that is the
dynamic half, not this module.

Exit: 0 every declared key/value reaches every layer or is exempted with
evidence · 1 a gap, or a bad/stale exemption · 3 nothing declared, or a layer
matched no files (a census of nothing is not a pass).

Manifest shape:

    census:
      declared: ["spec-source/**/*.json"]        # what THEY (or our own schema) declare
      values: [displayType, type, style]         # keys censused per value, not per key
      ignore_keys: []                            # structural keys with no behaviour (e.g. "id")
      layers:
        - {name: server, glob: ["app/**/*.py"]}
        - {name: client, glob: ["web/src/**/*.ts", "web/src/**/*.tsx"]}
      register: qa/census.yml
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_TOKEN = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_STRING = re.compile(r"""(["'`])((?:\\.|(?!\1).){1,80})\1""")
#: A declared VALUE is consumed only where code BRANCHES on it — compares with it,
#: cases on it, or keys a lookup table by it. A bare literal anywhere is not
#: evidence: "link" and "file" occur in any client for other reasons, and the
#: first version of this census let displayType=link through on exactly that.
_BRANCH = re.compile(r"""(?:===?|!==?|\bcase|\bin)\s*(["'`])((?:(?!\1).){1,60})\1"""
                     r"""|(["'`])((?:(?!\3).){1,60})\3\s*(?:===?|!==?)"""
                     r"""|^\s*(?:(["'])((?:(?!\5).){1,60})\5|([A-Za-z_$][\w$]*))\s*:""", re.M)


@dataclass
class Layer:
    name: str
    files: list[Path]
    tokens: set[str] = field(default_factory=set)
    strings: set[str] = field(default_factory=set)


def _glob(root: Path, patterns) -> list[Path]:
    out: set[Path] = set()
    for pat in patterns if isinstance(patterns, list) else [patterns]:
        out.update(p for p in root.glob(pat) if p.is_file())
    return sorted(out)


def read_layer(root: Path, name: str, patterns) -> Layer:
    layer = Layer(name, _glob(root, patterns))
    for f in layer.files:
        text = f.read_text(encoding="utf-8", errors="replace")
        layer.tokens.update(_TOKEN.findall(text))
        for m in _BRANCH.finditer(text):
            layer.strings.add(m.group(2) or m.group(4) or m.group(6) or m.group(7))
    return layer


def declared(files: list[Path], values: set[str], ignore: set[str]) -> tuple[dict[str, int], dict[str, int]]:
    """({key: occurrences}, {"key=value": occurrences}) over every JSON file."""
    keys: dict[str, int] = {}
    vals: dict[str, int] = {}

    def walk(node) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if not isinstance(k, str) or k in ignore or not _TOKEN.fullmatch(k):
                    walk(v)
                    continue
                keys[k] = keys.get(k, 0) + 1
                if k in values and isinstance(v, str) and v:
                    vals[f"{k}={v}"] = vals.get(f"{k}={v}", 0) + 1
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for f in files:
        try:
            walk(json.loads(f.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            continue
    return keys, vals


def reaches(item: str, layer: Layer) -> bool:
    if "=" in item:
        return item.split("=", 1)[1] in layer.strings
    return item in layer.tokens


@dataclass
class Row:
    item: str
    occurrences: int
    missing: list[str]                 # layers it does not reach
    exemption: dict | None = None
    problem: str = ""                  # why the row is red; "" when it is not


REQUIRED = ("stops_at", "reason", "evidence", "review_by")


def judge(item: str, n: int, missing: list[str], ex: dict | None, root: Path, today: dt.date,
          layer_names: list[str]) -> Row:
    row = Row(item, n, missing, ex)
    if not missing:
        if ex:
            row.problem = "stale exemption: it now reaches every layer — delete the entry"
        return row
    if not ex:
        row.problem = f"declared, and never reaches {', '.join(missing)}"
        return row
    lacking = [k for k in REQUIRED if not ex.get(k)]
    if lacking:
        row.problem = f"exemption lacks {', '.join(lacking)}"
        return row
    if ex["stops_at"] not in layer_names:
        row.problem = f"exemption stops_at {ex['stops_at']!r}, not a layer ({', '.join(layer_names)})"
        return row
    stops = layer_names.index(ex["stops_at"])
    beyond = layer_names[stops + 1:]
    if any(m not in beyond for m in missing):
        row.problem = f"exemption says it stops at {ex['stops_at']} but it never reaches {', '.join(missing)} either"
        return row
    evidence = ex["evidence"] if isinstance(ex["evidence"], list) else [ex["evidence"]]
    absent = [e for e in evidence if not (root / str(e).split("::")[0]).exists()]
    if absent:
        row.problem = f"exemption evidence does not exist: {', '.join(absent)}"
        return row
    try:
        due = dt.date.fromisoformat(str(ex["review_by"]))
    except ValueError:
        row.problem = f"exemption review_by {ex['review_by']!r} is not a date"
        return row
    if due < today:
        row.problem = f"exemption expired {due} — re-verify the reason against the code, or close the gap"
    return row


def run_census(root: Path, cfg: dict, *, today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    values = set(cfg.get("values") or [])
    ignore = set(cfg.get("ignore_keys") or [])
    decl_files = _glob(root, cfg.get("declared") or [])
    layers = [read_layer(root, l["name"], l["glob"]) for l in cfg.get("layers") or []]
    names = [l.name for l in layers]
    reg_path = root / cfg["register"] if cfg.get("register") else None
    register = (yaml.safe_load(reg_path.read_text(encoding="utf-8")) or {}) if reg_path and reg_path.exists() else {}
    exemptions = register.get("exemptions") or {}
    keys, vals = declared(decl_files, values, ignore)
    rows = []
    for item, n in sorted({**keys, **vals}.items()):
        if item in values:             # a per-value key is judged by its values, not by its name
            continue
        missing = [l.name for l in layers if not reaches(item, l)]
        rows.append(judge(item, n, missing, exemptions.get(item), root, today, names))
    orphans = sorted(set(exemptions) - {r.item for r in rows})
    return {
        "declared_files": len(decl_files),
        "layers": {l.name: len(l.files) for l in layers},
        "items": len(rows),
        "keys": len([r for r in rows if "=" not in r.item]),
        "values": len([r for r in rows if "=" in r.item]),
        "reaching_all": len([r for r in rows if not r.missing]),
        "exempted": len([r for r in rows if r.missing and r.exemption and not r.problem]),
        "red": [r.__dict__ for r in rows if r.problem],
        "orphan_exemptions": orphans,
    }


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def run(argv: list[str], *, today: dt.date | None = None) -> int:
    root = Path(_arg(argv, "--repo", ".")).resolve()
    mpath = root / "qa" / "manifest.yml"
    doc = yaml.safe_load(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    cfg = (doc or {}).get("census")
    if not cfg:
        print(f"no `census:` block in {mpath} — nothing measured (exit 3)", file=sys.stderr)
        return 3
    out = run_census(root, cfg, today=today)
    empty_layers = [n for n, c in out["layers"].items() if c == 0]
    if "--json" in argv:
        print(json.dumps(out, indent=1, ensure_ascii=False))
    else:
        print(f"CENSUS — {out['declared_files']} declared files, {out['keys']} keys + {out['values']} values; layers "
              + ", ".join(f"{n} ({c} files)" for n, c in out["layers"].items()))
        print(f"  reach every layer: {out['reaching_all']}   exempted with evidence: {out['exempted']}   "
              f"RED: {len(out['red'])}")
        for r in out["red"]:
            print(f"  RED  {r['item']:40} ×{r['occurrences']:<4} {r['problem']}")
        for o in out["orphan_exemptions"]:
            print(f"  RED  {o:40} exemption for an item nothing declares — delete it")
    if not out["declared_files"] or not out["items"] or empty_layers or not out["layers"]:
        print("the census compared nothing"
              + (f" (layer(s) matched no file: {', '.join(empty_layers)})" if empty_layers else "")
              + " — treat as did not run (exit 3)", file=sys.stderr)
        return 3
    return 1 if (out["red"] or out["orphan_exemptions"]) else 0
