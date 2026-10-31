"""The recorder patches the client the suite actually sends through, and a
recording that shrinks below its floor is refused rather than written."""
from __future__ import annotations

import json
import sys
import types

import pytest

from qabench import hits


@pytest.fixture
def fresh(monkeypatch):
    hits._seen.clear()
    monkeypatch.setattr(hits, "_installed", False)
    monkeypatch.delenv(hits.FLOOR_ENV, raising=False)
    monkeypatch.delenv(hits.ALLOW_SHRINK_ENV, raising=False)
    yield
    hits._seen.clear()


def _fake_client_module(name):
    """A stand-in for httpx2: a module with its own Client and AsyncClient."""
    class Response:
        status_code = 200
        headers = {}

    class URL:
        def __init__(self, path):
            self.path, self.host = path, "testserver"

    class Request:
        def __init__(self, method, path):
            self.method, self.url, self.content = method, URL(path), b""

    class Client:
        def send(self, request, *a, **kw):
            return Response()

    class AsyncClient:
        async def send(self, request, *a, **kw):
            return Response()

    mod = types.ModuleType(name)
    mod.Client, mod.AsyncClient, mod.Request = Client, AsyncClient, Request
    return mod


def test_a_second_client_module_is_patched_too(fresh, monkeypatch):
    """THE ESCAPE. Starlette 1.x's TestClient is built on httpx2, not httpx.

    Patching httpx alone, a fresh unit recording held about 60 rows where the
    suite makes about 1,290, and nothing failed.

    Mutation: patch only `httpx` and this request is never recorded.
    """
    mod = _fake_client_module("httpx2")
    monkeypatch.setitem(sys.modules, "httpx2", mod)
    assert hits.install()
    mod.Client().send(mod.Request("POST", "/admin/x/1/delete"))
    assert any(r.startswith("POST /admin/x/1/delete 200") for r in hits._seen)


def test_the_module_testclient_bound_is_patched_whatever_its_name(fresh, monkeypatch):
    """A future rename must not repeat the escape: whatever starlette.testclient
    imported as `httpx` is patched, not only the names listed in the kit.

    Mutation: drop `_testclient_module` from `client_modules` and this goes red.
    """
    mod = _fake_client_module("httpx_next")
    monkeypatch.setattr(hits, "_testclient_module", lambda: mod)
    assert mod in hits.client_modules()
    assert hits.install()
    mod.Client().send(mod.Request("GET", "/x"))
    assert any(r.startswith("GET /x 200") for r in hits._seen)


def test_a_real_starlette_testclient_request_is_recorded(fresh):
    """The proof on the real thing, where starlette is installed."""
    tc = pytest.importorskip("starlette.testclient")
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    app = Starlette(routes=[Route("/ping", lambda r: PlainTextResponse("ok"),
                                  methods=["POST"])])
    assert hits.install()
    tc.TestClient(app).post("/ping")
    assert any(r.startswith("POST /ping 200") for r in hits._seen), (
        f"TestClient sends through {tc.httpx.__name__}; the recorder missed it")


def test_installing_twice_never_records_a_request_twice_over(fresh, monkeypatch):
    """`send` is wrapped once per class, so tests that reinstall stay honest."""
    mod = _fake_client_module("httpx2")
    monkeypatch.setitem(sys.modules, "httpx2", mod)
    hits.install()
    once = mod.Client.send
    monkeypatch.setattr(hits, "_installed", False)
    hits.install()
    assert mod.Client.send is once


def _committed(path, n):
    rows = [f"GET /r{i} 200\t\t" for i in range(n)]
    path.write_text(json.dumps({"format": hits.FORMAT, "recorded": rows,
                                "count": n}), encoding="utf-8")


def test_a_recording_that_shrank_is_refused_and_the_old_one_kept(fresh, tmp_path):
    """The floor that would have made the httpx2 escape loud: 1,290 to 60.

    Mutation: remove `check_floor` from `write` and the 60-row file replaces it.
    """
    target = tmp_path / "unit.json"
    _committed(target, 1290)
    for i in range(60):
        hits.record("GET", f"/r{i}", 200)
    with pytest.raises(hits.ShrinkRefused, match="below the floor of 645"):
        hits.write(target)
    assert json.loads(target.read_text())["count"] == 1290


def test_a_recording_within_the_floor_is_written(fresh, tmp_path):
    target = tmp_path / "unit.json"
    _committed(target, 100)
    for i in range(50):
        hits.record("GET", f"/r{i}", 200)
    assert hits.write(target)["count"] == 50


def test_a_first_recording_has_no_floor(fresh, tmp_path):
    hits.record("GET", "/only", 200)
    assert hits.write(tmp_path / "unit.json")["count"] == 1


def test_an_absolute_floor_applies_with_no_previous_file(fresh, tmp_path, monkeypatch):
    monkeypatch.setenv(hits.FLOOR_ENV, "10")
    hits.record("GET", "/only", 200)
    with pytest.raises(hits.ShrinkRefused, match=hits.FLOOR_ENV):
        hits.write(tmp_path / "unit.json")


def test_a_deliberate_drop_is_accepted_by_name(fresh, tmp_path, monkeypatch):
    target = tmp_path / "unit.json"
    _committed(target, 1290)
    monkeypatch.setenv(hits.ALLOW_SHRINK_ENV, "1")
    hits.record("GET", "/only", 200)
    assert hits.write(target)["count"] == 1


def test_merging_workers_applies_the_floor(fresh, tmp_path):
    """Under xdist the per-worker files have no history; the merge is where the
    floor bites. Mutation: remove `check_floor` from `merge_workers`."""
    target = tmp_path / "unit.json"
    _committed(target, 1290)
    (tmp_path / "unit.gw0.json").write_text(json.dumps(
        {"recorded": ["GET /a 200\t\t"]}), encoding="utf-8")
    with pytest.raises(hits.ShrinkRefused):
        hits.merge_workers(str(target))
    assert (tmp_path / "unit.gw0.json").exists(), "a refused merge deletes nothing"


def test_folding_raw_lines_applies_the_floor(fresh, tmp_path):
    """Mutation: remove `check_floor` from `fold_raw`."""
    target = tmp_path / "browser.json"
    _committed(target, 400)
    (tmp_path / "a.raw").write_text("GET /a 200\t\t\n", encoding="utf-8")
    with pytest.raises(hits.ShrinkRefused):
        hits.fold_raw(str(target))
