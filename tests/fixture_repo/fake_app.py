"""A two-role app the kit's own tests drive. Every defect the bench claims to see
has a switch here (env FAKE_*), so a test can plant the defect and watch the
stage go red — the kit is not believed until it has failed for the right reason.
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

USERS = {"owner@example.test": ("pw-owner-secret-1", "owner"),
         "staff@example.test": ("pw-staff-secret-1", "staff")}
COMMIT = "abc123def456"

#: The declared guard per route — what `collect()` hands the bench.
ADMITS = {
    "/admin": {"owner": True, "staff": True},
    "/admin/owner-only": {"owner": True, "staff": False},
    "/admin/broken": {"owner": True, "staff": True},
    "/admin/wide": {"owner": True, "staff": True},
    "/admin/items/{item_id}": {"owner": True, "staff": True},
    "/admin/export.csv": {"owner": True, "staff": False},
    "/api/items": {"owner": True, "staff": True},
    "/api/secret": {"owner": True, "staff": False},
    "/api/boom": {"owner": True, "staff": True},
}

app = FastAPI()


def _role(request: Request) -> str | None:
    return request.cookies.get("sess") or None


def _page(title: str, extra: str = "") -> HTMLResponse:
    return HTMLResponse(f"<!doctype html><title>{title}</title><main><h1>{title}</h1>{extra}</main>"
                        "<script>document.title += ' ✓';</script>")


@app.get("/health")
def health():
    return {"ok": True, "commit": COMMIT}


@app.get("/login", response_class=HTMLResponse)
def login_form():
    resp = HTMLResponse("<form method=post><input name=email><input name=password type=password><input type=hidden name=_csrf><button type=submit>in</button></form>")
    if os.environ.get("FAKE_CSRF") == "1":
        resp.set_cookie("csrf_token", "csrf-pair-1", path="/")   # the pair a protected form demands back
    return resp


_LOGINS = {"n": 0}


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), csrf: str = Form("", alias="_csrf")):
    _LOGINS["n"] += 1
    if os.environ.get("FAKE_THROTTLE") == "1" and _LOGINS["n"] % 3 == 0:
        return HTMLResponse("<h1>slow down</h1>", status_code=429)     # the app's login throttle
    if os.environ.get("FAKE_CSRF") == "1" and csrf != request.cookies.get("csrf_token"):
        return HTMLResponse("<h1>bad csrf</h1>", status_code=403)   # reads exactly like a wrong password
    u = USERS.get(email.lower())
    if not u or u[0] != password:
        return HTMLResponse("<form>wrong</form>", status_code=401)
    resp = Response(status_code=302, headers={"Location": "/admin"})
    resp.set_cookie("sess", u[1], path="/")
    resp.set_cookie("csrf_token", "csrf-" + u[1], path="/")
    return resp


def _guard(request: Request, path: str):
    role = _role(request)
    if not role:
        return Response(status_code=302, headers={"Location": f"/login?next={path}"})
    admits = ADMITS[path]
    if os.environ.get("FAKE_UNGUARDED") == "1":
        return None                     # the mutation: the guard is gone
    if not admits.get(role):
        return HTMLResponse("<h1>Access denied</h1>", status_code=403)
    return None


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    return _guard(request, "/admin") or _page("Admin")


@app.get("/admin/owner-only", response_class=HTMLResponse)
def owner_only(request: Request):
    return _guard(request, "/admin/owner-only") or _page("Owner only")


@app.get("/admin/broken", response_class=HTMLResponse)
def broken(request: Request):
    g = _guard(request, "/admin/broken")
    if g:
        return g
    js = "<script>throw new Error('boom: the wiring below never runs')</script>" if os.environ.get("FAKE_BROKEN") == "1" else ""
    return _page("Broken?", js)


@app.get("/admin/wide", response_class=HTMLResponse)
def wide(request: Request):
    g = _guard(request, "/admin/wide")
    if g:
        return g
    # 600px: wider than the phone (390) and narrower than the desk (1440), so the
    # defect exists at exactly one of the two viewports — which is what the test
    # asserts, and what a real "fine on the laptop, broken on the phone" looks like.
    block = "<div style='width:600px;height:10px;background:#ccc'></div>" if os.environ.get("FAKE_WIDE") == "1" else ""
    return _page("Wide?", block)


@app.get("/admin/items/{item_id}", response_class=HTMLResponse)
def item(request: Request, item_id: str):
    return _guard(request, "/admin/items/{item_id}") or _page(f"Item {item_id}")


@app.get("/admin/export.csv")
def export_csv(request: Request):
    g = _guard(request, "/admin/export.csv")
    if g:
        return g
    return Response("id,name\n42,a thing\n", media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=export.csv"})


@app.get("/api/items")
def api_items(request: Request):
    return _guard(request, "/api/items") or JSONResponse([{"id": "42", "name": "a thing"}])


@app.get("/api/secret")
def api_secret(request: Request):
    return _guard(request, "/api/secret") or JSONResponse({"secret": "owner-only-data"})


@app.get("/api/boom")
def api_boom(request: Request):
    g = _guard(request, "/api/boom")
    if g:
        return g
    if os.environ.get("FAKE_500") == "1":
        return JSONResponse({"error": "boom"}, status_code=500)
    return JSONResponse({"ok": True})


# ── the providers the manifest names ──────────────────────────────────────────
def collect() -> list[dict]:
    return [{"path": p, "methods": ["GET"], "admits": a} for p, a in ADMITS.items()]


def resolve_ids(owner_client) -> dict[str, str]:
    r = owner_client.get("/api/items")
    rows = r.json() if r.status_code == 200 else []
    return {"item_id": rows[0]["id"]} if rows else {}
