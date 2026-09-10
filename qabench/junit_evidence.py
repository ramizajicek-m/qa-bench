"""Normalize an existing JUnit report without importing or running the app.

The controller records the process exit separately: XML alone cannot see
failed collection, interrupted teardown or a killed process. This parser does
not sign results; signing belongs outside the candidate's process/credentials.
"""
from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

from .acceptance import Invalid


def read_report(path: Path, *, exit_code: int) -> dict:
    if type(exit_code) is not int:
        raise Invalid("process exit code must be independently recorded")
    try:
        if path.stat().st_size > 32_000_000:
            raise Invalid("JUnit report exceeds size limit")
        raw = path.read_bytes()
        xml = raw.decode("utf-8-sig")
        if "\x00" in xml or "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
            raise Invalid("JUnit DTDs/entities are not accepted")
        root = ET.fromstring(xml)
    except (OSError, UnicodeError, ET.ParseError) as exc:
        raise Invalid("JUnit report is unavailable or malformed") from exc
    if root.tag not in ("testsuite", "testsuites"):
        raise Invalid("unsupported JUnit root")
    cases, names = [], set()
    for case in root.iter("testcase"):
        # Dialects with status/result flags need a dedicated adapter: absence
        # of a failure child alone cannot establish execution in those formats.
        if "status" in case.attrib or "result" in case.attrib:
            raise Invalid("unsupported JUnit execution-status attributes")
        classname, name = case.get("classname"), case.get("name")
        if not classname or not name:
            raise Invalid("JUnit testcase has no exact classname/name identity")
        identity = f"{classname}::{name}"
        if identity in names:
            raise Invalid("duplicate JUnit testcase identity")
        names.add(identity)
        outcomes = [child for child in case if child.tag in ("failure", "error", "skipped")]
        if len(outcomes) > 1:
            raise Invalid("ambiguous JUnit testcase outcome")
        status = "passed"
        if outcomes:
            outcome = outcomes[0]
            if outcome.tag == "failure":
                failure_type = outcome.get("type", "")
                kinds = [p.get("value") for p in case.findall("./properties/property")
                         if p.get("name") == "qabench.failure_kind"]
                if len(kinds) > 1:
                    raise Invalid("duplicate failure-kind observation")
                # Generic failures and timeouts cannot prove that the intended
                # assertion detected the mutation. Do not parse message prose.
                assertion = (failure_type in ("AssertionError", "builtins.AssertionError")
                             or (not failure_type and kinds == ["assertion"]))
                status = "assertion_failed" if assertion else "failed"
            else:
                status = outcome.tag
        cases.append({"id": identity, "status": status})
    if not cases:
        raise Invalid("JUnit report decided no testcases")
    # Check every suite, including an outer aggregate, against its actual
    # descendants. Contradictory declarations and truncated XML are not green.
    for suite in root.iter():
        if suite.tag not in ("testsuite", "testsuites"):
            continue
        descendants = list(suite.iter("testcase"))
        actual = {"tests": len(descendants),
                  "failures": sum(c.find("failure") is not None for c in descendants),
                  "errors": sum(c.find("error") is not None for c in descendants),
                  "skipped": sum(c.find("skipped") is not None for c in descendants)}
        for field, count in actual.items():
            value = suite.get(field)
            if value is not None and (not value.isdecimal() or int(value) != count):
                raise Invalid("JUnit declared counts disagree with testcases")
    return {"exit_code": exit_code, "report_sha256": hashlib.sha256(raw).hexdigest(), "cases": cases}
