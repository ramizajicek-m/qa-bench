"""Offline escaped-defect comparison with explicit observation gaps.

Counts and exposure are data supplied by the estate's incident/release sources.
Missing source coverage is unknown, never an invented zero-defect baseline.
No network calls, test runs or writes. Percentage changes are descriptive and
are not statistical significance or proof that testing caused an improvement.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .acceptance import Invalid, _text, _time, read_json

SOURCES = {"user", "staff", "internal_review", "harness", "operations"}
SEVERITIES = {"critical", "high", "medium", "low"}


def compare(data: dict, *, now: datetime | None = None) -> dict:
    if type(data.get("version")) is not int or data["version"] != 1:
        raise Invalid("unsupported outcome input version")
    now = now or datetime.now(timezone.utc)
    observed_at = _time(data.get("observed_at"))
    if now.tzinfo is None or observed_at > now + timedelta(minutes=5):
        raise Invalid("observation timestamp is in the future")
    projects = data.get("projects")
    if not isinstance(projects, list) or not projects or any(not isinstance(p, str) or not p for p in projects):
        raise Invalid("explicit project population is required")
    if len(set(projects)) != len(projects):
        raise Invalid("duplicate project")
    windows = {}
    for name in ("baseline", "followup"):
        window = data.get(name)
        if not isinstance(window, dict):
            raise Invalid("both comparison windows are required")
        start, end = _time(window.get("start")), _time(window.get("end"))
        if start >= end:
            raise Invalid("comparison window is empty or reversed")
        if end > observed_at:
            raise Invalid("comparison window is not completely observed yet")
        coverage = window.get("observed_projects")
        if (not isinstance(coverage, list) or any(p not in projects for p in coverage)
                or len(coverage) != len(set(coverage))):
            raise Invalid("source observation coverage must name projects explicitly")
        releases = window.get("releases")
        if not isinstance(releases, dict) or any(p not in projects for p in releases):
            raise Invalid("invalid release exposure population")
        if any(type(n) is not int or n < 0 for n in releases.values()):
            raise Invalid("release exposures must be nonnegative integer counts")
        windows[name] = {"start": start, "end": end, "coverage": coverage, "releases": releases}
    if windows["baseline"]["end"] > windows["followup"]["start"]:
        raise Invalid("baseline and followup overlap")
    incidents = data.get("incidents")
    if not isinstance(incidents, list):
        raise Invalid("missing incident inventory")
    seen = set()
    clean = []
    for item in incidents:
        if not isinstance(item, dict):
            raise Invalid("malformed incident")
        _text(item.get("defect_id"), "canonical defect id")
        episode = _text(item.get("episode_id"), "incident episode id")
        if episode in seen:
            raise Invalid("duplicate episode id; deduplicate reports before measuring")
        seen.add(episode)
        if item.get("occurrence") not in ("new", "reopened"):
            raise Invalid("incident must distinguish new from reopened")
        if item.get("project") not in projects or item.get("source") not in SOURCES or item.get("severity") not in SEVERITIES:
            raise Invalid("invalid incident project/source/severity")
        if type(item.get("escaped")) is not bool:
            raise Invalid("incident must distinguish escaped from internally found")
        _text(item.get("source_reference"), "incident provenance")
        timestamp = _time(item.get("reported_at"))
        if timestamp > observed_at:
            raise Invalid("incident was reported after source observation")
        clean.append({**item, "timestamp": timestamp})
    rows = []
    for project in projects:
        row = {"project": project}
        for name, window in windows.items():
            observed = project in window["coverage"]
            items = [item for item in clean if item["project"] == project and window["start"] <= item["timestamp"] < window["end"]]
            escapes = [item for item in items if item["escaped"] and item["source"] in ("user", "staff")]
            exposure = window["releases"].get(project)
            row[name] = {
                "source_coverage": "observed" if observed else "unknown",
                "duration_days": (window["end"] - window["start"]).total_seconds() / 86400,
                "reported_escapes": len(escapes) if observed else None,
                "known_escape_ids": [item["defect_id"] for item in escapes],
                "known_episode_ids": [item["episode_id"] for item in escapes],
                "escapes_by_occurrence": {kind: sum(item["occurrence"] == kind for item in escapes) if observed else None
                                          for kind in ("new", "reopened")},
                "severe_escapes": sum(item["severity"] in ("critical", "high") for item in escapes) if observed else None,
                "reports_by_source": {source: sum(item["source"] == source for item in items) for source in sorted(SOURCES)},
                "releases": exposure,
                "escapes_per_100_releases": round(len(escapes) * 100 / exposure, 3) if observed and exposure else None,
            }
        old, new = row["baseline"], row["followup"]
        old_rate, new_rate = old["escapes_per_100_releases"], new["escapes_per_100_releases"]
        row["rate_reduction_percent"] = round((old_rate - new_rate) * 100 / old_rate, 2) if old_rate and new_rate is not None else None
        row["severe_increase"] = (new["severe_escapes"] > old["severe_escapes"]
                                  if old["severe_escapes"] is not None and new["severe_escapes"] is not None else None)
        measured = old_rate is not None and new_rate is not None
        row["rate_change_per_100_releases"] = round(new_rate - old_rate, 3) if measured else None
        row["comparison"] = "descriptive_only" if measured else "insufficient_evidence"
        rows.append(row)
    return {"status": "reported", "projects": rows, "causal_reduction_proven": False,
            "note": "Source completeness is declared by the collector; rates alone do not establish significance or causality."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = compare(read_json(args.input))
    except (Invalid, TypeError) as exc:
        print(json.dumps({"status": "unavailable", "reason": str(exc) if isinstance(exc, Invalid) else "malformed outcome input"}))
        return 3
    print(json.dumps(result, sort_keys=True))
    return 3 if any(p["comparison"] == "insufficient_evidence" for p in result["projects"]) else 0


if __name__ == "__main__":
    sys.exit(main())
