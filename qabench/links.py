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


#: Navigation written in JavaScript rather than in markup. anat builds most of
#: its table rows with innerHTML, so 12 of 12 links to /admin/collection/ live
#: inside a <script> block — and HTMLParser hands script content over as CDATA,
#: so a markup-only sweep cannot see any of them. Reported 44 "unreachable"
#: pages on anat, every one of which was reachable. Found by checking the list
#: before filing it.
_JS_LINK = re.compile(
    r"""href\s*=\s*[\"'`](?P<href>/[^\"'`\s>]*)"""              # href in a JS string
    r"""|(?:location\.href|location\.assign|window\.open)\s*[=(]\s*[\"'`](?P<nav>/[^\"'`\s)]*)""",
    re.I)


class _Lifter(HTMLParser):
    def __init__(self, template: str):
        super().__init__()
        self.template = template
        self.found: list[Link] = []
        self._open: Link | None = None
        self._in_script = False
        self.scripts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self._in_script = True
            return
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
        if self._in_script:
            self.scripts.append(data)
            return
        if self._open is not None and not self._open.text:
            text = " ".join(data.split())[:60]
            if text:
                self._open.text = text

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False
        if tag == "a":
            self._open = None

    #: A character that cannot appear in a path, so the URL has ended. Without
    #: this the walk ran on into the rest of an innerHTML string and produced
    #: `/admin/clients/{}{} \u2192</a>` — markup appended to a path.
    _PATH_END = re.compile(r"""["'`<>\s]""")

    @classmethod
    def _follow_concat(cls, line: str, after: int) -> str:
        """Continue a path across `' + expr + '` — the SUFFIX, not just the prefix.

        THE FALSE DEFECTS THIS EXISTS FOR. All three "dead links" the first
        version reported on anat were real routes whose path continues after the
        id:

            '/admin/estimates/' + estimateId + '/proposal-preview'
            '/admin/customer/'  + row.get(...)  + '/billing'

        Stopping at the prefix produced `/admin/estimates/{}`, which matches no
        route, in a list whose ceiling is zero — the most expensive place for a
        false positive. anat's own scripts/qa_week/template_paths._follow_chain
        does this walk; the idea is borrowed rather than reinvented.

        Returns one PLACEHOLDER per interpolated expression plus each following
        literal, and STOPS at the first character a path cannot contain. Reads
        the rest of one LINE only — a path assembled across several lines is not
        followed, and that is stated rather than guessed at.
        """
        out = ""
        pos = 0
        rest = line[after:]
        while True:
            m = re.match(r"""["'`]?\s*\+\s*[^+]*?\+\s*["'`]""", rest[pos:])
            if not m:
                break
            out += PLACEHOLDER
            pos += m.end()
            stop = cls._PATH_END.search(rest[pos:])
            literal = rest[pos:pos + stop.start()] if stop else rest[pos:]
            out += literal
            if stop:                      # the closing quote: the URL ends here
                break
            pos += len(literal)
        if not out and re.match(r"""["'`]?\s*\+""", rest):
            out = PLACEHOLDER             # `'/a/' + id` and nothing after it
        return out

    def links_in_script(self) -> list[Link]:
        """Navigation built in JS: an href inside a string, or a location assignment.

        No label is available — the text is assembled at runtime — so these carry
        the source kind instead, which is what a reader needs to find them.
        """
        out: list[Link] = []
        blob = "\n".join(self.scripts)
        for m in _JS_LINK.finditer(blob):
            raw = m.group("href") or m.group("nav") or ""
            # `${...}` is JS interpolation; the Jinja pass has already handled
            # `{{ }}`. Both become the placeholder a route key uses.
            here = re.sub(r"\$\{[^}]*\}", PLACEHOLDER, raw)
            # A JS string ENDING in a slash is a prefix the code concatenates onto
            # — `'/admin/estimates/' + id + '/proposal-preview'`. Follow the chain
            # so the SUFFIX comes too; naming only the prefix invented three dead
            # links on anat that were all real routes.
            if here.endswith("/") and len(here) > 1:
                line_start = blob.rfind("\n", 0, m.start()) + 1
                line_end = blob.find("\n", m.start())
                line = blob[line_start:line_end if line_end != -1 else len(blob)]
                # The trailing slash is NOT itself a placeholder — the walk emits
                # one per interpolated expression. Adding one here too produced
                # `/admin/breakdown/{}{}`.
                here = here[:-1] + "/" + self._follow_concat(line, m.end() - line_start).lstrip("/")
            norm = normalise(here)
            if not norm or norm == PLACEHOLDER or not norm.startswith("/"):
                continue
            out.append(Link(template=self.template, href=norm, raw=raw,
                            text="(built in JavaScript)"))
        return out


def lift_links(template_root, glob: str = "**/*.html") -> list[Link]:
    """Every internal link in every template, sorted so a report is stable."""
    root = Path(template_root)
    out: list[Link] = []
    for p in sorted(root.glob(glob)):
        lifter = _Lifter(str(p.relative_to(root)))
        lifter.feed(neutralise_jinja(p.read_text(encoding="utf-8", errors="replace")))
        lifter.close()
        out.extend(lifter.found)
        out.extend(lifter.links_in_script())
    # Unique by id: the same destination linked from three rows of one table is
    # one link, and counting it three times would inflate every report.
    seen: dict = {}
    for link in out:
        seen.setdefault(link.id, link)
    return sorted(seen.values(), key=lambda link: link.id)


def _matcher(path: str):
    """A route as a pattern: every parameter matches ONE concrete segment.

    STRING EQUALITY IS NOT ROUTE RESOLUTION, and assuming it was produced a
    fourth round of false defects. ana-log declares one route `/cards/:card/:id`
    and 25 descriptor link targets like `/cards/customers/{Orders.customer}`;
    comparing normalised strings called all 25 dead when every one resolves. The
    same trap was latent for anat: a link written with a literal id,
    `/admin/clients/7/edit`, would never equal `/admin/clients/{}/edit`.

    A placeholder on the LINK side matches a concrete route segment too, because
    the id it stands for is concrete at runtime.
    """
    parts = re.split(r"\{[^}]*\}|:[A-Za-z_][A-Za-z0-9_]*", path)
    return re.compile("".join(re.escape(x) if i == 0 else r"[^/]+" + re.escape(x)
                              for i, x in enumerate(parts)) + r"/?$")


def unresolved(links: list[Link], route_paths) -> list[Link]:
    """Links naming no mounted route. A defect list; its ceiling is zero.

    Resolves each link against the route PATTERNS, so `/admin/clients/7/edit` and
    a mounted `/admin/clients/{client_id}/edit` agree — and so does a link whose
    own dynamic segment is a placeholder.
    """
    patterns = [_matcher(p) for p in route_paths]
    out = []
    for link in links:
        probe = link.href.replace(PLACEHOLDER, "1")
        if not any(pat.fullmatch(probe) for pat in patterns):
            out.append(link)
    return out


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
