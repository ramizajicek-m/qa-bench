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
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import yaml

DEFAULT_ESTATE = Path(__file__).with_name("estate.yml")


def valid_commit(value: object) -> bool:
    """Health often uses short SHAs; a word such as 'unknown' is no identity."""
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{7,40}", value) is not None


class _Unreadable:
    """The read did not happen. NOT an answer about the thing being read.

    This exists because the morning report spent 2026-09-08 and 09-09 telling
    six projects they were RED because "the schedule has NEVER fired", while
    every one of those crons had fired — anat's thirteen times. `gh` had no
    usable auth inside the workflow, every call failed, `gh_json` returned None,
    and None was indistinguishable from "the API answered, and there are no
    scheduled runs". A failed read became the strongest negative claim this
    report can make.

    The cost was not the wrong sentence. It is that a report which says RED for
    everything every morning cannot be read at all, and inside two days of that
    noise two real failures went unseen: anat's staging refresh had been dead
    for three weeks, and five projects' runners were offline for nine hours —
    with the uptime alerts that watch whether the sites are up among the jobs
    that never ran.

    Falsy, so every existing `if not d` guard keeps treating it as "nothing came
    back"; distinguishable, so no verdict is ever derived from it.
    """

    __slots__ = ()

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "UNREADABLE"


#: Returned by a fetch whose call FAILED, as opposed to one that answered empty.
UNREADABLE = _Unreadable()


def gh_json(path: str) -> dict | list | None | _Unreadable:
    try:
        out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True, timeout=60).stdout
        return json.loads(out)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return UNREADABLE


def health_commit(url: str) -> str | None:
    """The `commit` an environment answers, or None when it cannot say."""
    try:
        r = httpx.get(url, timeout=20, follow_redirects=True)
        if r.status_code != 200:
            return None
        v = r.json().get("commit")
        return v if valid_commit(v) else None
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


def latest_run(repo: str, workflow: str) -> dict | None | _Unreadable:
    d = gh_json(f"repos/{repo}/actions/workflows/{workflow}/runs?per_page=1")
    if d is UNREADABLE:
        return UNREADABLE
    runs = (d or {}).get("workflow_runs") if isinstance(d, dict) else None
    return runs[0] if runs else None


def latest_scheduled_run(repo: str, workflow: str) -> dict | None:
    """The last run the CRON started. A hand dispatch proves the lane works;
    it says nothing about the schedule — on 2026-09-07 three projects had
    never had a scheduled night at all and every morning read green off the
    hand runs, and the ones that did fire fired 4.5 h late (a starved
    account is queued last)."""
    d = gh_json(f"repos/{repo}/actions/workflows/{workflow}/runs?event=schedule&per_page=1")
    if d is UNREADABLE:
        return UNREADABLE
    runs = (d or {}).get("workflow_runs") if isinstance(d, dict) else None
    return runs[0] if runs else None


def main_tip(repo: str, branch: str) -> str | None:
    d = gh_json(f"repos/{repo}/commits/{branch}")
    return d.get("sha") if isinstance(d, dict) else None


def compare(repo: str, base: str, head: str) -> str | None:
    """GitHub's word for head relative to base: identical, ahead, behind, diverged."""
    d = gh_json(f"repos/{repo}/compare/{base}...{head}")
    return d.get("status") if isinstance(d, dict) else None


