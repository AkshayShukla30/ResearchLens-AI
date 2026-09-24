from __future__ import annotations

from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from src.embeddings.embedder import create_embeddings


class VectorStore:
    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.embeddings = create_embeddings()

    def build(self, documents: List[Document]) -> FAISS:
        db = FAISS.from_documents(documents, self.embeddings)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        db.save_local(str(self.index_dir))
        return db

    def load(self) -> FAISS:
        return FAISS.load_local(
            str(self.index_dir),
            self.embeddings,
            allow_dangerous_deserialization=True,
        )

    def exists(self) -> bool:
        return (self.index_dir / "index.faiss").exists() and (self.index_dir / "index.pkl").exists()
