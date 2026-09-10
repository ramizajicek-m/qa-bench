"""Offline acceptance evidence checks (C3/C8/C10/C12).

No test execution, application imports, subprocesses, sockets or deployment.
The evaluator controller must authenticate results OUTSIDE the candidate's
process. A locally supplied key/contract is useful for qualification, not
proof that production's trust boundary has been provisioned.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


class Invalid(ValueError):
    """Missing or malformed evidence, distinct from an observed product failure."""


def canonical(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise Invalid("value cannot be encoded as canonical JSON") from exc


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid("duplicate JSON key")
        result[key] = value
    return result


def read_json(path: Path) -> dict:
    def finite(number):
        value = float(number)
        if not math.isfinite(value):
            raise Invalid("nonfinite JSON number")
        return value

    try:
        if path.stat().st_size > 8_000_000:
            raise Invalid("JSON input exceeds size limit")
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs,
                           parse_float=finite,
                           parse_constant=lambda _: (_ for _ in ()).throw(Invalid("nonfinite JSON number")))
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise Invalid("JSON input is unreadable or malformed") from exc
    if not isinstance(value, dict):
        raise Invalid("JSON input must be an object")
    return value


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise Invalid(f"missing or invalid {field}")
    return value


def _hex(value, length, field):
    if not isinstance(value, str) or not re.fullmatch(f"[0-9a-f]{{{length}}}", value):
        raise Invalid(f"invalid {field}")
    return value


def _time(value):
    try:
        stamp = datetime.fromisoformat(_text(value, "timestamp").replace("Z", "+00:00"))
    except ValueError as exc:
        raise Invalid("invalid timestamp") from exc
    if stamp.tzinfo is None:
        raise Invalid("timestamp requires timezone")
    return stamp


def contract_cases(contract: dict) -> dict[str, dict]:
    if type(contract.get("version")) is not int or contract["version"] != 1:
        raise Invalid("unsupported contract version")
    for field in ("project", "requirement_source"):
        _text(contract.get(field), field)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", _text(contract.get("repo"), "repo")):
        raise Invalid("invalid repository")
    scenarios = contract.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise Invalid("contract has no scenarios")
    result = {}
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise Invalid("malformed scenario")
        name = _text(scenario.get("id"), "scenario id")
        if name in result:
            raise Invalid("duplicate scenario id")
        for field in ("requirement", "root_cause", "sibling_scope", "expected_outcome"):
            _text(scenario.get(field), field)
        checks = scenario.get("checks")
        if (not isinstance(checks, list) or not checks
                or any(c not in {f"C{i}" for i in range(1, 13)} for c in checks)):
            raise Invalid("scenario requires existing C1-C12 checks")
        tests = scenario.get("tests")
        if not isinstance(tests, list) or any(not isinstance(t, str) or not t.strip() for t in tests):
            raise Invalid("scenario tests must be explicit identifiers")
        if len(tests) != len(set(tests)):
            raise Invalid("duplicate test identifier")
        result[name] = scenario
    return result


def _run(run: object) -> dict[str, str]:
    if not isinstance(run, dict) or type(run.get("exit_code")) is not int:
        raise Invalid("run process exit is missing")
    _hex(run.get("report_sha256"), 64, "report digest")
    cases = run.get("cases")
    if not isinstance(cases, list) or not cases:
        raise Invalid("run decided no test cases")
    result = {}
    for case in cases:
        if not isinstance(case, dict):
            raise Invalid("malformed test case")
        name = _text(case.get("id"), "test id")
        status = case.get("status")
        if name in result or status not in ("passed", "assertion_failed", "error", "skipped", "failed"):
            raise Invalid("duplicate or malformed test outcome")
        result[name] = status
    return result


def assess(contract: dict, envelope: dict, *, key: bytes, contract_digest: str,
           candidate: str, evaluator: str, session: str, environment: str,
           now: datetime | None = None, max_age_hours: int = 30) -> dict:
    """Assess authenticated evidence against a separately pinned contract.

    The controller supplies expected identities; nothing takes them on trust
    from the candidate or from the envelope being graded. This does not merge
    code, authorize production access or replace deployment/branch checks.
    """
    scenarios = contract_cases(contract)
    _hex(contract_digest, 64, "pinned contract digest")
    _hex(candidate, 40, "candidate SHA")
    _hex(evaluator, 40, "evaluator SHA")
    _text(session, "controller session")
    _text(environment, "environment identity")
    if type(max_age_hours) is not int or not 1 <= max_age_hours <= 168:
        raise Invalid("evidence window must be 1-168 whole hours")
    if not isinstance(key, bytes) or len(key) < 32:
        raise Invalid("independent attestation key is unavailable or too short")
    if digest(contract) != contract_digest:
        raise Invalid("acceptance contract changed from the independently pinned version")
    payload = envelope.get("payload")
    signature = envelope.get("hmac_sha256")
    if not isinstance(payload, dict):
        raise Invalid("missing authenticated payload")
    _hex(signature, 64, "attestation signature")
    expected_signature = hmac.new(key, canonical(payload), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise Invalid("untrusted or modified evaluator evidence")
    expected = {"version": 1, "project": contract["project"], "repo": contract["repo"],
                "contract_sha256": contract_digest, "candidate": candidate,
                "evaluator": evaluator, "session": session, "environment": environment}
    if any(type(payload.get(k)) is not type(v) or payload.get(k) != v for k, v in expected.items()):
        raise Invalid("evidence does not match the controller's contract/candidate/run/environment")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise Invalid("controller clock requires timezone")
    start, end = _time(payload.get("started_at")), _time(payload.get("completed_at"))
    if end < start or end > now + timedelta(minutes=5) or start < now - timedelta(hours=max_age_hours):
        raise Invalid("evidence timestamps are stale or inconsistent")
    rows = payload.get("results")
    if not isinstance(rows, list):
        raise Invalid("missing scenario results")
    results = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("id") not in scenarios or row["id"] in results:
            raise Invalid("duplicate or unknown scenario result")
        results[row["id"]] = row
    findings, unavailable = [], []
    verified = 0
    for name, scenario in scenarios.items():
        required = set(scenario["tests"])
        if not required:
            unavailable.append(f"{name}: executable cases not mapped")
            continue
        row = results.get(name)
        if row is None:
            unavailable.append(f"{name}: scenario did not run")
            continue
        try:
            healthy = _run(row.get("healthy"))
            # Preserve product failures even if subsequent negative controls
            # could not run. An infrastructure failure must not erase a bug.
            if row["healthy"]["exit_code"] == 1 and any(v in ("failed", "assertion_failed") for v in healthy.values()):
                findings.append(f"{name}: healthy candidate failed")
            if not required <= healthy.keys():
                raise Invalid("required healthy test identifiers did not all execute")
            if row["healthy"]["exit_code"] != 0:
                if row["healthy"]["exit_code"] != 1 or not any(v in ("failed", "assertion_failed") for v in healthy.values()):
                    unavailable.append(f"{name}: healthy process did not finish cleanly")
                if row.get("broken") is None:
                    unavailable.append(f"{name}: negative control did not run")
                continue
            if any(v != "passed" for v in healthy.values()):
                raise Invalid("healthy run contains skipped, failed or error cases")
            broken = _run(row.get("broken"))
            mutation = row.get("mutation")
            if not isinstance(mutation, dict):
                raise Invalid("missing negative control")
            before = _hex(mutation.get("before_sha256"), 64, "original source digest")
            after = _hex(mutation.get("after_sha256"), 64, "mutated source digest")
            _hex(mutation.get("patch_sha256"), 64, "mutation patch digest")
            if before == after:
                raise Invalid("negative control changed no source")
            _text(mutation.get("mechanism"), "negative control mechanism")
            failures = mutation.get("expected_failures")
            if (not isinstance(failures, list) or not failures
                    or any(not isinstance(t, str) for t in failures)
                    or len(set(failures)) != len(failures) or not set(failures) <= required):
                raise Invalid("negative control has no unambiguous expected assertion")
            if not required <= healthy.keys() or not required <= broken.keys():
                raise Invalid("required test identifiers did not all execute")
            if any(v in ("skipped", "error", "failed") for v in broken.values()):
                raise Invalid("negative control did not produce a clean assertion verdict")
            actual_failures = {t for t, v in broken.items() if v == "assertion_failed"}
            if row["broken"]["exit_code"] == 0 and not actual_failures:
                findings.append(f"{name}: tests survived the negative control")
                continue
            if row["broken"]["exit_code"] != 1 or actual_failures != set(failures):
                raise Invalid("negative control failed for an unexpected reason")
            verified += 1
        except Invalid as exc:
            unavailable.append(f"{name}: {exc}")
    # Findings remain visible when another scenario was unable to run.
    status = "failed" if findings else "unavailable" if unavailable else "qualified"
    return {"status": status, "project": contract["project"], "candidate": candidate,
            "contract_sha256": contract_digest, "scenarios": len(scenarios), "verified": verified,
            "findings": findings, "unavailable": unavailable, "production_authorized": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    for arg in ("contract-digest", "candidate", "evaluator", "session", "environment"):
        parser.add_argument(f"--{arg}", required=True)
    parser.add_argument("--key-env", default="QA_ACCEPTANCE_ATTESTATION_KEY")
    args = vars(parser.parse_args(argv))
    try:
        contract, evidence = read_json(args.pop("contract")), read_json(args.pop("evidence"))
        key = os.environ.get(args.pop("key_env"), "").encode("utf-8")
        result = assess(contract, evidence, key=key, **args)
    except (Invalid, TypeError, RecursionError) as exc:
        # Never print evidence, keys, subprocess logs or credential-bearing paths.
        result = {"status": "unavailable", "reason": str(exc) if isinstance(exc, Invalid) else "malformed evidence"}
    print(json.dumps(result, sort_keys=True))
    return {"qualified": 0, "failed": 1, "unavailable": 3}[result["status"]]


if __name__ == "__main__":
    sys.exit(main())
