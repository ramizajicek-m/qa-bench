"""pytest plugin: run a project's EXISTING browser tier with the read census attached.

    QA_READ_CENSUS=/tmp/census.json pytest -p qabench.readcensus_pytest tests/e2e

No change to the project's tests or conftest: every Playwright BrowserContext the
suite opens gets the recorder (qabench.readcensus), and at the end of the session
the merged census and its diff are written to the path in QA_READ_CENSUS.

Why ride the existing tier rather than crawl: a crawler that only opens screens
reports every key read by a branch it never ran — on ana-log's 119 endpoints a
passive crawl left 1,493 served keys "unread", most of them validation rules
read on submit and filters read when a filter is opened. The suite already
presses those buttons. What stays unread after the whole tier is either data
nothing uses or behaviour no test drives — both are findings.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from . import readcensus

_SINK: dict = {}
_PATCHED = False


def pytest_configure(config):
    global _PATCHED
    if not os.environ.get("QA_READ_CENSUS") or _PATCHED:
        return
    from playwright.sync_api._generated import Browser

    original = Browser.new_context

    def new_context(self, *args, **kwargs):
        ctx = original(self, *args, **kwargs)
        try:
            readcensus.attach(ctx, _SINK)
        except Exception as e:  # noqa: BLE001 — a census that cannot attach must say so, not break the suite
            print(f"[read census] could not attach: {e}")
        return ctx

    Browser.new_context = new_context
    _PATCHED = True


def pytest_sessionfinish(session, exitstatus):
    out = os.environ.get("QA_READ_CENSUS")
    if not out:
        return
    diff = readcensus.diff(_SINK)
    Path(out).write_text(json.dumps({"summary": readcensus.summary(diff), "diff": diff, "census": _SINK},
                                    indent=1, ensure_ascii=False))
    s = readcensus.summary(diff)
    print(f"\n[read census] {s['endpoints']} endpoints, {s['served_leaves']} served leaves, "
          f"{s['unread']} never read, {s['read_not_served']} read and never served → {out}")
