"""printcheck — the printed thing, read the way the paper and the scanner will read it.

    from qabench.printcheck import check_pdf
    problems = check_pdf(pdf_bytes, paper_mm=(100, 150), orientation="landscape",
                         symbology="QRCode", codes_per_page=1, expect_payloads={...})

WHY. The label in ana-log was reported four times in three days, each time by
Israel holding the paper (AL-014/015/016), and the camera could not read a
single label the system had ever printed (AL-006): the printer drew Code 128,
the camera decodes QR. Eleven guards measured the sheet and all eleven asked
whether the content fits THE PAGE THE SHEET DECLARES — the code agreeing with
itself. Two questions were never asked of the output:

  1. PAPER. Is each page the size and orientation of the stock in the printer
     (from `qa/requirements.yml` — an answer a person gave), not whatever the
     template declared? A 100×150 page printed portrait on a landscape roll is
     the right size and the wrong way round.
  2. SCANNER. Rasterised at the printer's resolution, does every page decode —
     with the symbology the reader in the field actually reads, the expected
     number of codes, and the payload the scan handler accepts?

Also: text that runs off the page box (a clipped line on paper cannot scroll).
Requires the kit's `print` extra: pypdf, pypdfium2, zxing-cpp.
"""
from __future__ import annotations

import io

MM_PER_PT = 25.4 / 72


def _pages(pdf: bytes):
    from pypdf import PdfReader
    return PdfReader(io.BytesIO(pdf)).pages


def check_pdf(pdf: bytes, *, paper_mm: tuple[float, float] | None = None, orientation: str | None = None,
              symbology: str | None = None, codes_per_page: int | None = None,
              expect_payloads: set[str] | None = None, dpi: int = 203, tolerance_mm: float = 2.0) -> list[dict]:
    """[{page, kind, detail}] — [] when the PDF is what the paper and the reader need."""
    problems: list[dict] = []
    if not pdf.startswith(b"%PDF"):
        return [{"page": 0, "kind": "not-a-pdf", "detail": f"the answer is not a PDF: {pdf[:60]!r}"}]
    pages = _pages(pdf)
    if not pages:
        return [{"page": 0, "kind": "empty", "detail": "the PDF has no pages"}]
    for i, page in enumerate(pages, 1):
        box = page.mediabox
        rot = (page.get("/Rotate") or 0) % 180
        w, h = float(box.width) * MM_PER_PT, float(box.height) * MM_PER_PT
        if rot:
            w, h = h, w
        if paper_mm:
            a, b = sorted(paper_mm)
            if not (abs(min(w, h) - a) <= tolerance_mm and abs(max(w, h) - b) <= tolerance_mm):
                problems.append({"page": i, "kind": "paper", "detail": f"page is {w:.0f}×{h:.0f} mm, the stock is {a:g}×{b:g} mm"})
        if orientation:
            actual = "landscape" if w > h else "portrait"
            if actual != orientation:
                problems.append({"page": i, "kind": "orientation", "detail": f"page is {actual} ({w:.0f}×{h:.0f} mm), the printer holds it {orientation}"})
    problems += _offpage_text(pdf)
    if symbology or codes_per_page is not None or expect_payloads:
        problems += _decode(pdf, symbology, codes_per_page, expect_payloads, dpi)
    return problems


def _offpage_text(pdf: bytes) -> list[dict]:
    import pdfplumber
    out = []
    with pdfplumber.open(io.BytesIO(pdf)) as doc:
        for i, page in enumerate(doc.pages, 1):
            off = [w["text"] for w in page.extract_words()
                   if w["x0"] < -0.5 or w["top"] < -0.5 or w["x1"] > page.width + 0.5 or w["bottom"] > page.height + 0.5]
            if off:
                out.append({"page": i, "kind": "off-page", "detail": f"{len(off)} word(s) outside the page: {' '.join(off[:6])[:80]}"})
    return out


def _decode(pdf: bytes, symbology, codes_per_page, expect_payloads, dpi) -> list[dict]:
    import pypdfium2 as pdfium
    import zxingcpp
    out = []
    seen: set[str] = set()
    doc = pdfium.PdfDocument(pdf)
    for i in range(len(doc)):
        image = doc[i].render(scale=dpi / 72).to_pil().convert("L")
        found = zxingcpp.read_barcodes(image)
        kinds = [str(b.format).split(".")[-1] for b in found]
        texts = [b.text for b in found]
        seen.update(texts)
        if codes_per_page is not None and len(found) != codes_per_page:
            out.append({"page": i + 1, "kind": "codes", "detail": f"{len(found)} code(s) decoded at {dpi} dpi, expected {codes_per_page}: {kinds}"})
        if symbology:
            norm = lambda x: "".join(ch for ch in x.lower() if ch.isalnum())     # "QR Code" == "QRCode" == "qr_code"
            wrong = [k for k in kinds if norm(k) != norm(symbology)]
            if wrong or not found:
                out.append({"page": i + 1, "kind": "symbology",
                            "detail": f"the reader in the field reads {symbology}; this page carries {kinds or 'nothing it can read'}"})
    if expect_payloads:
        missing = sorted(expect_payloads - seen)
        if missing:
            out.append({"page": 0, "kind": "payload", "detail": f"{len(missing)} expected payload(s) not decoded: {missing[:5]}"})
    return out
