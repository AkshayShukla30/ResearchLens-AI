from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import fitz
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_pdf(path: Path, chunk_size: int, chunk_overlap: int) -> tuple[List[Document], int]:
    """Extract text page-by-page so page metadata is preserved."""
    pages: List[Document] = []
    with fitz.open(path) as pdf:
        page_count = len(pdf)
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            if not text:
                continue
            pages.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "page": page_number,
                        "page_label": str(page_number),
                    },
                )
            )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
    )
    chunks = splitter.split_documents(pages)

    for idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = idx

    return chunks, page_count
