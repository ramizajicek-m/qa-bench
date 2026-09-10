"""Protocol fixtures and actual pytest outcome calibration; no product coverage."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

from qabench.acceptance import Invalid
from qabench.junit_evidence import read_report


def report(tmp_path, content, exit_code=0):
    path = tmp_path / "junit.xml"
    path.write_text(content)
    return read_report(path, exit_code=exit_code)


def test_normalizes_exact_parameter_identity_and_preserves_process_exit(tmp_path):
    result = report(tmp_path, '<testsuite tests="1"><testcase classname="tests.approval" name="test_choice[suppress]"/></testsuite>', 1)
    assert result["cases"] == [{"id": "tests.approval::test_choice[suppress]", "status": "passed"}]
    assert result["exit_code"] == 1
    assert len(result["report_sha256"]) == 64


@pytest.mark.parametrize("body,status", [('<failure type="AssertionError"/>', "assertion_failed"),
    ('<failure type="TimeoutError"/>', "failed"), ('<error/>', "error"), ('<skipped/>', "skipped")])
def test_only_assertion_failure_is_negative_control_evidence(tmp_path, body, status):
    result = report(tmp_path, f'<testsuite><testcase classname="test" name="x">{body}</testcase></testsuite>', 1)
    assert result["cases"][0]["status"] == status


def test_pytest_property_supplies_type_missing_from_standard_failure_node(tmp_path):
    xml = ('<testsuite><testcase classname="test" name="x"><properties>'
           '<property name="qabench.failure_kind" value="assertion"/>'
           '</properties><failure message="not inspected"/></testcase></testsuite>')
    assert report(tmp_path, xml, 1)["cases"][0]["status"] == "assertion_failed"


@pytest.mark.parametrize("xml", [
    '<testsuite tests="2"><testcase classname="test" name="x"/></testsuite>',
    '<testsuite><testcase classname="test" name="x"/><testcase classname="test" name="x"/></testsuite>',
    '<testsuite tests="0"/>',
    '<testsuite><testcase name="x"/></testsuite>',
    '<testsuite><testcase classname="test" name="x" status="notrun" result="suppressed"/></testsuite>',
    '<testsuite><testcase classname="test" name="x"><failure/><skipped/></testcase></testsuite>',
    '<!DOCTYPE testsuite [<!ENTITY x "expansion">]><testsuite/>',
    '<testsuite><testcase',
])
def test_missing_ambiguous_or_truncated_evidence_is_unavailable(tmp_path, xml):
    with pytest.raises(Invalid):
        report(tmp_path, xml)


def test_utf16_entities_cannot_bypass_the_dtd_prohibition(tmp_path):
    path = tmp_path / "junit.xml"
    path.write_bytes(('<?xml version="1.0" encoding="UTF-16"?>'
                      '<!DOCTYPE testsuite [<!ENTITY x "expanded">]>'
                      '<testsuite><testcase classname="test" name="&x;"/></testsuite>').encode("utf-16"))
    with pytest.raises(Invalid):
        read_report(path, exit_code=0)


def test_real_pytest_assertions_are_distinct_from_setup_crash_and_skip(tmp_path):
    """A missing expected refusal uses pytest's Failed, not AssertionError.

    Real pytest writes the XML. Removing Failed from the plugin's recognized
    assertion types must change only the missing-raise/explicit-fail verdicts.
    """
    subject = tmp_path / "test_subject.py"
    subject.write_text('''import time
import pytest

def test_assert():
    assert False

def test_missing_raise():
    with pytest.raises(ValueError):
        pass

def test_explicit_fail():
    pytest.fail("expected refusal was absent")

def test_crash():
    raise RuntimeError("application failure")

def test_timeout():
    raise TimeoutError("timing is not assertion proof")

@pytest.mark.timeout(0.05, method="signal")
def test_plugin_timeout():
    time.sleep(2)

def test_pass():
    pass

def test_skip():
    pytest.skip("not executed")

def test_xfail():
    pytest.xfail("not qualified")

@pytest.fixture
def setup_failure():
    pytest.fail("fixture could not start")

def test_setup(setup_failure):
    pass
''')
    xml = tmp_path / "actual.xml"
    env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
           "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    env.pop("PYTEST_ADDOPTS", None)
    result = subprocess.run([sys.executable, "-m", "pytest", "-c", os.devnull,
                             "--rootdir=" + str(tmp_path),
                             "-p", "qabench.pytest_evidence", "-p", "pytest_timeout", "-q", str(subject),
                             "--junitxml=" + str(xml)], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 1, result.stdout + result.stderr
    normalized = read_report(xml, exit_code=result.returncode)
    assert normalized["cases"] == [
        {"id": "test_subject::test_assert", "status": "assertion_failed"},
        {"id": "test_subject::test_missing_raise", "status": "assertion_failed"},
        {"id": "test_subject::test_explicit_fail", "status": "assertion_failed"},
        {"id": "test_subject::test_crash", "status": "failed"},
        {"id": "test_subject::test_timeout", "status": "failed"},
        {"id": "test_subject::test_plugin_timeout", "status": "failed"},
        {"id": "test_subject::test_pass", "status": "passed"},
        {"id": "test_subject::test_skip", "status": "skipped"},
        {"id": "test_subject::test_xfail", "status": "skipped"},
        {"id": "test_subject::test_setup", "status": "error"},
    ]
