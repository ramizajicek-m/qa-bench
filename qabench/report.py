"""report — one row per project, every morning: did the night run, was it green,
does production answer with the commit it swept, how far behind main is each
environment. Exit 1 when any row is red, so the workflow that runs it fails and
somebody hears about it (C8: a night that did not run must not read like a
night with nothing to say).

    python -m qabench report                 # the estate in qabench/estate.yml
    python -m qabench report --estate FILE   # another estate
    python -m qabench report --json          # rows as JSON, for another program

Reads GitHub through `gh api` (the runner's own login) and each environment's
/health over HTTP. Both are fetched, never assumed; a fetch that fails is a
red row that says "could not read", never a green one.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import yaml

DEFAULT_ESTATE = Path(__file__).with_name("estate.yml")


def gh_json(path: str) -> dict | list | None:
    try:
        out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True, timeout=60).stdout
        return json.loads(out)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def health_commit(url: str) -> str | None:
    """The `commit` an environment answers, or None when it cannot say."""
    try:
        r = httpx.get(url, timeout=20, follow_redirects=True)
        if r.status_code != 200:
            return None
        v = r.json().get("commit")
        return v or None
    except Exception:  # noqa: BLE001
        return None


def _cron_days(spec: str) -> set[int]:
    days: set[int] = set()
    for part in spec.split(","):
        a, _, b = part.partition("-")
        days.update(range(int(a), int(b or a) + 1))
    return days


def night_expected(cron_days: str, now: datetime) -> bool:
    """Was a night scheduled in the last 24 hours? (cron numbering: 0 = Sunday)"""
    yesterday = (now - timedelta(days=1)).weekday()          # Monday = 0
    cron_yesterday = (yesterday + 1) % 7                      # Sunday = 0
    return cron_yesterday in _cron_days(cron_days)


def latest_run(repo: str, workflow: str) -> dict | None:
    d = gh_json(f"repos/{repo}/actions/workflows/{workflow}/runs?per_page=1")
    runs = (d or {}).get("workflow_runs") if isinstance(d, dict) else None
    return runs[0] if runs else None


def main_tip(repo: str, branch: str) -> str | None:
    d = gh_json(f"repos/{repo}/commits/{branch}")
    return d.get("sha") if isinstance(d, dict) else None


def compare(repo: str, base: str, head: str) -> str | None:
    """GitHub's word for head relative to base: identical, ahead, behind, diverged."""
    d = gh_json(f"repos/{repo}/compare/{base}...{head}")
    return d.get("status") if isinstance(d, dict) else None


def row_for(p: dict, now: datetime, *, fetch_run=latest_run, fetch_tip=main_tip, fetch_health=health_commit, fetch_compare=compare) -> dict:
    """One project's row. `red` carries the reasons; an empty list is green."""
    red: list[str] = []
    notes: list[str] = []
    run = fetch_run(p["repo"], p["night_workflow"])
    expected = night_expected(p.get("cron_days", "0-6"), now)
    age_h = None
    if run is None:
        red.append("could not read the night workflow's runs" if expected else "no night run readable")
    else:
        created = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        age_h = round((now - created).total_seconds() / 3600, 1)
        if run.get("status") != "completed":
            notes.append(f"night still {run.get('status')} ({age_h}h old)")
        elif run.get("conclusion") != "success":
            red.append(f"last night was {run.get('conclusion')} ({age_h}h ago)")
        if expected and age_h > p.get("window_h", 30):
            red.append(f"no night in {age_h}h — the schedule did not fire")
    tip = fetch_tip(p["repo"], p.get("main", "main"))
    prod = fetch_health(p["production"])
    stag = fetch_health(p["staging"]) if p.get("staging") else None
    if prod is None:
        red.append("production does not name its commit (unreachable, or no `commit` in /health)")
    elif run and run.get("conclusion") == "success" and not prod.startswith(run["head_sha"][: len(prod)]) and not run["head_sha"].startswith(prod):
        # Production is not the build the last green night swept. Newer and on
        # main is a hand promote through the gate (the next night sweeps it) —
        # a note. Older means the promote never happened; off main means a
        # build nobody tested — both red.
        rel = fetch_compare(p["repo"], run["head_sha"], prod)      # prod relative to the swept SHA
        if rel == "ahead":
            notes.append(f"production serves {prod[:8]}, promoted by hand after the last night swept {run['head_sha'][:8]} — the next night sweeps it")
        elif rel == "behind":
            red.append(f"production serves {prod[:8]}, OLDER than the last green night's {run['head_sha'][:8]} — the promote did not happen")
        else:
            red.append(f"production serves {prod[:8]}, which is not on the line the last green night swept ({run['head_sha'][:8]}; compare says {rel})")
    if tip and prod and not tip.startswith(prod) and not prod.startswith(tip):
        notes.append(f"production is behind main ({prod[:8]} vs {tip[:8]}) — expected until the next green night")
    if p.get("staging") and stag is None:
        red.append("staging does not name its commit")
    elif tip and stag and not tip.startswith(stag) and not stag.startswith(tip):
        notes.append(f"staging serves {stag[:8]}, main is {tip[:8]} — a deploy in flight, or the day lane is red")
    return {"name": p["name"], "night": (run or {}).get("conclusion") or (run or {}).get("status") or "unreadable",
            "night_age_h": age_h, "night_sha": (run or {}).get("head_sha", "")[:8], "expected": expected,
            "main": (tip or "")[:8], "production": (prod or "")[:8], "staging": (stag or "")[:8],
            "red": red, "notes": notes}


def render(rows: list[dict]) -> str:
    lines = ["| project | night | age | swept | main | staging | production | verdict |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        verdict = "RED — " + "; ".join(r["red"]) if r["red"] else ("ok" + (" — " + "; ".join(r["notes"]) if r["notes"] else ""))
        age = "" if r["night_age_h"] is None else f"{r['night_age_h']}h"
        lines.append(f"| {r['name']} | {r['night']} | {age} | {r['night_sha']} | {r['main']} | {r['staging'] or '—'} | {r['production'] or '—'} | {verdict} |")
    return "\n".join(lines)


def run(argv: list[str]) -> int:
    estate = Path(argv[argv.index("--estate") + 1]) if "--estate" in argv else DEFAULT_ESTATE
    projects = yaml.safe_load(estate.read_text())["projects"]
    now = datetime.now(timezone.utc)
    rows = [row_for(p, now) for p in projects]
    if "--json" in argv:
        print(json.dumps(rows, indent=1))
    else:
        text = f"### The estate on {now.strftime('%Y-%m-%d %H:%M')} UTC\n\n" + render(rows)
        print(text)
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a") as fh:
                fh.write(text + "\n")
    reds = [r for r in rows if r["red"]]
    if reds:
        print(f"\n{len(reds)} of {len(rows)} projects RED: " + ", ".join(r["name"] for r in reds), file=sys.stderr)
        return 1
    print(f"\nall {len(rows)} projects ok")
    return 0
