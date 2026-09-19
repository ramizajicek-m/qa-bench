"""shapes — pick REAL records that have the shapes defects hide in, so a journey visits them.

    python -m qabench shapes --dsn "$DATABASE_URL"            # the `shapes:` block of qa/manifest.yml
    python -m qabench shapes --dsn ... --json > shapes.json   # for the explorer brief or a test

WHY. 13 of the 121 defects people found in ana-log (blind-coded, docs/methodology.md
§9) were a data shape no test visited: the longest real item name that wrapped
a label row through a page break; a stored pallet with no order, whose label
fell back to the warehouse's own address (2,213 of 2,422 such pallets); a drive
with no driver; an account with no groups; one row where the copy said «1
שורות»; the 61st pallet on a screen that fetched 60; the 51st document in a list
capped at 50. Every one existed in the real data. Fixtures written by the
author held none of them — `'א' * n` for a name, a warehouse with a city and no
street — and agreed with the code by construction.

So this does not generate data. It ASKS the real database, per table the
manifest names, for one record of each shape:

  null:<col>        a row where a nullable column is empty (and one where it is not)
  longest:<col>     the row with the longest value in a text column
  state:<col>=<v>   one row per value of a low-cardinality column (a status)
  children:<fk>=0|1|max   a parent with no, one, and the most children
  count>cap         when a table holds more rows than a declared page/list cap

and prints the URL a person would open for it. What it cannot pick — a state the
column's type or check constraint allows and no row holds — it lists as ABSENT:
those are the shapes a test has to manufacture (ana-log's unwalked states).

It is a supplier of subjects, not an oracle: something must still look at the
record — the explorer (the list goes into its brief), the layout probe, a person.

Manifest:

    shapes:
      dsn_env: DATABASE_URL
      tables:
        pallets_storage: {url: "/cards/pallets/{id}"}
        orders:          {url: "/cards/orders/{id}", caps: [60]}
      max_states: 12            # a column with more distinct values is not a status
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml


def _connect(dsn: str):
    try:
        import psycopg  # type: ignore
        return psycopg.connect(dsn)
    except ImportError:
        import psycopg2  # type: ignore
        return psycopg2.connect(dsn)


def _ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _q(cur, sql: str, args=()):
    cur.execute(sql, args)
    return cur.fetchall()


def columns(cur, table: str) -> list[tuple[str, str, bool]]:
    rows = _q(cur, """select column_name, data_type, is_nullable = 'YES'
                      from information_schema.columns
                      where table_schema = current_schema() and table_name = %s order by ordinal_position""", (table,))
    return [(r[0], r[1], bool(r[2])) for r in rows]


def child_fks(cur, table: str) -> list[tuple[str, str]]:
    """[(child_table, child_column)] for every FK pointing at `table`."""
    rows = _q(cur, """select kcu.table_name, kcu.column_name
                      from information_schema.referential_constraints rc
                      join information_schema.key_column_usage kcu on kcu.constraint_name = rc.constraint_name
                      join information_schema.constraint_column_usage ccu on ccu.constraint_name = rc.unique_constraint_name
                      where ccu.table_name = %s and kcu.table_schema = current_schema()""", (table,))
    return [(r[0], r[1]) for r in rows]


def pick(cur, table: str, spec: dict, max_states: int = 12) -> tuple[list[dict], list[str]]:
    t = _ident(table)
    url = spec.get("url", "")
    picks: list[dict] = []
    absent: list[str] = []

    def add(shape: str, rid) -> None:
        if rid is not None:
            picks.append({"table": table, "shape": shape, "id": rid, "url": url.replace("{id}", str(rid)) if url else ""})

    total = _q(cur, f"select count(*) from {t}")[0][0]
    for cap in spec.get("caps") or []:
        if total > cap:
            add(f"count>{cap}", _q(cur, f"select id from {t} order by id offset %s limit 1", (cap,))[0][0])
        else:
            absent.append(f"{table}: count>{cap} (only {total} rows)")
    for col, dtype, nullable in columns(cur, table):
        c = _ident(col)
        if col == "id":
            continue
        if nullable:
            r = _q(cur, f"select id from {t} where {c} is null order by id limit 1")
            add(f"null:{col}", r[0][0] if r else None)
            if not r:
                absent.append(f"{table}: null:{col}")
        if dtype in ("text", "character varying", "character"):
            r = _q(cur, f"select id, length({c}) from {t} where {c} is not null order by length({c}) desc, id limit 1")
            if r:
                add(f"longest:{col}({r[0][1]})", r[0][0])
            distinct = _q(cur, f"select count(distinct {c}) from {t}")[0][0]
            if 1 < distinct <= max_states:
                for (v,) in _q(cur, f"select distinct {c} from {t} where {c} is not null order by 1"):
                    rr = _q(cur, f"select id from {t} where {c} = %s order by id limit 1", (v,))
                    add(f"state:{col}={v}", rr[0][0] if rr else None)
    for child, fk in child_fks(cur, table):
        ct, cc = _ident(child), _ident(fk)
        counts = _q(cur, f"""select p.id, count(c.{cc}) n from {t} p left join {ct} c on c.{cc} = p.id
                             group by p.id order by n, p.id""")
        by_n: dict[int, int] = {}
        for pid, n in counts:
            by_n.setdefault(n, pid)
        for label, n in (("0", 0), ("1", 1)):
            if n in by_n:
                add(f"children:{child}.{fk}={label}", by_n[n])
            else:
                absent.append(f"{table}: children:{child}.{fk}={label}")
        if counts:
            add(f"children:{child}.{fk}=max({counts[-1][1]})", counts[-1][0])
    return picks, absent


def run(argv: list[str]) -> int:
    root = Path(argv[argv.index("--repo") + 1] if "--repo" in argv else ".").resolve()
    mpath = root / "qa" / "manifest.yml"
    doc = (yaml.safe_load(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}) or {}
    cfg = doc.get("shapes")
    if not cfg or not cfg.get("tables"):
        print(f"no `shapes:` block with tables in {mpath} — nothing picked (exit 3)", file=sys.stderr)
        return 3
    dsn = argv[argv.index("--dsn") + 1] if "--dsn" in argv else os.environ.get(cfg.get("dsn_env", "DATABASE_URL"), "")
    if not dsn:
        print("no database to ask (--dsn or the manifest's dsn_env) — exit 3", file=sys.stderr)
        return 3
    picks, absent = [], []
    with _connect(dsn) as conn:
        cur = conn.cursor()
        for table, spec in cfg["tables"].items():
            p, a = pick(cur, table, spec or {}, int(cfg.get("max_states", 12)))
            picks += p
            absent += a
    if "--json" in argv:
        print(json.dumps({"picks": picks, "absent": absent}, indent=1, ensure_ascii=False, default=str))
    else:
        print(f"SHAPES — {len(picks)} real records to visit across {len(cfg['tables'])} tables; {len(absent)} shapes absent")
        for p in picks:
            print(f"  {p['table']:20} {p['shape']:44} id={p['id']}  {p['url']}")
        for a in absent:
            print(f"  ABSENT {a} — no row holds it; a test must manufacture it")
    return 0 if picks else 3
