"""layout — measure what a page LOOKS like: clipped text, squeezed controls, split numbers, the space left for records.

    from qabench.layout import measure
    problems = measure(page)          # a Playwright page, after it has settled

WHY. 15 of the 121 defects people found in ana-log were layout, and the browser
tier passed every one because it asked the only mechanical question it had —
is the page wider than the screen — which they all pass:

  * a search box squeezed to its own icon on a phone; "a control squeezed to
    0 px causes no overflow" (Shahar, AL-054);
  * the first record pushed to 390 px of an 844 px phone screen by four rows of
    controls (AL-051);
  * `244,40` broken mid-number by `overflow-wrap: anywhere` (AL-041), and a
    14-digit label value split with a lone `4` on the next line (AL-048);
  * a product name cut mid-word in a table cell (AL-105); a field drawn with a
    line through its label (AL-098).

Each is a property of RENDERED geometry, so this reads geometry: every visible
element's box, per viewport. It reports; the caller decides whether a finding
fails (the stage) or is recorded (a ratchet). Findings name the element by a
readable path and quote its text, so a person can find it.

  clipped      text cut by its own box: overflow hidden/clip (or an ellipsis)
               with scrollWidth > clientWidth — a label nobody can read in full
  squeezed     a visible control (input, button, link, select, [role=button])
               narrower or shorter than `min_target` px (WCAG 2.5.8 says 24)
  split-number a run of digits (with , . : / -) rendered across two lines
  budget       on a screen with a table or list, the first data row starts
               below `budget` of the viewport height (phones: records first)

What it cannot see, stated: text drawn into a canvas; a clip done with
`clip-path`; overlap between elements (too many deliberate overlays to judge
generically) — those stay with a person and the explorer.
"""
from __future__ import annotations

_JS = r"""
({minTarget, budget}) => {
  const out = [];
  const vh = window.innerHeight;
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0 && el.getClientRects().length === 0) return null;
    const s = getComputedStyle(el);
    if (s.visibility === 'hidden' || s.display === 'none' || Number(s.opacity) === 0) return null;
    return r;
  };
  const name = (el) => {
    const bits = [];
    for (let e = el, i = 0; e && e.nodeType === 1 && i < 4; e = e.parentElement, i++) {
      let b = e.tagName.toLowerCase();
      const label = e.getAttribute('aria-label') || e.getAttribute('name') || e.getAttribute('data-testid');
      if (label) b += `[${label.slice(0, 30)}]`;
      bits.unshift(b);
    }
    return bits.join(' > ');
  };
  const text = (el) => (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 60);

  // clipped
  for (const el of document.querySelectorAll('body *')) {
    if (!el.firstChild || el.children.length > 3) continue;
    const t = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
    if (t.length < 2) continue;
    const r = visible(el); if (!r) continue;
    const s = getComputedStyle(el);
    const hides = /hidden|clip/.test(s.overflowX + s.overflow) || s.textOverflow === 'ellipsis';
    if (hides && el.scrollWidth > el.clientWidth + 1)
      out.push({kind: 'clipped', where: name(el), text: t.slice(0, 60), detail: `${el.scrollWidth}px of text in ${el.clientWidth}px`});
  }
  // squeezed
  const controls = 'input:not([type=hidden]), button, select, textarea, a[href], [role=button], [role=combobox], [role=checkbox]';
  for (const el of document.querySelectorAll(controls)) {
    const r = visible(el); if (!r) continue;
    if (el.closest('[aria-hidden=true]')) continue;
    if (r.width < minTarget || r.height < minTarget) {
      const inline = el.tagName === 'A' && getComputedStyle(el).display === 'inline';   // WCAG 2.5.8 exempts inline links
      if (!inline) out.push({kind: 'squeezed', where: name(el), text: text(el),
                             detail: `${Math.round(r.width)}×${Math.round(r.height)}px, under ${minTarget}px`});
    }
  }
  // split-number
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const num = /\d[\d,.:/\-]{3,}\d/g;
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const p = n.parentElement; if (!p || !visible(p)) continue;
    for (const m of n.textContent.matchAll(num)) {
      const range = document.createRange();
      range.setStart(n, m.index); range.setEnd(n, m.index + m[0].length);
      const tops = new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top)));
      if (tops.size > 1) out.push({kind: 'split-number', where: name(p), text: m[0], detail: `drawn on ${tops.size} lines`});
    }
  }
  // budget
  const row = document.querySelector('[role=row]:not(:first-child), tbody tr, [role=listitem], li[data-row]');
  const hasHeaderRow = document.querySelector('[role=row]');
  const first = hasHeaderRow ? [...document.querySelectorAll('[role=row]')].find(r => !r.querySelector('[role=columnheader]')) : row;
  if (first) {
    const r = visible(first);
    if (r && r.top > vh * budget)
      out.push({kind: 'budget', where: name(first), text: text(first),
                detail: `first record starts at ${Math.round(r.top)}px of ${vh}px (${Math.round(100 * r.top / vh)}% down)`});
  }
  return out;
}
"""


def measure(page, *, min_target: int = 24, budget: float = 0.5) -> list[dict]:
    """[{kind, where, text, detail}] for the page as rendered now."""
    return page.evaluate(_JS, {"minTarget": min_target, "budget": budget})


def summary(problems: list[dict]) -> dict:
    out: dict = {}
    for p in problems:
        out[p["kind"]] = out.get(p["kind"], 0) + 1
    return out
