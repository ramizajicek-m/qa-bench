"""delta — a tier that is habitually red reports nothing when it becomes differently red.

    python -m qabench delta --before LAST.xml --after THIS.xml [--json]
    python -m qabench delta --store DIR --name TIER --after THIS.xml [--json]

WHY. ana-log's nightly browser tier ran six shards; all six had been failing for
days. On 2026-09-21 shard 0 carried 38 failures, and THIRTY-THREE of them were
one cause introduced two days earlier. They changed nothing anyone could see: the
run was already `failure`, the shard was already `failure`, and the count sat in
a log body nobody opens. Every instrument worked and reported honestly, and the
output carried no information, because A CONSTANT IS NOT A SIGNAL. The signal is
the DELTA in the verdict, and nobody was computing one.

WHAT IT PRINTS: N failing, K NEW since the baseline (named), R fixed, and V
VANISHED — failing before and absent now. A failure that disappears usually
means a test stopped running, not that it started passing, so a vanished
failure is red exactly like a new one. Tests that appear or disappear while
passing are listed, not judged.

WHY IT NEEDS A PEER. The companion lesson from the same week (ana-log): a set
whose members depend on what ran first carries no information in either
direction, and a delta over such a set moves for reasons unrelated to any
change. The discriminating procedure is two runs with one unrelated change
between them, comparing failure SETS; `delta` is the tool that compares the
sets, and an order-dependent tier shows up as churn in both directions.

`--store DIR --name TIER` keeps the last report per tier and compares against
it, then replaces it — the baseline is "the last run of this tier", which is
what a nightly needs without any CI artefact plumbing. The first run has no
baseline and exits 3: there is nothing to subtract, and pretending otherwise is
how a red tier reads as news-free.

IDENTITY is suite name + classname + name, so a Playwright report that runs the
same file under several projects stays distinct. A duplicate identity is
refused: two cases with one name make "new" undecidable.

Exit: 0 no new and no vanished failures · 1 some · 3 no baseline, or a report
that could not be read.
"""
from __future__ import annotations

import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

FAILING = ("failure", "error")


class Unreadable(ValueError):
    pass


def read(path: Path) -> dict[str, str]:
    """{identity: "passed" | "failed" | "skipped"} from a JUnit report."""
    try:
        raw = path.read_bytes().decode("utf-8-sig")
        if "<!DOCTYPE" in raw.upper() or "<!ENTITY" in raw.upper():
            raise Unreadable(f"{path}: JUnit DTDs/entities are not accepted")
        root = ET.fromstring(raw)
    except (OSError, UnicodeError, ET.ParseError) as ex:
        raise Unreadable(f"{path}: unreadable or malformed ({ex})") from ex
    if root.tag not in ("testsuite", "testsuites"):
        raise Unreadable(f"{path}: root is <{root.tag}>, not a JUnit report")
    out: dict[str, str] = {}
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite")) or [root]
    for suite in suites:
        for case in suite.findall("testcase"):
            ident = f"{suite.get('name', '')}::{case.get('classname', '')}::{case.get('name', '')}"
            if ident in out:
                raise Unreadable(f"{path}: duplicate testcase identity {ident!r} — 'new' is undecidable")
            tags = {child.tag for child in case}
            out[ident] = "failed" if tags & set(FAILING) else "skipped" if "skipped" in tags else "passed"
    if not out:
        raise Unreadable(f"{path}: no testcases — a report that decided nothing is not a baseline")
    return out


def compare(before: dict[str, str], after: dict[str, str]) -> dict:
    fb = {k for k, v in before.items() if v == "failed"}
    fa = {k for k, v in after.items() if v == "failed"}
    return {"failing": len(fa),
            "new": sorted(fa - fb),
            "fixed": sorted(k for k in fb - fa if k in after),
            "vanished": sorted(k for k in fb if k not in after),
            "appeared": sorted(k for k in after if k not in before and k not in fa),
            "dropped": sorted(k for k in before if k not in after and k not in fb)}


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default


def run(argv: list[str], *, echo=print) -> int:
    after_p = _arg(argv, "--after")
    store, name = _arg(argv, "--store"), _arg(argv, "--name")
    before_p = _arg(argv, "--before")
    if not after_p or not (before_p or (store and name)):
        print("usage: python -m qabench delta --before LAST.xml --after THIS.xml\n"
              "       python -m qabench delta --store DIR --name TIER --after THIS.xml", file=sys.stderr)
        return 3
    baseline = Path(before_p) if before_p else Path(store) / f"{name}.xml"
    try:
        after = read(Path(after_p))
    except Unreadable as ex:
        print(f"delta: {ex} (exit 3)", file=sys.stderr)
        return 3
    if store and name:
        # The new report becomes the next baseline whatever this one says: the
        # question is always "what changed since the LAST run of this tier".
        keep = Path(store) / f"{name}.xml"
        keep.parent.mkdir(parents=True, exist_ok=True)
        prior = keep.read_bytes() if keep.exists() else None
        shutil.copyfile(after_p, keep)
        if prior is None and not before_p:
            echo(f"delta {name}: no baseline yet — stored this run as the baseline; nothing to subtract (exit 3)")
            return 3
        if not before_p:
            tmp = keep.with_suffix(".prev.xml")
            tmp.write_bytes(prior)
            baseline = tmp
    try:
        before = read(baseline)
    except Unreadable as ex:
        print(f"delta: baseline {ex} (exit 3)", file=sys.stderr)
        return 3
    d = compare(before, after)
    if "--json" in argv:
        echo(json.dumps(d, indent=1, ensure_ascii=False))
    else:
        label = name or Path(after_p).name
        echo(f"delta {label}: {d['failing']} failing, {len(d['new'])} NEW, {len(d['vanished'])} VANISHED, "
             f"{len(d['fixed'])} fixed (baseline {baseline})")
        for k in d["new"]:
            echo(f"  NEW       {k}")
        for k in d["vanished"]:
            echo(f"  VANISHED  {k}  — failing before, absent now: usually stopped running, not fixed")
        for k in d["fixed"]:
            echo(f"  fixed     {k}")
        if d["appeared"] or d["dropped"]:
            echo(f"  ({len(d['appeared'])} passing test(s) appeared, {len(d['dropped'])} passing test(s) no longer ran)")
    return 1 if d["new"] or d["vanished"] else 0
