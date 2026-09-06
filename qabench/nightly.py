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


def _run_shared(name: str, cfg: Bench, timeout: int) -> tuple[int, float]:
    started = time.time()
    proc = subprocess.run([sys.executable, "-m", "qabench", "stage", name], cwd=cfg.repo, timeout=timeout,
                          env={**os.environ, "QA_SHOT_DIR": str(cfg.shots)})
    return proc.returncode, time.time() - started


def _run_extra(argv: list[str], cfg: Bench, timeout: int) -> tuple[int, float]:
    started = time.time()
    proc = subprocess.run([sys.executable, *argv], cwd=cfg.repo, timeout=timeout,
                          env={**os.environ, "PYTHONPATH": str(cfg.repo), "QA_SHOT_DIR": str(cfg.shots)})
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
    print(table, flush=True)
    out = {"ok": ok, "qabench": __version__, "origin": cfg.origin, "swept_sha": swept_sha, "results": results}
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
