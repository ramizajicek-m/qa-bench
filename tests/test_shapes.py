"""`qabench shapes` against a real Postgres — skipped when none is reachable, and says so.

The picker is judged on the property it exists for: given a table where the
risky shapes exist, it returns a record for each — the null, the longest, every
state, a parent with 0, 1 and the most children — and lists a shape that no row
holds as ABSENT rather than dropping it.
"""
from __future__ import annotations

import os
import uuid

import pytest

from qabench import shapes

DSN = os.environ.get("QABENCH_TEST_DSN", "")
pytestmark = pytest.mark.skipif(not DSN, reason="QABENCH_TEST_DSN not set: no Postgres to pick shapes from (a skip, not a pass)")


@pytest.fixture
def cur():
    conn = shapes._connect(DSN)
    conn.autocommit = True
    c = conn.cursor()
    schema = "qb_" + uuid.uuid4().hex[:8]
    c.execute(f"create schema {schema}; set search_path to {schema}")
    c.execute("create table parent (id serial primary key, name text, status text, note text)")
    c.execute("create table child (id serial primary key, parent int references parent(id))")
    c.execute("""insert into parent (name, status, note) values
                 ('short', 'open', null), ('a much longer real name', 'closed', 'x'), ('mid name', 'open', 'y')""")
    c.execute("insert into child (parent) values (1), (2), (2)")
    yield c
    c.execute(f"drop schema {schema} cascade")
    conn.close()


def test_every_risky_shape_gets_a_real_record(cur):
    picks, absent = shapes.pick(cur, "parent", {"url": "/cards/parent/{id}", "caps": [2, 10]})
    got = {p["shape"]: p["id"] for p in picks}
    assert got["null:note"] == 1
    assert got["longest:name(23)"] == 2
    assert got["state:status=open"] == 1 and got["state:status=closed"] == 2
    assert got["children:child.parent=0"] == 3 and got["children:child.parent=1"] == 1
    assert got["children:child.parent=max(2)"] == 2
    assert got["count>2"] == 3
    assert "parent: count>10 (only 3 rows)" in absent
    assert all(p["url"] == f"/cards/parent/{p['id']}" for p in picks)
