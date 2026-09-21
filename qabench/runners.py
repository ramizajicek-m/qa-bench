"""runners — the shared runner's queue, seen from every project at once.

    python -m qabench runners [--estate FILE] [--json]

WHY. A session cannot diagnose its own wait, because the queue it is in is not
visible from the repository it is in. ana-log's CI sat `queued` for an hour on
2026-09-21; the runner API said ONLINE and BUSY; the only unfinished runs in
ana-log were its own. The three facts a session can obtain — mine is queued,
the runner is busy, nothing of mine is running — are exactly what a HUNG runner
looks like too, and three times that day the correct inference from them was
"it is hung". It was another repository's work. Every project sharing the
machine pays that diagnosis separately, and polling for the answer consumes the
machine whose scarcity is the question.

So this reads every project in the estate file and prints, per runner, what it
is running, from which repository, and for how long — and every queued run with
how long it has waited. One view, the same for every consumer. A second runner
shortens the queue; it does not make it visible, so the two are complements.

A repository it cannot read is printed as UNREADABLE with the reason, never as
an empty queue: "could not look" is a third state, and folding it into "nothing
running" is the defect this kit refuses everywhere else.

AND A GREEN RUN IS NOT A DEPLOY (`--served`). tharros's staging served one commit
from 05:32 UTC to past 12:00 on 2026-09-21 while six pushes landed on main;
Railway recorded every one as SKIPPED, and nothing reported it — a session found
it by querying Railway. Three were red (e2e broke on main), three were batched
into the next run, and the one that went green did so 2h15m after it was pushed,
behind one self-hosted runner. `--served` asks each staging which commit it
serves and compares it with the NEWEST commit whose push CI went green on the
branch that deploys it: a staging behind its newest green commit is red, with
how long that commit has been green.

Exit: 0 read (and, with --served, every staging serves its newest green commit)
· 1 --served and a staging is behind · 3 no project could be read.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import yaml

from . import report


def _age(ts: str | None, now: dt.datetime) -> str:
    if not ts:
        return "?"
    try:
        t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return "?"
    mins = int((now - t).total_seconds() // 60)
    return f"{mins // 60}h{mins % 60:02d}m" if mins >= 60 else f"{mins}m"


def survey(projects: list[dict], *, fetch=report.gh_json, now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    running, queued, unreadable = [], [], []
    for p in projects:
        repo = p.get("repo")
        if not repo:
            continue
        for status in ("in_progress", "queued"):
            runs = fetch(f"repos/{repo}/actions/runs?status={status}&per_page=30")
            if not isinstance(runs, dict):
                unreadable.append({"repo": repo, "status": status,
                                   "why": getattr(runs, "reason", "") or "gh could not read it"})
                continue
            for r in runs.get("workflow_runs") or []:
                row = {"repo": repo, "workflow": r.get("name", "?"), "sha": str(r.get("head_sha", ""))[:9],
                       "branch": r.get("head_branch", "")}
                if status == "queued":
                    queued.append({**row, "waiting": _age(r.get("created_at"), now)})
                    continue
                jobs = fetch(f"repos/{repo}/actions/runs/{r.get('id')}/jobs?per_page=50")
                live = [j for j in (jobs.get("jobs") or []) if j.get("status") == "in_progress"] \
                    if isinstance(jobs, dict) else []
                if not isinstance(jobs, dict):
                    unreadable.append({"repo": repo, "status": f"jobs of run {r.get('id')}",
                                       "why": "gh could not read it"})
                for j in live or [{}]:
                    running.append({**row, "job": j.get("name", "?"), "runner": j.get("runner_name") or "(none yet)",
                                    "for": _age(j.get("started_at") or r.get("run_started_at"), now)})
    return {"running": running, "queued": queued, "unreadable": unreadable}


def served(projects: list[dict], *, fetch=report.gh_json, health=report.health_commit,
           now: dt.datetime | None = None) -> list[dict]:
    """Per project: the commit staging serves against the newest green push on its deploy branch."""
    now = now or dt.datetime.now(dt.timezone.utc)
    out = []
    for p in projects:
        repo, url = p.get("repo"), p.get("staging")
        branch = p.get("staging_branch") or p.get("main") or "main"
        if not repo or not url:
            continue
        runs = fetch(f"repos/{repo}/actions/runs?branch={branch}&event=push&status=success&per_page=10")
        green = (runs.get("workflow_runs") or [None])[0] if isinstance(runs, dict) else None
        serves = health(url)
        row = {"repo": repo, "branch": branch, "serves": (serves or "")[:9],
               "newest_green": str((green or {}).get("head_sha", ""))[:9],
               "green_for": _age((green or {}).get("updated_at"), now)}
        if not isinstance(runs, dict) or not serves:
            row["state"] = "UNREADABLE"
        elif not green:
            row["state"] = "no green push run"
        elif str(green["head_sha"]).startswith(serves) or serves.startswith(str(green["head_sha"])[: len(serves)]):
            row["state"] = "ok"
        else:
            # By HISTORY, not by string: staging may serve a commit NEWER than the newest green one (a deploy
            # that did not wait for CI), which is not "behind". The first version compared strings and
            # called ana-log's staging behind while it served a descendant.
            cmp = fetch(f"repos/{repo}/compare/{serves}...{green['head_sha']}")
            status = cmp.get("status") if isinstance(cmp, dict) else None
            row["state"] = {"ahead": "BEHIND", "behind": "ahead of green", "diverged": "DIVERGED",
                            "identical": "ok"}.get(status, "UNREADABLE")
        out.append(row)
    return out


def run(argv: list[str], *, echo=print, fetch=report.gh_json) -> int:
    path = Path(argv[argv.index("--estate") + 1]) if "--estate" in argv else report.DEFAULT_ESTATE
    try:
        projects = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("projects") or []
    except (OSError, yaml.YAMLError) as ex:
        print(f"runners: cannot read {path}: {ex} (exit 3)", file=sys.stderr)
        return 3
    out = survey(projects, fetch=fetch)
    if "--json" in argv:
        echo(json.dumps(out, indent=1, ensure_ascii=False))
    else:
        echo(f"runners: {len(out['running'])} job(s) running, {len(out['queued'])} run(s) queued, "
             f"{len(out['unreadable'])} unreadable")
        for r in sorted(out["running"], key=lambda x: x["runner"]):
            echo(f"  RUNNING  {r['runner']:28} {r['repo']:32} {r['workflow']} / {r['job']}  {r['sha']}  for {r['for']}")
        for q in out["queued"]:
            echo(f"  queued   {'':28} {q['repo']:32} {q['workflow']}  {q['sha']}  waiting {q['waiting']}")
        for u in out["unreadable"]:
            echo(f"  UNREADABLE {u['repo']} ({u['status']}): {u['why']} — could not look, which is not 'nothing'")
    readable = {p.get("repo") for p in projects} - {u["repo"] for u in out["unreadable"]}
    if not readable:
        return 3
    if "--served" in argv:
        rows = served(projects, fetch=fetch)
        for r in rows:
            echo(f"  {r['state']:10} {r['repo']:32} staging serves {r['serves'] or '?':9}  newest green on "
                 f"{r['branch']}: {r['newest_green'] or '?':9} (green for {r['green_for']})")
        if any(r["state"] == "BEHIND" for r in rows):
            return 1
    return 0
