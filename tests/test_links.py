"""The navigation population — the one the control register never had.

`qabench.gestures` reads an `<a>` only when it carries `data-action` or
`onclick`; it never looks at `href`. So every menu, sidebar, breadcrumb, card and
tab link was outside the population, and the estate was reporting "no
non-functional buttons" with the menus unexamined.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qabench.links import Link, lift_links, normalise, orphans, route_key, unresolved


def write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def test_internal_links_are_lifted_and_external_ones_are_not(tmp_path):
    """A population that swept up mailto: and https:// would drown the finding."""
    write(tmp_path, "nav.html", """
      <a href="/admin/clients">Clients</a>
      <a href="/admin/clients/{{ c.id }}/edit">Edit</a>
      <a href="https://example.com/docs">Docs</a>
      <a href="mailto:a@b.com">Mail</a>
      <a href="tel:+972">Call</a>
      <a href="//cdn.example.com/x">Protocol relative</a>
      <a href="#overview">Tab</a>
      <a href="javascript:void(0)">Fake</a>
      <a>No href</a>
    """)
    # A SET, because the register sorts by id and "/" sorts before "]" — so the
    # dynamic link precedes its parent. Deterministic, just not document order,
    # and asserting the order here would pin an incidental fact.
    assert {link.href for link in lift_links(tmp_path)} == {
        "/admin/clients", "/admin/clients/{}/edit"}


def test_the_label_a_person_reads_is_kept(tmp_path):
    """A report that names a URL and not the menu entry is hard to act on."""
    write(tmp_path, "nav.html", '<a href="/admin/payroll">Payroll &amp; HR</a>')
    link = lift_links(tmp_path)[0]
    assert link.text == "Payroll & HR"
    assert link.id == "nav.html::a[/admin/payroll]"


def test_a_query_and_a_fragment_do_not_make_one_link_into_several(tmp_path):
    write(tmp_path, "nav.html", """
      <a href="/admin/collections?status=open">Open</a>
      <a href="/admin/collections?status=paid">Paid</a>
      <a href="/admin/collections#top">Top</a>
      <a href="/admin/collections/">Trailing</a>
    """)
    assert {link.href for link in lift_links(tmp_path)} == {"/admin/collections"}


def test_a_href_built_entirely_by_the_template_is_not_called_dead(tmp_path):
    """`href="{{ url }}"` names no route statically.

    Reporting it as dead would be a false defect in a list whose ceiling is
    zero — the one place a false positive is most expensive.
    """
    write(tmp_path, "nav.html", '<a href="{{ next_url }}">Next</a>')
    assert lift_links(tmp_path) == []


def test_a_link_naming_no_mounted_route_is_a_defect(tmp_path):
    """THE FIRST CLAIM, and it is not a backlog.

    A menu entry to nowhere has no legitimate reason to exist, so the ceiling is
    zero rather than a ratchet worked down.

    Mutation: rename the route and leave the menu entry — which is exactly the
    scenario below — and this returns the stale link.
    """
    write(tmp_path, "nav.html", """
      <a href="/admin/clients">Clients</a>
      <a href="/admin/customers">Customers</a>
    """)
    links = lift_links(tmp_path)
    mounted = ["/admin/clients", "/admin/clients/{client_id}"]
    dead = unresolved(links, mounted)
    assert [link.href for link in dead] == ["/admin/customers"]
    assert unresolved(links, mounted + ["/admin/customers"]) == []


def test_a_dynamic_link_agrees_with_a_mounted_parameter(tmp_path):
    write(tmp_path, "nav.html", '<a href="/admin/clients/{{ c.id }}/edit">Edit</a>')
    assert unresolved(lift_links(tmp_path), ["/admin/clients/{client_id}/edit"]) == []
    assert route_key("/admin/clients/{client_id}/edit") == "/admin/clients/{}/edit"


def test_a_page_no_link_points_at_is_an_orphan(tmp_path):
    """THE SECOND CLAIM: a surface nobody can find.

    Mutation: add a page route and no link — which is what the assertion below
    does — and it is reported.
    """
    write(tmp_path, "nav.html", '<a href="/admin/clients">Clients</a>')
    links = lift_links(tmp_path)
    routes = ["/admin/clients", "/admin/secret-report", "/api/clients", "/health"]

    def is_page(p):
        return not p.startswith(("/api/", "/health"))

    assert orphans(routes, links, is_page=is_page) == ["/admin/secret-report"]


def test_orphans_refuses_without_the_project_saying_what_a_page_is(tmp_path):
    """Every route counting as a page makes the answer noise, not a finding."""
    with pytest.raises(ValueError, match="is_page"):
        orphans(["/api/x"], [], is_page=None)


def test_normalise_and_route_key_agree_on_the_root(tmp_path):
    """`/` must not be stripped to the empty string by the trailing-slash rule."""
    assert normalise("/") == "/"
    assert route_key("/") == "/"
    write(tmp_path, "nav.html", '<a href="/">Home</a>')
    assert unresolved(lift_links(tmp_path), ["/"]) == []


def test_navigation_built_in_javascript_is_lifted_too(tmp_path):
    """44 FALSE ORPHANS came from missing this.

    anat builds most of its table rows with innerHTML, so 12 of 12 links to
    /admin/collection/ live inside a <script> block. HTMLParser hands script
    content over as CDATA, so a markup-only sweep sees none of them — and the
    orphan list then reported 44 pages as unreachable when every one was
    reachable. A defect list with a ceiling of zero cannot afford that.

    Mutation: drop `links_in_script()` from `lift_links` and all three below
    disappear from the population.
    """
    write(tmp_path, "rows.html", """
      <a href="/admin/clients">Clients</a>
      <script>
        row.innerHTML = '<a href="/admin/collection/' + c.id + '">Open</a>';
        el.innerHTML = `<a href="/admin/projects/${p.id}">Project</a>`;
        function go(id) { location.href = '/admin/estimates/' + id; }
        window.open('https://example.com/external');
      </script>
    """)
    hrefs = {link.href for link in lift_links(tmp_path)}
    assert "/admin/clients" in hrefs, "markup links must still be lifted"
    assert "/admin/collection/" in hrefs or "/admin/collection/{}" in hrefs
    assert "/admin/projects/{}" in hrefs, "a JS template literal must normalise"
    assert "/admin/estimates/" in hrefs or "/admin/estimates/{}" in hrefs
    assert not any(h.startswith("http") for h in hrefs), "external stays out"


def test_the_same_destination_linked_many_times_is_one_link(tmp_path):
    """A table of thirty rows links one destination thirty times.

    Counting them separately would inflate every report and make the orphan
    arithmetic wrong.
    """
    write(tmp_path, "t.html", """
      <a href="/admin/clients">One</a>
      <a href="/admin/clients">Two</a>
      <a href="/admin/clients">Three</a>
    """)
    assert len(lift_links(tmp_path)) == 1
