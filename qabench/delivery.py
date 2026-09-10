"""Read-only local worktree inventory and explicit ready-work deadlines (C8).

This module never fetches, commits, merges, pushes, runs hooks or starts tests.
Local ancestry is labelled local: it cannot establish remote deployment.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .acceptance import Invalid, _hex, _text, _time, read_json


def _git(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null",
                                 "-C", str(repo), *args], capture_output=True,
                                check=True, timeout=15,
                                env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
        return result.stdout.decode("utf-8")
    except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
        raise Invalid("local git observation unavailable") from exc


def inventory(repo: Path, base: str) -> dict:
    """Resolve base once; do not make a stale local ref look like remote truth."""
    if _git(repo, "rev-parse", "--is-shallow-repository").strip() != "false":
        raise Invalid("local ancestry is incomplete; shallow history cannot establish integration")
    base_sha = _git(repo, "rev-parse", "--verify", "--end-of-options", base + "^{commit}").strip()
    _hex(base_sha, 40, "local base SHA")
    listing = _git(repo, "worktree", "list", "--porcelain", "-z")
    rows = []
    for record in listing.split("\0\0"):
        if not record.strip("\0"):
            continue
        fields = dict(field.partition(" ")[::2] for field in record.split("\0") if field)
        path = fields.get("worktree")
        if not path:
            raise Invalid("malformed git worktree inventory")
        try:
            # Read the actual checkout HEAD, not only worktree registration.
            tree = Path(path)
            # Status may run clean/process filters while comparing content.
            # Refuse those repositories instead of invoking arbitrary programs
            # or silently changing their interpretation of the working tree.
            keys = _git(tree, "config", "--list", "--name-only").splitlines()
            if any(re.fullmatch(r"filter\..*\.(clean|process)", key) for key in keys):
                raise Invalid("content filter configured (including global config); conservative inventory cannot establish whether it applies")
            head = _git(tree, "rev-parse", "HEAD").strip()
            _hex(head, 40, "worktree SHA")
            status = _git(tree, "status", "--porcelain=v1", "-z", "--untracked-files=normal")
            ahead = int(_git(tree, "rev-list", "--count", f"{base_sha}..{head}").strip())
            behind = int(_git(tree, "rev-list", "--count", f"{head}..{base_sha}").strip())
            if (_git(tree, "rev-parse", "HEAD").strip() != head
                    or _git(tree, "status", "--porcelain=v1", "-z", "--untracked-files=normal") != status):
                raise Invalid("worktree changed while it was observed")
            rows.append({"worktree": path, "branch": fields.get("branch"), "head": head,
                         "dirty": bool(status), "ahead": ahead, "behind": behind,
                         "observation": "local_git"})
        except Invalid as exc:
            rows.append({"worktree": path, "observation": "unavailable", "reason": str(exc)})
    if not rows:
        raise Invalid("no worktrees observed")
    return {"version": 1, "base_ref": base, "base_sha": base_sha,
            "observed_at": datetime.now(timezone.utc).isoformat(), "worktrees": rows}


def evaluate(snapshot: dict, ledger: dict, *, now: datetime | None = None,
             deadline_hours: int = 2, escalation_hours: int = 4) -> dict:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or not (0 < deadline_hours <= escalation_hours):
        raise Invalid("invalid clock or ready-work deadlines")
    if snapshot.get("version") != 1 or ledger.get("version") != 1:
        raise Invalid("unsupported delivery input version")
    age = now - _time(snapshot.get("observed_at"))
    if age < -timedelta(minutes=5) or age > timedelta(minutes=15):
        raise Invalid("local worktree snapshot is stale")
    _hex(snapshot.get("base_sha"), 40, "local base SHA")
    declarations = ledger.get("items")
    observed = snapshot.get("worktrees")
    if not isinstance(declarations, list) or not isinstance(observed, list) or not observed:
        raise Invalid("missing worktree inventory or readiness declarations")
    by_path = {}
    for item in declarations:
        if not isinstance(item, dict):
            raise Invalid("malformed readiness declaration")
        path = _text(item.get("worktree"), "declared worktree")
        if path in by_path:
            raise Invalid("duplicate worktree declaration")
        by_path[path] = item
    rows, seen = [], set()
    for observed_row in observed:
        if not isinstance(observed_row, dict):
            raise Invalid("malformed worktree observation")
        path = _text(observed_row.get("worktree"), "observed worktree")
        if path in seen:
            raise Invalid("duplicate worktree observation")
        seen.add(path)
        row = {**observed_row, "findings": [], "notes": [], "remote_state": "not_observed"}
        rows.append(row)
        item = by_path.get(path)
        if observed_row.get("observation") != "local_git":
            row["findings"].append("worktree could not be observed")
            continue
        _hex(row.get("head"), 40, "worktree head")
        if type(row.get("dirty")) is not bool or any(type(row.get(k)) is not int or row[k] < 0 for k in ("ahead", "behind")):
            raise Invalid("invalid local worktree counts")
        if item is None:
            row["notes"].append("dirty work in progress" if row["dirty"] else "readiness not declared")
            continue
        _text(item.get("owner"), "ready-work owner")
        _hex(item.get("candidate"), 40, "declared candidate")
        ready_at = _time(item.get("ready_at"))
        if ready_at > now:
            raise Invalid("ready timestamp is in the future")
        row.update(owner=item["owner"], ready_at=item["ready_at"])
        if item["candidate"] != row["head"] or row["dirty"]:
            row["findings"].append("readiness no longer matches the clean candidate; re-evaluate readiness")
            continue
        if row["ahead"] == 0:
            row["notes"].append("candidate integrated into the observed local base; remote/deployment unverified")
            continue
        parked = item.get("parked")
        if parked is not None:
            if not isinstance(parked, dict):
                raise Invalid("invalid parking declaration")
            _text(parked.get("reason"), "parking reason")
            expiry = _time(parked.get("until"))
            if expiry > now:
                row["notes"].append("explicitly parked with owner, reason and expiry")
                row["parked_until"] = parked["until"]
                continue
            row["findings"].append("parking expired")
        elapsed = (now - ready_at).total_seconds() / 3600
        row["ready_age_hours"] = round(elapsed, 2)
        if elapsed >= deadline_hours:
            row["findings"].append("ready candidate remains unmerged")
        if elapsed >= escalation_hours:
            row["findings"].append("ready-work escalation deadline exceeded")
        if item.get("blocker"):
            row["blocker"] = _text(item["blocker"], "blocker")
    for path in by_path.keys() - seen:
        rows.append({"worktree": path, "findings": ["declared ready worktree is missing from inventory"],
                     "notes": [], "remote_state": "not_observed"})
    return {"status": "failed" if any(r["findings"] for r in rows) else "observed",
            "base_sha": snapshot["base_sha"], "observed_at": snapshot["observed_at"], "worktrees": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--base", required=True, help="local ref only; no fetch is performed")
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = evaluate(inventory(args.repo, args.base), read_json(args.ledger))
    except (Invalid, TypeError, ValueError) as exc:
        result = {"status": "unavailable", "reason": str(exc) if isinstance(exc, Invalid) else "invalid delivery data"}
    print(json.dumps(result, sort_keys=True))
    return {"observed": 0, "failed": 1, "unavailable": 3}[result["status"]]


if __name__ == "__main__":
    sys.exit(main())
