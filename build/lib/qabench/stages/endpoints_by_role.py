"""endpoints_by_role — every GET API route, as every role: the surface behind the pages.

READ-ONLY BY CONSTRUCTION: GET only. Asserts, in descending order of harm:
  1. a portal (customer) role never passes auth on a staff endpoint;
  2. the declared gate is the real gate — where the route provider says who is
     admitted, the live answer agrees;
  3. nothing 500s for anybody.
Streams and by-design-open paths are named in the manifest, not silently skipped.
"""
from __future__ import annotations

from .. import core
from ..manifest import Bench


def _api_routes(cfg: Bench, rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        path = row["path"]
        if "GET" not in row.get("methods", ["GET"]):
            continue
        if not any(path.startswith(p) for p in cfg.api.include_prefixes):
            continue
        if path in cfg.api.exclude_paths:
            continue
        out.append(row)
    return sorted(out, key=lambda r: r["path"])


def main(cfg: Bench, argv: list[str]) -> int:
    if not cfg.routes:
        raise SystemExit("bench.routes is unset — name the provider that lists this project's routes")
    core.refuse_prod(cfg, "endpoints_by_role drives every GET API route as every role")
    L = core.Ledger("endpoints_by_role", cfg.shots, cfg.origin)
    core.banner(f"GET API routes × roles on {cfg.origin}")
    rows = _api_routes(cfg, list(cfg.provider(cfg.routes)()))
    if not rows:
        L.skip("api routes", "the provider yields no GET route under api.include_prefixes — nothing to probe here")
        L.write()
        return L.exit_code()
    ids: dict = {}
    if cfg.ids:
        try:
            with core.login(cfg, cfg.roles[0]).client() as h:
                ids = dict(cfg.provider(cfg.ids)(h) or {})
        except SystemExit as ex:
            L.skip("resolve path ids", str(ex)[:160])
    exposure, contradiction, errors = [], [], []
    probed = decidable = no_id = 0
    for role in cfg.roles:
        try:
            sess = core.login(cfg, role)
        except SystemExit as ex:
            L.skip(f"{role}: no session", str(ex)[:160])
            continue
        with sess.client() as h:
            for row in rows:
                path = core.fill(row["path"], ids)
                if path is None:
                    no_id += 1
                    continue
                try:
                    r = h.get(path)
                except Exception as ex:  # noqa: BLE001
                    errors.append(f"{role} GET {row['path']}: request failed {type(ex).__name__}")
                    continue
                probed += 1
                st = r.status_code
                if st >= 500:
                    errors.append(f"{role} GET {row['path']} -> {st}")
                is_portal_path = row["path"].startswith(tuple(cfg.api.portal_prefixes) + tuple(cfg.api.open_prefixes)) if (cfg.api.portal_prefixes or cfg.api.open_prefixes) else False
                if role in cfg.api.portal_roles and not is_portal_path and 200 <= st < 300:
                    exposure.append(f"{role} GET {row['path']} -> {st}")
                a = row.get("admits")
                if isinstance(a, (dict, list, tuple, set)):
                    decidable += 1
                    permitted = bool(a.get(role)) if isinstance(a, dict) else role in a
                    refused = st in (401, 403)
                    if permitted and refused:
                        contradiction.append(f"{role} GET {row['path']} -> {st} but the guard admits this role")
                    elif not permitted and 200 <= st < 300:
                        contradiction.append(f"{role} GET {row['path']} -> {st} though the guard does not admit this role")
    if cfg.api.portal_roles:
        L.check(f"no customer role passes auth on a staff endpoint ({probed} probes)", not exposure, "; ".join(exposure[:6]), "; ".join(exposure))
    L.check(f"the declared gate is the real gate ({decidable} decidable pairs)", not contradiction, "; ".join(contradiction[:6]), "; ".join(contradiction))
    L.check(f"nothing 500s for any role ({probed} probes)", not errors, "; ".join(errors[:6]), "; ".join(errors))
    if no_id:
        L.skip(f"{no_id} route×role pairs", "no id for a path parameter (bench.ids)")
    L.extra.update(probed=probed, decidable=decidable)
    print(f"\n  DECIDED: {probed} probes across {len(cfg.roles)} role(s); {decidable} had a declared guard to compare against; {no_id} skipped for want of an id", flush=True)
    L.write()
    return L.exit_code()
