"""core.shot is evidence for a cell already decided; it must not abort the stage.

2026-10-23, IGA: WebKit at 390px refused a full-page shot of /admin/trades
("Cannot take screenshot larger than 32767 pixels on any dimension") and
pages_by_role died with 15 cells undecided, which skipped the promotion.
"""
from __future__ import annotations

import pytest

from qabench import core


class FakePage:
    def __init__(self, error: str | None):
        self.error = error
        self.calls: list[bool] = []

    def screenshot(self, path: str, full_page: bool):
        self.calls.append(full_page)
        if full_page and self.error:
            raise RuntimeError(self.error)


def test_a_page_too_tall_for_a_full_shot_gets_the_viewport(tmp_path):
    page = FakePage("Page.screenshot: Cannot take screenshot larger than 32767 pixels on any dimension")
    core.shot(page, tmp_path, "admin__phone__admin_trades")
    assert page.calls == [True, False]


def test_an_ordinary_page_gets_one_full_shot(tmp_path):
    page = FakePage(None)
    core.shot(page, tmp_path, "admin__desk__admin")
    assert page.calls == [True]


def test_any_other_screenshot_error_still_raises(tmp_path):
    page = FakePage("Target page, context or browser has been closed")
    with pytest.raises(RuntimeError, match="closed"):
        core.shot(page, tmp_path, "x")
