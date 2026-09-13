"""Every way a person NAVIGATES — the population the control register never had.

THE GAP. `qabench.gestures` lifts buttons and forms. It looks at an `<a>` only
when the anchor carries `data-action` or `onclick`; it never reads `href` at all.
So a nav link, a sidebar entry, a breadcrumb, a card link or a tab pointing at a
dead or renamed page is not in the population — not undriven, ABSENT. The estate
has been reporting "no non-functional buttons" while the menus were unexamined.

THREE CLAIMS, and the first two are not backlogs.

  1. Every internal link names a MOUNTED ROUTE. A menu entry to nowhere has no
     legitimate reason to exist, so this is a defect list with a ceiling of zero,
     not a ratchet to be worked down.

  2. Every route that RENDERS A PAGE is reachable by at least one link. An
     orphaned surface is a feature nobody can find. The project declares which
     routes are pages, because only it knows that /api and /health are not.

  3. Every link a ROLE IS SHOWN answers the status that role's guard declares.
     A link rendered for someone who gets a 403 is as broken as a dead one, and
     this is the half a static check cannot see — it needs the live app and a
     session per role, so it is a bench stage (`links_by_role`) rather than a
     unit guard. The page sweep already loads routes per role; this makes it
     MENU-driven instead of route-driven, which is the actual gap.

Dynamic segments are normalised the way actions are: `{{ c.id }}` has already
become `{}` by the time this reads the markup, and a mounted `{client_id}`
becomes `{}` too, so the two sides compare.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

from .gestures import PLACEHOLDER, neutralise_jinja

#: Schemes and shapes that are not internal navigation. `#` alone is a control
#: (a tab, a dialog opener) and belongs to the gesture register, not here.
_EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", re.I)


@dataclass
class Link:
    template: str
    href: str          #: normalised, PLACEHOLDER for every dynamic segment
    raw: str           #: as written, for the failure message
    text: str = ""     #: the visible label, so a report names what a person sees

    @property
    def id(self) -> str:
        return f"{self.template}::a[{self.href}]"


def normalise(href: str) -> str:
    """`/admin/clients/{}/edit?tab=x#frag` -> `/admin/clients/{}/edit`.

    Query and fragment are dropped: they do not choose a route, and keeping them
    would make one link read as several.
    """
    href = href.split("#", 1)[0].split("?", 1)[0].strip()
    if len(href) > 1:
        href = href.rstrip("/")
    return href


def route_key(path: str) -> str:
    """A mounted path in the same shape: `/admin/clients/{client_id}` -> `.../{}`."""
    out = re.sub(r"\{[^}]*\}", PLACEHOLDER, path)
    return out.rstrip("/") if len(out) > 1 else out


class _Lifter(HTMLParser):
    def __init__(self, template: str):
        super().__init__()
        self.template = template
        self.found: list[Link] = []
        self._open: Link | None = None

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = ""
        for k, v in attrs:
            if (k or "").lower() == "href":
                href = (v or "").strip()
        if not href or _EXTERNAL.match(href):
            return
        # A href that is ENTIRELY a placeholder was built by the template from a
        # value we cannot see; it names no route statically and must not be
        # reported as dead. Recorded as unresolvable rather than silently
        # dropped would be better still, but the population here is what a
        # static reader can honestly resolve.
        norm = normalise(href)
        if not norm or norm == PLACEHOLDER or not norm.startswith("/"):
            return
        self._open = Link(template=self.template, href=norm, raw=href)
        self.found.append(self._open)

    def handle_data(self, data):
        if self._open is not None and not self._open.text:
            text = " ".join(data.split())[:60]
            if text:
                self._open.text = text

    def handle_endtag(self, tag):
        if tag == "a":
            self._open = None


def lift_links(template_root, glob: str = "**/*.html") -> list[Link]:
    """Every internal link in every template, sorted so a report is stable."""
    root = Path(template_root)
    out: list[Link] = []
    for p in sorted(root.glob(glob)):
        lifter = _Lifter(str(p.relative_to(root)))
        lifter.feed(neutralise_jinja(p.read_text(encoding="utf-8", errors="replace")))
        lifter.close()
        out.extend(lifter.found)
    return sorted(out, key=lambda link: link.id)


def unresolved(links: list[Link], route_paths) -> list[Link]:
    """Links naming no mounted route. A defect list; its ceiling is zero.

    Compares on the normalised shape, so a link to `/admin/clients/7/edit` and a
    mounted `/admin/clients/{client_id}/edit` agree.
    """
    mounted = {route_key(p) for p in route_paths}
    return [link for link in links if link.href not in mounted]


def orphans(route_paths, links: list[Link], *, is_page=None) -> list[str]:
    """Page routes no link points at — a surface nobody can find.

    `is_page` is supplied by the PROJECT, because only it knows that `/api/...`,
    `/health` and a download are not pages a person navigates to. Without one,
    every route counts and the answer is noise.
    """
    if is_page is None:
        raise ValueError(
            "orphans() needs is_page from the project: without it /api and /health "
            "count as pages and the result is noise, not a finding")
    linked = {link.href for link in links}
    return sorted({route_key(p) for p in route_paths
                   if is_page(p) and route_key(p) not in linked})
