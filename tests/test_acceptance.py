"""C8: approval must depend on the named behavior, build and negative control.

Synthetic controller envelopes exercise the evidence protocol only. They are
not product coverage or a claim that an independent attester is deployed.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import hmac

import pytest

from qabench.acceptance import Invalid, assess, canonical, digest, read_json

NOW = datetime(2026, 9, 9, 18, tzinfo=timezone.utc)
KEY = b"synthetic-test-key-not-a-real-secret" * 2
CASE = "tests.approval::test_actual_gesture[suppress]"


@pytest.fixture
def inputs():
    contract = {"version": 1, "project": "sample", "repo": "example/sample",
                "requirement_source": "test protocol fixture",
                "scenarios": [{"id": "approval", "checks": ["C9", "C10"],
                    "requirement": "Suppress approves without sending",
                    "root_cause": "source checks missed a no-op handler",
                    "sibling_scope": "every approval caller", "expected_outcome": "stored approval and no outbox entry",
                    "tests": [CASE]}]}
    payload = {"version": 1, "project": "sample", "repo": "example/sample",
               "contract_sha256": digest(contract), "candidate": "a" * 40,
               "evaluator": "b" * 40, "session": "controller-attempt-2", "environment": "disposable-db-2",
               "started_at": "2026-09-09T17:00:00Z", "completed_at": "2026-09-09T17:30:00Z",
               "results": [{"id": "approval",
                   "healthy": {"exit_code": 0, "report_sha256": "1" * 64,
                               "cases": [{"id": CASE, "status": "passed"}]},
                   "broken": {"exit_code": 1, "report_sha256": "2" * 64,
                              "cases": [{"id": CASE, "status": "assertion_failed"}]},
                   "mutation": {"before_sha256": "3" * 64, "after_sha256": "4" * 64,
                                "patch_sha256": "5" * 64, "mechanism": "return before approval request",
                                "expected_failures": [CASE]}}]}
    options = dict(key=KEY, contract_digest=digest(contract), candidate="a" * 40,
                   evaluator="b" * 40, session="controller-attempt-2", environment="disposable-db-2", now=NOW)
    return contract, payload, options


def signed(payload):
    return {"payload": payload, "hmac_sha256": hmac.new(KEY, canonical(payload), hashlib.sha256).hexdigest()}


def evaluate(inputs):
    contract, payload, options = inputs
    return assess(contract, signed(payload), **options)


def test_healthy_and_discriminating_failure_qualify_without_authorizing_production(inputs):
    result = evaluate(inputs)
    assert result["status"] == "qualified"
    assert result["scenarios"] == result["verified"] == 1
    assert result["production_authorized"] is False


@pytest.mark.parametrize("field,value", [("candidate", "c" * 40), ("evaluator", "c" * 40),
    ("session", "older-attempt"), ("environment", "another-database"), ("repo", "other/sample"),
    ("version", True), ("contract_sha256", "c" * 64)])
def test_even_authentic_evidence_requires_controller_identities(inputs, field, value):
    inputs[1][field] = value
    with pytest.raises(Invalid, match="controller"):
        evaluate(inputs)


def test_builder_cannot_weaken_the_pinned_contract(inputs):
    inputs[0]["scenarios"][0]["expected_outcome"] = "success toast is enough"
    with pytest.raises(Invalid, match="contract changed"):
        evaluate(inputs)


def test_results_cannot_be_modified_after_attestation(inputs):
    contract, payload, options = inputs
    envelope = signed(payload)
    payload["results"][0]["healthy"]["cases"][0]["status"] = "skipped"
    with pytest.raises(Invalid, match="untrusted"):
        assess(contract, envelope, **options)


@pytest.mark.parametrize("status", ["skipped", "error", "failed", "assertion_failed"])
def test_passing_process_cannot_hide_nonpassing_healthy_case(inputs, status):
    inputs[1]["results"][0]["healthy"]["cases"][0]["status"] = status
    assert evaluate(inputs)["status"] == "unavailable"


def test_green_xml_with_failed_teardown_is_not_a_pass(inputs):
    inputs[1]["results"][0]["healthy"]["exit_code"] = 1
    assert evaluate(inputs)["status"] == "unavailable"


def test_actual_healthy_failure_is_a_finding(inputs):
    healthy = inputs[1]["results"][0]["healthy"]
    healthy.update(exit_code=1, cases=[{"id": CASE, "status": "assertion_failed"}])
    result = evaluate(inputs)
    assert result["status"] == "failed" and result["findings"]


def test_missing_negative_control_cannot_erase_observed_product_failure(inputs):
    row = inputs[1]["results"][0]
    row["healthy"].update(exit_code=1, cases=[{"id": CASE, "status": "assertion_failed"}])
    row.pop("broken")
    result = evaluate(inputs)
    assert result["status"] == "failed" and result["findings"] and result["unavailable"]


def test_surviving_mutation_is_a_finding(inputs):
    broken = inputs[1]["results"][0]["broken"]
    broken.update(exit_code=0, cases=[{"id": CASE, "status": "passed"}])
    assert evaluate(inputs)["status"] == "failed"


def test_noop_anchor_is_unavailable_not_surviving_product_defect(inputs):
    mutation = inputs[1]["results"][0]["mutation"]
    mutation["after_sha256"] = mutation["before_sha256"]
    result = evaluate(inputs)
    assert result["status"] == "unavailable" and not result["findings"]


@pytest.mark.parametrize("status,exit_code", [("error", 1), ("assertion_failed", 2), ("skipped", 0)])
def test_harness_error_or_collection_failure_cannot_kill_mutation(inputs, status, exit_code):
    broken = inputs[1]["results"][0]["broken"]
    broken.update(exit_code=exit_code, cases=[{"id": CASE, "status": status}])
    assert evaluate(inputs)["status"] == "unavailable"


def test_failure_of_another_assertion_is_not_the_required_negative_control(inputs):
    inputs[1]["results"][0]["broken"]["cases"].append({"id": "unrelated", "status": "assertion_failed"})
    assert evaluate(inputs)["status"] == "unavailable"


def test_required_case_missing_or_duplicated_cannot_qualify(inputs):
    cases = inputs[1]["results"][0]["healthy"]["cases"]
    cases[0]["id"] = "a-different-valid-test"
    assert evaluate(inputs)["status"] == "unavailable"
    cases[0]["id"] = CASE
    cases.append(deepcopy(cases[0]))
    assert evaluate(inputs)["status"] == "unavailable"


def test_added_scenario_without_execution_cannot_disappear(inputs):
    contract, payload, options = inputs
    scenario = deepcopy(contract["scenarios"][0])
    scenario["id"] = "new-approval-caller"
    contract["scenarios"].append(scenario)
    options["contract_digest"] = payload["contract_sha256"] = digest(contract)
    result = evaluate(inputs)
    assert result["status"] == "unavailable" and result["scenarios"] == 2 and result["verified"] == 1


@pytest.mark.parametrize("start,end", [("2026-09-01T17:00:00Z", "2026-09-09T17:30:00Z"),
    ("2026-09-09T17:00:00Z", "2026-09-09T19:00:00Z"),
    ("2026-09-09T17:00:00", "2026-09-09T17:30:00Z"),
    ("2026-09-09T17:00:00Z", "2026-09-09T16:00:00Z")])
def test_stale_future_or_ambiguous_clock_evidence_is_unavailable(inputs, start, end):
    inputs[1].update(started_at=start, completed_at=end)
    with pytest.raises(Invalid):
        evaluate(inputs)


def test_duplicate_keys_are_not_last_writer_wins(tmp_path):
    path = tmp_path / "evidence.json"
    path.write_text('{"exit_code": 1, "exit_code": 0}')
    with pytest.raises(Invalid):
        read_json(path)


@pytest.mark.parametrize("number", ["1e400", "NaN", "Infinity", "-Infinity"])
def test_nonfinite_json_is_unavailable(tmp_path, number):
    path = tmp_path / "evidence.json"
    path.write_text('{"amount":' + number + '}')
    with pytest.raises(Invalid):
        read_json(path)
