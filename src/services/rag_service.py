from __future__ import annotations

import time
from collections import Counter
from pathlib import Path

from src.ingestion.pdf_processor import extract_pdf


class RAGService:
    def __init__(self, document_service, settings):
        self.document_service = document_service
        self.settings = settings

    def retrieve(self, query: str):
        start = time.perf_counter()
        db = self.document_service.store.load()
        results = db.similarity_search_with_score(query, k=self.settings["top_k"])
        chunks = []
        for doc, distance in results:
            chunks.append({
                "text": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page"),
                "chunk_id": doc.metadata.get("chunk_id"),
                "distance": float(distance),
            })
        return chunks, (time.perf_counter() - start) * 1000

    def build_sources(self, chunks):
        seen = set()
        sources = []
        for chunk in chunks:
            key = (chunk.get("source"), chunk.get("page"))
            if key in seen:
                continue
            seen.add(key)
            sources.append({
                "source": chunk.get("source"),
                "page": chunk.get("page"),
                "context": "Retrieved page/chunk evidence",
            })
        return sources

    def document_content(self, filename: str) -> str:
        path = self.document_service.upload_dir / Path(filename).name
        chunks, _ = extract_pdf(
            path,
            self.settings["chunk_size"],
            self.settings["chunk_overlap"],
        )
        return "\n\n".join(c.page_content for c in chunks)
