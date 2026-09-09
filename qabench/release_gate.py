"""Require completed checks for the exact candidate, workflow and run attempt.

Stdlib-only so a production workflow can execute this file from a pinned kit
checkout before installing application dependencies or exposing deploy tokens.
The enclosing nightly can still be running its promotion dispatch; only the
explicit prerequisite jobs must have completed. Nothing here deploys or waits.

GitHub contracts: docs.github.com/en/rest/actions/workflow-runs and workflow-jobs.
Exit 0: evidence accepted; 1: evidence refuses promotion; 3: could not obtain it.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode


class Refused(ValueError):
    pass


class Unavailable(RuntimeError):
    pass


def gh_json(path: str) -> dict:
    try:
        result = subprocess.run(["gh", "api", path], check=True, text=True,
                                capture_output=True, timeout=45)
        data = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        # Do not echo CLI stderr: it may include credential-bearing diagnostics.
        raise Unavailable(f"GitHub evidence unreadable at {path} ({type(exc).__name__})") from exc
    if not isinstance(data, dict):
        raise Unavailable("GitHub evidence is not an object")
    return data


def _positive(value: object, field: str) -> int:
    if type(value) is not int or value < 1:
        raise Unavailable(f"missing or invalid {field}")
    return value


def _time(value: object) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise Unavailable("missing or invalid evidence time") from exc
    if parsed.tzinfo is None:
        raise Unavailable("evidence time has no timezone")
    return parsed


def check(*, repo: str, sha: str, workflow: str, branch: str,
          required: list[str], events: list[str], run_id: int | None = None,
          attempt: int | None = None, max_age_hours: float = 30,
          immutable_push_evidence: bool = False,
          fetch=gh_json, now: datetime | None = None) -> dict:
    """Return an auditable verdict or raise; never search for older green runs."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise Refused("repo must be owner/repository")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise Refused("candidate must be a resolved full 40-character SHA")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.ya?ml", workflow):
        raise Refused("workflow must be a workflow filename")
    if not branch or not required or any(not job.strip() for job in required):
        raise Refused("branch and nonempty required job names are mandatory")
    if len(set(required)) != len(required) or not events:
        raise Refused("required job names must be unique and events must be explicit")
    if not math.isfinite(max_age_hours) or max_age_hours <= 0:
        raise Refused("evidence age limit must be finite and positive")
    if type(immutable_push_evidence) is not bool:
        raise Refused("immutable push evidence must be a boolean")
    if immutable_push_evidence and set(events) != {"push"}:
        raise Refused("immutable evidence is allowed only for push checks; deployed checks must be fresh")
    if run_id is not None and (type(run_id) is not int or run_id < 1):
        raise Refused("run id must be positive")
    if attempt is not None and (type(attempt) is not int or attempt < 1):
        raise Refused("run attempt must be positive")
    if attempt is not None and run_id is None:
        raise Refused("an attempt requires its run id")

    prefix = f"repos/{repo}/actions"
    definition = fetch(f"{prefix}/workflows/{quote(workflow, safe='')}")
    workflow_id = _positive(definition.get("id"), "workflow id")
    if definition.get("path") != f".github/workflows/{workflow}":
        raise Refused("workflow path does not match the required workflow")
    def newest():
        # Select within the required branch/event contract. A feature-branch
        # dispatch of the same commit must not shadow the main branch's night.
        candidates = []
        for event in set(events):
            query = urlencode({"head_sha": sha, "branch": branch, "event": event, "per_page": 1})
            runs = fetch(f"{prefix}/workflows/{workflow_id}/runs?{query}").get("workflow_runs")
            if not isinstance(runs, list):
                raise Unavailable("workflow run list missing")
            if runs:
                if not isinstance(runs[0], dict):
                    raise Unavailable("malformed workflow run")
                candidates.append(_positive(runs[0].get("id"), "latest run id"))
        if not candidates:
            raise Refused("no eligible run exists for the candidate SHA")
        return max(candidates)

    newest_id = newest()
    if run_id is not None and newest_id != run_id:
        raise Refused("requested run is not the latest run for this candidate")
    run_id = newest_id
    run = fetch(f"{prefix}/runs/{run_id}")
    current_attempt = _positive(run.get("run_attempt"), "run attempt")
    if attempt is not None and attempt != current_attempt:
        raise Refused("requested attempt has been superseded by a rerun")
    repository = run.get("repository")
    if not isinstance(repository, dict) or not isinstance(repository.get("full_name"), str):
        raise Unavailable("run repository identity is malformed")
    if (run.get("id") != run_id or run.get("workflow_id") != workflow_id
            or repository["full_name"].casefold() != repo.casefold()
            or run.get("head_sha") != sha or run.get("head_branch") != branch
            or run.get("event") not in events):
        raise Refused("run identity disagrees with repo/workflow/SHA/branch/event")
    started = _time(run.get("run_started_at"))
    now = now or datetime.now(timezone.utc)
    age = now - started
    if age < -timedelta(minutes=5) or (not immutable_push_evidence and age > timedelta(hours=max_age_hours)):
        raise Refused("run evidence is stale or future-dated")

    jobs: list[dict] = []
    total = None
    for page in range(1, 102):
        payload = fetch(f"{prefix}/runs/{run_id}/attempts/{current_attempt}/jobs?per_page=100&page={page}")
        expected = payload.get("total_count")
        batch = payload.get("jobs")
        if type(expected) is not int or expected < 0 or not isinstance(batch, list):
            raise Unavailable("job listing has no count or jobs")
        if total is not None and expected != total:
            raise Unavailable("job listing changed while it was read")
        total = expected
        if any(not isinstance(job, dict) for job in batch):
            raise Unavailable("malformed job in listing")
        jobs.extend(batch)
        if len(jobs) == total:
            break
        if not batch or len(jobs) > total:
            raise Unavailable("job listing is incomplete or inconsistent")
    else:
        raise Unavailable("job listing exceeded bounded pagination")
    ids = [_positive(job.get("id"), "job id") for job in jobs]
    if len(ids) != len(set(ids)):
        raise Unavailable("duplicate job identities across pages")

    accepted = []
    for name in required:
        # Exact names, including every expected expanded matrix member. A
        # prefix cannot distinguish a complete matrix from its sole survivor.
        matches = [job for job in jobs if job.get("name") == name]
        if not matches:
            raise Refused(f"required job {name!r} did not run")
        if len(matches) != 1:
            raise Unavailable(f"required job name {name!r} is ambiguous")
        for job in matches:
            if job.get("run_id") != run_id or job.get("head_sha") != sha:
                raise Refused(f"job {name!r} belongs to another run or candidate")
            job_attempt = _positive(job.get("run_attempt"), "job attempt")
            if job_attempt > current_attempt:
                raise Refused(f"job {name!r} belongs to a future attempt")
            if job.get("status") != "completed" or job.get("conclusion") != "success":
                raise Refused(f"required job {job.get('name')!r} is {job.get('status')}/{job.get('conclusion')}")
            completed = _time(job.get("completed_at"))
            # GitHub includes inherited successful jobs in a failed-only rerun
            # (observed Tharros run 34107882560/attempts/2). They are valid
            # same-SHA evidence, but a fresh rerun cannot rejuvenate old proof.
            if (not immutable_push_evidence and completed < now - timedelta(hours=max_age_hours)) or completed > now + timedelta(minutes=5):
                raise Refused(f"job {name!r} evidence is stale or future-dated")
            accepted.append({"id": job["id"], "name": job["name"], "attempt": job_attempt,
                             "completed_at": job["completed_at"]})

    # A rerun beginning during pagination invalidates the evidence just read.
    reread = fetch(f"{prefix}/runs/{run_id}")
    if reread.get("run_attempt") != current_attempt or reread.get("head_sha") != sha:
        raise Refused("run changed while evidence was read")
    if newest() != run_id:
        raise Refused("a newer eligible run appeared while evidence was read")
    return {"status": "accepted", "repo": repo, "sha": sha, "workflow": workflow,
            "branch": branch, "run_id": run_id, "attempt": current_attempt,
            "immutable_push_evidence": immutable_push_evidence,
            "required_jobs": accepted, "observed_at": now.isoformat()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("repo", "sha", "workflow", "branch"):
        parser.add_argument(f"--{arg}", required=True)
    parser.add_argument("--required", action="append", required=True)
    parser.add_argument("--event", action="append", required=True)
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--attempt", type=int)
    parser.add_argument("--max-age-hours", type=float, default=30)
    parser.add_argument("--immutable-push-evidence", action="store_true",
                        help="Reuse unchanged-SHA push proof without age expiry; never for deployed/night checks")
    args = vars(parser.parse_args(argv))
    args["events"] = args.pop("event")
    try:
        print(json.dumps(check(**args), sort_keys=True))
    except (Refused, Unavailable) as exc:
        print(json.dumps({"status": "unavailable" if isinstance(exc, Unavailable) else "refused",
                          "reason": str(exc)}), file=sys.stderr)
        return 3 if isinstance(exc, Unavailable) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
