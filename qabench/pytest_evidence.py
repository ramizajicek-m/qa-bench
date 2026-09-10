"""Opt-in pytest evidence metadata; never auto-loaded by the package.

Enable only in a later authorized evaluator run with
``-p qabench.pytest_evidence --junitxml=...``. Pytest's JUnit failure node does
not include the exception type; record that fact without copying traceback or
message text. This is observation metadata, NOT an attestation signature.
"""
import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if call.when == "call":
        # Reserved metadata must not be inherited from a test's record_property.
        item.user_properties[:] = [(name, value) for name, value in item.user_properties
                                   if name != "qabench.failure_kind"]
        kind = "none"
        if report.failed:
            assertion = call.excinfo and call.excinfo.errisinstance(AssertionError)
            if call.excinfo and call.excinfo.errisinstance(pytest.fail.Exception):
                # pytest.raises uses Failed, but so does pytest-timeout. Look
                # at the caller of pytest's outcome helper, never its message.
                # Failed from other plugins/helpers is deliberately unqualified.
                origin = ""
                trace = call.excinfo.value.__traceback__
                while trace is not None:
                    module = trace.tb_frame.f_globals.get("__name__", "")
                    if module != "_pytest.outcomes":
                        origin = module
                    trace = trace.tb_next
                allowed = {"_pytest.raises", "_pytest.python_api"}
                test_module = getattr(getattr(item, "module", None), "__name__", None)
                if test_module:
                    allowed.add(test_module)
                assertion = origin in allowed
            kind = "assertion" if assertion else "other"
        item.user_properties.append(("qabench.failure_kind", kind))
        report.user_properties[:] = item.user_properties
