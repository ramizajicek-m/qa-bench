"""`qabench.readcensus` in a real browser: what a response carried vs what the page read.

Claims, each on a page served by Playwright routing (no app):
  1. a key the page reads is READ; a key it never touches is UNREAD; a key it
     reads that the response does not carry is READ-NOT-SERVED;
  2. the recorder does not change the page: the same object read twice is the
     SAME object (identity), and a proxied object survives history.pushState —
     the two ways its first version broke two of ana-log's browser tests.

Mutation (watched 2026-09-19): the WeakMap cache removed → claim 2's identity
check reads false; the pushState unwrap removed → pushState throws DataCloneError.
"""
from __future__ import annotations

import json

import pytest

pw = pytest.importorskip("playwright.sync_api")

from qabench import readcensus as rc

PAGE = """<!doctype html><script>
window.run = async () => {
  const r = await fetch('/api/thing/7');
  const body = await r.json();
  const a = body.rows[0], b = body.rows[0];
  window.same = a === b;
  window.title = a.title;
  window.missing = body.applied;          // read, never served
  history.pushState({row: a}, '', '/next');
  window.pushed = true;
};
</script>"""


def test_the_census_sees_reads_and_leaves_the_page_alone():
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context()
        sink: dict = {}
        rc.attach(ctx, sink)
        ctx.route("http://qa.test/", lambda r: r.fulfill(body=PAGE, content_type="text/html"))
        ctx.route("http://qa.test/api/thing/7", lambda r: r.fulfill(
            body=json.dumps({"rows": [{"title": "t", "unused": 1}], "total": 1}), content_type="application/json"))
        page = ctx.new_page()
        page.goto("http://qa.test/")
        page.evaluate("window.run()")
        assert page.evaluate("window.same") is True
        assert page.evaluate("window.pushed") is True
        census = rc.collect(page)
        b.close()
    d = rc.diff(census)["GET /api/thing/{id}"]
    assert d["unread"] == ["rows[].unused", "total"]
    assert d["read_not_served"] == ["applied"]
