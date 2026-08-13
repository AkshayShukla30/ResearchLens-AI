from pathlib import Path
import fitz
from src.ingestion.pdf_processor import extract_pdf

def test_pdf_extraction_preserves_page_metadata(tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Research paper content.")
    doc.save(pdf_path)
    doc.close()

    chunks, pages = extract_pdf(pdf_path, 200, 20)
    assert pages == 1
    assert chunks
    assert chunks[0].metadata["source"] == "paper.pdf"
    assert chunks[0].metadata["page"] == 1
