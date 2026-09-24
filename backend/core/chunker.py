"""Text chunking with configurable size / overlap."""
from typing import Dict, List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pages(
    pages: List[Dict], doc_id: str, filename: str, chunk_size: int, chunk_overlap: int
) -> List[Document]:
    if chunk_size < 100:
        raise ValueError("chunk_size must be at least 100")
    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size")

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks: List[Document] = []
    for page in pages:
        for piece in splitter.split_text(page["text"]):
            chunks.append(
                Document(
                    page_content=piece,
                    metadata={"doc_id": doc_id, "source": filename, "page": page["page"]},
                )
            )
    return chunks