def row_for(p: dict, now: datetime, *, fetch_run=latest_run, fetch_tip=main_tip, fetch_health=health_commit, fetch_compare=compare,
            fetch_scheduled=latest_scheduled_run) -> dict:
    """One project's row. `red` carries the reasons; an empty list is green."""
    red: list[str] = []
    notes: list[str] = []
    run = fetch_run(p["repo"], p["night_workflow"])
    expected = night_expected(p.get("cron_days", "0-6"), now)
    age_h = None
    # The schedule is a second claim: the cron fired. Judged separately so a
    # hand run cannot stand in for it.
    sched = fetch_scheduled(p["repo"], p["night_workflow"])
    sched_age_h = None
    if sched is not None and sched is not UNREADABLE:
        sched_age_h = round((now - datetime.fromisoformat(sched["created_at"].replace("Z", "+00:00"))).total_seconds() / 3600, 1)
    if expected:
        # A READ THAT FAILED IS NOT EVIDENCE ABOUT THE CRON. Still red — a
        # morning nobody can see is not a morning that is fine — but the
        # sentence must name the INSTRUMENT rather than accuse the schedule, so
        # that one broken credential cannot read as six broken projects. That is
        # exactly what it read as on 2026-09-08 and 09-09.
        if sched is UNREADABLE:
            red.append("could not read the schedule — gh failed here; this says NOTHING about whether the cron fired")
        elif sched is None:
            red.append("scheduled-run evidence unavailable — no scheduled run readable; a hand dispatch does not prove the schedule")
        elif sched_age_h > p.get("window_h", 30):
            red.append(f"the schedule last fired {sched_age_h}h ago — the nights since were hand dispatches, or none")
    if run is UNREADABLE:
        red.append("could not read the night workflow's runs — gh failed here")
    elif run is None:
        red.append("the night workflow has no runs at all" if expected else "no night run readable")
    else:
        created = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        age_h = round((now - created).total_seconds() / 3600, 1)
        if run.get("run_attempt", 1) > 1:
            attempt_timestamp = run.get("run_started_at")
            age_h = (round((now - datetime.fromisoformat(attempt_timestamp.replace("Z", "+00:00"))).total_seconds() / 3600, 1)
                     if attempt_timestamp else None)
            if age_h is None:
                red.append("night retry age unavailable — current attempt has no start timestamp")
        if run.get("status") != "completed":
            queued = run.get("status") in ("queued", "waiting", "requested", "pending")
            deadline = p.get("queue_deadline_h", 0.5) if queued else p.get("run_deadline_h", 3)
            # created_at survives a rerun, including time spent queued. GitHub's
            # current attempt timestamp is required before judging retry age.
            retry = run.get("run_attempt", 1) > 1
            attempt_start = run.get("run_started_at")
            if retry and not attempt_start:
                pass  # Already reported above, for completed retries too.
            else:
                clock_start = attempt_start if retry or not queued else run["created_at"]
                runtime_start = datetime.fromisoformat((clock_start or run["created_at"]).replace("Z", "+00:00"))
                active_age = round((now - runtime_start).total_seconds() / 3600, 1)
                message = f"night still {run.get('status')} ({active_age}h {'queued' if queued else 'running'}; deadline {deadline}h)"
                (red if active_age > deadline else notes).append(message)
        elif run.get("conclusion") != "success":
            red.append(f"last night was {run.get('conclusion')} ({age_h}h ago)")
        if expected and age_h is not None and age_h > p.get("window_h", 30):
            red.append(f"no night in {age_h}h — the schedule did not fire")
    tip = fetch_tip(p["repo"], p.get("main", "main"))
    integration_branch = p.get("staging_branch") or p.get("main", "main")
    integration_tip = (tip if integration_branch == p.get("main", "main")
                       else fetch_tip(p["repo"], integration_branch))
    if not valid_commit(tip):
        red.append("could not identify the production branch tip")
        tip = None
    if not valid_commit(integration_tip):
        red.append(f"could not identify the integration branch {integration_branch}")
        integration_tip = None
    prod = fetch_health(p["production"])
    stag = fetch_health(p["staging"]) if p.get("staging") else None
    prod = prod if valid_commit(prod) else None
    stag = stag if valid_commit(stag) else None
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
    elif integration_tip and stag and not integration_tip.startswith(stag) and not stag.startswith(integration_tip):
        notes.append(f"staging serves {stag[:8]}, {integration_branch} is {integration_tip[:8]} — a deploy in flight, or the day lane is red")
    return {"name": p["name"], "night": (run or {}).get("conclusion") or (run or {}).get("status") or "unreadable",
            "night_age_h": age_h, "night_sha": (run or {}).get("head_sha", "")[:8], "expected": expected,
            "night_event": (run or {}).get("event"), "schedule_age_h": sched_age_h,
            "schedule_unreadable": sched is UNREADABLE,
            "main": (tip or "")[:8], "integration_branch": integration_branch, "integration_tip": (integration_tip or "")[:8],
            "production": (prod or "")[:8], "staging": (stag or "")[:8],
            "red": red, "notes": notes}


def render(rows: list[dict]) -> str:
    lines = ["| project | night | age | by | schedule fired | swept | main | staging | production | verdict |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        verdict = "RED — " + "; ".join(r["red"]) if r["red"] else ("ok" + (" — " + "; ".join(r["notes"]) if r["notes"] else ""))
        age = "" if r["night_age_h"] is None else f"{r['night_age_h']}h"
        by = {"schedule": "cron", "workflow_dispatch": "hand"}.get(r.get("night_event") or "", r.get("night_event") or "")
        # "never" is a claim about the cron; "?" is a claim about our reading of
        # it. The table is what people actually look at, so the distinction has
        # to survive into the column and not only into the verdict sentence.
        if r.get("schedule_unreadable"):
            sched = "?"
        else:
            sched = "never" if r.get("schedule_age_h") is None else f"{r['schedule_age_h']}h ago"
        lines.append(f"| {r['name']} | {r['night']} | {age} | {by} | {sched} | {r['night_sha']} | {r['main']} | {r['staging'] or '—'} | {r['production'] or '—'} | {verdict} |")
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
    print(f"\nall {len(rows)} projects ok", file=sys.stderr if "--json" in argv else sys.stdout)
    return 0
