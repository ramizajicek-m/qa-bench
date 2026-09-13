"""Attribute requests to the CONTROL that caused them, by bracketing the click.

THE PROBLEM THIS SOLVES, in one measurement: anat has 973 controls and 125 are
judgeable. The other 848 are not untested — they are unmeasurable, because
`judgeable` means the lifter resolved what URL a control calls, and 804 buttons
and 44 forms have no resolvable action. 45,000 lines of inline JS build their
paths from ternaries and concatenation, `apiFetch` covers 150 of ~950 request
sites, and `templates/admin/layout.html` monkey-patches `window.fetch` so every
admin request goes through a chokepoint that exists only in a browser.

A passive browser recorder does NOT fix it, and this was measured rather than
assumed: adding one to anat's e2e conftest moved `judgeable` by zero. Recording
more traffic cannot name a control whose destination is unknown — you learn that
`POST /api/x` happened, not which of 804 buttons sent it.

**The click is the identity.** Clear the sink, click ONE control, wait for the
network to settle, and every request in that window belongs to that control. No
URL needs to be known in advance, which is the whole point.

WHAT THIS CANNOT DO, stated rather than discovered later:

  * Two clicks racing in one window cannot be separated, so `press` SERIALISES
    and refuses to nest. A wrong attribution is worse than none — that lesson
    cost six false "accepted" verdicts on 2026-09-13.
  * A control that schedules work returning later is attributed to the window it
    opened, not to the request it eventually causes.
  * Traffic arriving while no press is outstanding is reported as UNATTRIBUTED,
    never assigned to whichever control was pressed last.
  * ACCEPTED IS NOT CORRECT. This says a request the control sent was acted on.
    It says nothing about whether the right row changed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

#: One press at a time, process-wide. Nesting cannot be attributed, so it is
#: refused rather than guessed at.
_OUTSTANDING: str | None = None

ENV = "QABENCH_RECORD_PRESSES"


class NestedPress(RuntimeError):
    """Two presses open at once — the window cannot say which control acted."""


def target_path() -> Path | None:
    """Where presses are recorded, or None when recording is off."""
    raw = os.environ.get(ENV)
    if not raw:
        return None
    p = Path(raw)
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    if worker:
        p = p.with_name(f"{p.stem}.{worker}{p.suffix}")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _append(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


class press:
    """Context manager: attribute every request in the window to `control_id`.

        with press(page, "admin/clients/detail.html::button[id=fs-bf-save]"):
            page.click("#fs-bf-save")

    The control id is the register's own key, so what this records joins the
    register by identity instead of by URL.
    """

    def __init__(self, page, control_id: str, settle_ms: int = 1500):
        self.page = page
        self.control_id = control_id
        self.settle_ms = settle_ms
        self.seen: list[tuple[str, str, int]] = []
        self._handler = None

    def __enter__(self):
        global _OUTSTANDING
        if _OUTSTANDING is not None:
            raise NestedPress(
                f"press({self.control_id!r}) opened while press({_OUTSTANDING!r}) "
                f"is still outstanding. Two clicks in one window cannot be told "
                f"apart, and a wrong attribution is worse than none — serialise "
                f"them.")
        _OUTSTANDING = self.control_id

        def _on(response):
            try:
                self.seen.append((response.request.method, response.url,
                                  response.status))
            except (AttributeError, ValueError):
                pass          # a response whose request is already gone

        self._handler = _on
        self.page.on("response", _on)
        return self

    def __exit__(self, exc_type, exc, tb):
        global _OUTSTANDING
        try:
            if exc_type is None:
                # Let the handler's own requests land before closing the window.
                try:
                    self.page.wait_for_timeout(self.settle_ms)
                except Exception:  # noqa: BLE001 - a closed page is not a finding
                    pass
            self.page.remove_listener("response", self._handler)

            path = target_path()
            if path is not None and exc_type is None:
                from .hits import _acted
                accepted = any(_acted(s, "") or 200 <= s < 300
                               for _m, _u, s in self.seen)
                _append(path, {
                    "control": self.control_id,
                    "requests": [f"{m} {u} {s}" for m, u, s in self.seen],
                    "accepted": accepted,
                })
        finally:
            _OUTSTANDING = None
        return False


def read_presses(path) -> dict:
    """`{control_id: accepted}` from one file or a directory of them.

    A control pressed twice is accepted if it was EVER accepted: one refusal
    among several presses is a test driving the refusal, not evidence the control
    is broken.
    """
    p = Path(path)
    files = sorted(p.glob("*.jsonl")) if p.is_dir() else ([p] if p.exists() else [])
    out: dict = {}
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cid = row["control"]
            out[cid] = out.get(cid, False) or bool(row.get("accepted"))
    return out
