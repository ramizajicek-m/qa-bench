"""The orchestrator: run every stage, in order, with proof each one RAN.

Two lessons built in (anat, 2026-08-21/22), each of which cost a morning:
  * a pipeline that discards a stage's exit code reads green when the stage was
    SIGTERM'd at 2% — every stage's own code is captured here;
  * an exit code is not proof of completion — every stage writes
    `<shots>/<name>.json`; a stage that exits 0 and leaves no ledger is NOT RUN
    and the night fails. A stage that decided nothing is red too.

`swept_sha` (from smoke) is written into nightly.json and handed to the
heartbeat provider, so a promote step can refuse a SHA the sweep never saw.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from . import __version__
from .manifest import Bench

SHARED = ["smoke", "pages_by_role", "endpoints_by_role"]


#: Where THIS kit lives, so a stage subprocess imports the same qabench that
#: planned it — a checkout run from its own tree (the kit's tests) has no
#: installed copy, and `-m qabench` under the project's cwd found nothing.
_KIT_HOME = str(Path(__file__).resolve().parents[1])


def _pythonpath(*first: str) -> str:
    return os.pathsep.join([*first, _KIT_HOME, *filter(None, [os.environ.get("PYTHONPATH")])])


def _run_shared(name: str, cfg: Bench, timeout: int) -> tuple[int, float]:
    started = time.time()
    proc = subprocess.run([sys.executable, "-m", "qabench", "stage", name], cwd=cfg.repo, timeout=timeout,
                          env={**os.environ, "PYTHONPATH": _pythonpath(), "QA_SHOT_DIR": str(cfg.shots)})
    return proc.returncode, time.time() - started


def _run_extra(argv: list[str], cfg: Bench, timeout: int) -> tuple[int, float]:
    started = time.time()
    proc = subprocess.run([sys.executable, *argv], cwd=cfg.repo, timeout=timeout,
                          env={**os.environ, "PYTHONPATH": _pythonpath(str(cfg.repo)), "QA_SHOT_DIR": str(cfg.shots)})
    return proc.returncode, time.time() - started


def _read_ledger(shots: Path, name: str) -> dict | None:
    p = shots / f"{name}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def verdict(results: list[dict], floor: int) -> tuple[bool, str]:
    lines = ["| stage | exit | done | decided | fail | skip | s |", "|---|---|---|---|---|---|---|"]
    ok = True
    for r in results:
        good = r["completed"] and r["exit"] in (0, 3) and not r["failed"] and r["decided"] >= floor
        ok = ok and good
        lines.append(f"| {r['name']} | {r['exit']} | {'yes' if r['completed'] else 'NO'} | {r['decided']} | "
                     f"{len(r['failed'])} | {len(r['not_run'])} | {r['seconds']} |")
    for r in results:
        for f in r["failed"]:
            lines.append(f"- {r['name']}: {f[0]} — {f[1]}" if isinstance(f, (list, tuple)) else f"- {r['name']}: {f}")
        if not r["completed"]:
            lines.append(f"- {r['name']}: NOT RUN — no ledger written (exit {r['exit']})")
        elif r["decided"] < floor:
            lines.append(f"- {r['name']}: DECIDED NOTHING — {r['decided']} checks came to a verdict, {len(r['not_run'])} skipped. A stage that decides nothing is not evidence.")
    return ok, "\n".join(lines)


def _failure_ids(results) -> dict[str, set[str]]:
    """{stage: {failure label}} for every stage that COMPLETED — a stage that did not run has no failures to
    compare, and counting its absence as "fixed" is how a tier that stopped running reads as a tier that got better."""
    out = {}
    for r in results:
        if r.get("completed"):
            out[r["name"]] = {str(f[0] if isinstance(f, (list, tuple)) and f else f) for f in r.get("failed") or []}
    return out


def _delta(cfg: Bench, results) -> dict:
    """What is NEW since the last nightly of this origin.

    ana-log's browser tier had been red for days when one change added thirty-three failures; the run was
    already `failure`, so they changed nothing anyone could see. A constant is not a signal — the delta is.
    The baseline is kept outside the run's shot dir (QABENCH_DELTA_DIR, default ~/.qabench/delta), which
    persists on a self-hosted runner; a runner with no memory prints "no baseline" and nothing else.
    """
    import re as _re
    store = Path(os.environ.get("QABENCH_DELTA_DIR") or Path.home() / ".qabench" / "delta")
    key = _re.sub(r"[^A-Za-z0-9._-]+", "_", cfg.origin or "origin")
    now = _failure_ids(results)
    path = store / f"{key}.json"
    try:
        before = {k: set(v) for k, v in json.loads(path.read_text()).items()}
    except (OSError, ValueError, AttributeError):
        before = None
    try:
        store.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({k: sorted(v) for k, v in now.items()}, indent=1))
    except OSError as ex:
        return {"line": f"delta: baseline not stored ({ex}) — tomorrow's run will not know what is new", "new": [], "vanished": []}
    if before is None:
        return {"line": "delta: no baseline yet — stored this run; tomorrow's report names what is NEW", "new": [], "vanished": []}
    new = sorted(f"{s}::{f}" for s, fs in now.items() for f in fs - before.get(s, set()))
    vanished = sorted(f"{s}::{f}" for s, fs in before.items() if s in now for f in fs - now[s])
    lines = [f"delta since last night: {len(new)} NEW failure(s), {len(vanished)} gone"]
    lines += [f"  NEW   {n}" for n in new[:50]] + [f"  gone  {v}" for v in vanished[:50]]
    return {"line": "\n".join(lines), "new": new, "vanished": vanished}


def run(cfg: Bench, argv: list[str]) -> int:
    plan: list[tuple[str, list[str] | None]] = [(n, None) for n in SHARED] + [(n, a) for n, a in cfg.stages_extra]
    # A stage with nothing to measure is EXCLUDED BY DECLARATION, never run to
    # a vacuous verdict: eliad's console has no /api, and on 2026-09-06
    # endpoints_by_role ran there, decided nothing, and the floor rightly
    # called the night red. The manifest says so (api.include_prefixes: [])
    # and the plan prints why — a silent omission would read like a sweep.
    if not cfg.api.include_prefixes:
        plan = [p for p in plan if p[0] != "endpoints_by_role"]
        print("endpoints_by_role: not applicable — bench.api.include_prefixes is empty (declared in the manifest, not discovered)", flush=True)
    if "--only" in argv:
        keep = set(argv[argv.index("--only") + 1].split(","))
        plan = [p for p in plan if p[0] in keep]
    if "--except" in argv:
        drop = set(argv[argv.index("--except") + 1].split(","))
        plan = [p for p in plan if p[0] not in drop]
    timeout = int(os.environ.get("QABENCH_STAGE_TIMEOUT", "3600"))
    cfg.shots.mkdir(parents=True, exist_ok=True)
    results = []
    for name, extra_argv in plan:
        stale = cfg.shots / f"{name}.json"
        if stale.exists():
            stale.unlink()
        try:
            code, secs = _run_shared(name, cfg, timeout) if extra_argv is None else _run_extra(extra_argv, cfg, timeout)
        except subprocess.TimeoutExpired:
            code, secs = -1, float(timeout)
        led = _read_ledger(cfg.shots, name)
        results.append({
            "name": name, "exit": code, "seconds": round(secs), "completed": led is not None,
            "passed": (led or {}).get("passed", 0), "failed": (led or {}).get("failed", []),
            "not_run": (led or {}).get("not_run", []),
            "decided": (led or {}).get("decided", (led or {}).get("passed", 0) + len((led or {}).get("failed", []))),
        })
    ok, table = verdict(results, cfg.floor)
    smoke = _read_ledger(cfg.shots, "smoke") or {}
    swept_sha = smoke.get("swept_sha", "")
    delta = _delta(cfg, results)
    table += "\n" + delta["line"]
    print(table, flush=True)
    out = {"ok": ok, "qabench": __version__, "origin": cfg.origin, "swept_sha": swept_sha, "results": results,
           "delta": delta}
    (cfg.shots / "nightly.json").write_text(json.dumps(out, indent=1))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a") as fh:
            fh.write(f"## qabench nightly — {'green' if ok else 'RED'} — {cfg.origin} @ {swept_sha[:12] or '?'}\n\n{table}\n")
    if cfg.heartbeat.stamp:
        try:
            cfg.provider(cfg.heartbeat.stamp)({"key": cfg.heartbeat.key, "ok": ok, "swept_sha": swept_sha,
                                               "stages": len(results), "qabench": __version__})
            print(f"  heartbeat {cfg.heartbeat.key} stamped (ok={ok}, swept_sha={swept_sha[:12]})", flush=True)
        except Exception as ex:  # noqa: BLE001 — a heartbeat that kills the run hides the run
            print(f"  heartbeat NOT stamped: {type(ex).__name__}: {ex}", flush=True)
            ok = False
    return 0 if ok else 1
