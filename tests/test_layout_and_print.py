"""`qabench.layout` and `qabench.printcheck` — geometry, read the way a person and a printer read it.

Each defect is PLANTED in a page or a PDF built here, and a healthy twin must
come back clean — a guard that cannot pass is as useless as one that cannot fail.

Mutation (watched 2026-09-19): the squeezed-control rule's `minTarget`
comparison inverted → the healthy page reports every control; `orientation`
compared by page width alone ignoring /Rotate → the rotated-landscape PDF reads
portrait.
"""
from __future__ import annotations

import base64
import io

import pytest

pw = pytest.importorskip("playwright.sync_api")
zx = pytest.importorskip("zxingcpp")

from qabench import layout, printcheck

HEALTHY = """<!doctype html><html dir=rtl><body style="margin:0;font:16px sans-serif">
<header style="height:60px"><input aria-label="search" style="width:200px;height:32px"></header>
<table><tr role=row><th role=columnheader>שם</th></tr><tr role=row><td>משטח 12</td></tr></table>
<p style="width:300px">סה״כ 244,40 ₪</p></body></html>"""

BROKEN = """<!doctype html><html dir=rtl><body style="margin:0;font:16px sans-serif">
<header style="height:500px"><input aria-label="search" style="width:4px;height:32px"></header>
<table><tr role=row><th role=columnheader>שם</th></tr><tr role=row><td>
  <div style="width:60px;overflow:hidden;white-space:nowrap">מוצר עם שם ארוך במיוחד</div></td></tr></table>
<p style="width:40px;overflow-wrap:anywhere">2026090211471</p></body></html>"""


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _measure(browser, html, w=390, h=844):
    page = browser.new_page(viewport={"width": w, "height": h})
    page.set_content(html)
    out = layout.measure(page)
    page.close()
    return out


def test_a_healthy_page_is_clean(browser):
    assert _measure(browser, HEALTHY) == []


def test_every_planted_layout_defect_is_named(browser):
    kinds = layout.summary(_measure(browser, BROKEN))
    assert kinds == {"clipped": 1, "squeezed": 1, "split-number": 1, "budget": 1}, kinds


def _pdf(browser, html, w_mm, h_mm):
    page = browser.new_page()
    page.set_content(html)
    data = page.pdf(width=f"{w_mm}mm", height=f"{h_mm}mm", print_background=True)
    page.close()
    return data


def _code_img(text, fmt):
    svg = zx.write_barcode_to_svg(zx.create_barcode(text, getattr(zx.BarcodeFormat, fmt)))
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def _label(browser, fmt, w_mm, h_mm, payload="7451"):
    html = f"<body style='margin:8mm'><img src='{_code_img(payload, fmt)}' style='width:40mm'><p>משטח {payload}</p></body>"
    return _pdf(browser, html, w_mm, h_mm)


def test_a_label_on_the_right_paper_with_a_readable_qr_is_clean(browser):
    pdf = _label(browser, "QRCode", 150, 100)
    assert printcheck.check_pdf(pdf, paper_mm=(100, 150), orientation="landscape", symbology="QRCode",
                                codes_per_page=1, expect_payloads={"7451"}) == []


def test_code_128_where_the_field_reads_qr_is_named(browser):
    pdf = _label(browser, "Code128", 150, 100)
    kinds = {p["kind"] for p in printcheck.check_pdf(pdf, symbology="QRCode", codes_per_page=1)}
    assert "symbology" in kinds


def test_the_right_size_the_wrong_way_round_is_named(browser):
    pdf = _label(browser, "QRCode", 100, 150)                     # portrait, printer holds it landscape
    problems = printcheck.check_pdf(pdf, paper_mm=(100, 150), orientation="landscape")
    assert [p["kind"] for p in problems] == ["orientation"]


def test_a4_where_the_stock_is_a_label_roll_is_named(browser):
    pdf = _label(browser, "QRCode", 210, 297)
    assert "paper" in {p["kind"] for p in printcheck.check_pdf(pdf, paper_mm=(100, 150))}


def test_a_neighbouring_code_on_the_same_page_is_counted(browser):
    html = f"<body><img src='{_code_img('1', 'QRCode')}' style='width:30mm'><img src='{_code_img('2', 'QRCode')}' style='width:30mm'></body>"
    pdf = _pdf(browser, html, 150, 100)
    assert "codes" in {p["kind"] for p in printcheck.check_pdf(pdf, codes_per_page=1)}
