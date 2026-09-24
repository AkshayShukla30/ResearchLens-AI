"""PDF text extraction with PyMuPDF (page-aware, so citations carry page numbers)."""
from typing import Dict, List

import pymupdf as fitz  # PyMuPDF


class PDFError(ValueError):
    pass


def extract_pages(data: bytes) -> List[Dict]:
    try:
        pdf = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # corrupt / not a pdf
        raise PDFError(f"Could not open PDF: {exc}") from exc

    pages: List[Dict] = []
    try:
        for number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append({"page": number, "text": text})
        total = pdf.page_count
    finally:
        pdf.close()

    if not pages:
        raise PDFError("No extractable text found (scanned PDF without OCR?).")
    return [{**p, "total_pages": total} for p in pages]
