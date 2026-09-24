"""FAISS vector store with per-document management and disk persistence."""
import json
import shutil
import threading
import time
from typing import Dict, List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

import config
from core.embeddings import get_embeddings


class VectorStoreManager:
    def __init__(self) -> None:
        self.embeddings = get_embeddings()
        self.store: Optional[FAISS] = None
        self.registry: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._index_dir = config.DATA_DIR / "faiss"
        self._registry_file = config.DATA_DIR / "registry.json"
        self._load()

    # ---------- persistence ----------
    def _load(self) -> None:
        if self._registry_file.exists() and (self._index_dir / "index.faiss").exists():
            try:
                self.registry = json.loads(self._registry_file.read_text())
                self.store = FAISS.load_local(
                    str(self._index_dir), self.embeddings, allow_dangerous_deserialization=True
                )
            except Exception:
                self.registry, self.store = {}, None

    def _persist(self) -> None:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        if self.store is None or not self.registry:
            shutil.rmtree(self._index_dir, ignore_errors=True)
            self._registry_file.unlink(missing_ok=True)
            return
        self.store.save_local(str(self._index_dir))
        self._registry_file.write_text(json.dumps(self.registry, indent=2))

    # ---------- documents ----------
    def add_document(self, doc_id: str, filename: str, pages: int, chunks: List[Document],
                     chunk_size: int, chunk_overlap: int) -> Dict:
        ids = [f"{doc_id}:{i}" for i in range(len(chunks))]
        for cid, chunk in zip(ids, chunks):
            chunk.metadata["chunk_id"] = cid
        with self._lock:
            if self.store is None:
                self.store = FAISS.from_documents(chunks, self.embeddings, ids=ids)
            else:
                self.store.add_documents(chunks, ids=ids)
            meta = {
                "doc_id": doc_id,
                "filename": filename,
                "pages": pages,
                "chunks": len(chunks),
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "chunk_ids": ids,
                "uploaded_at": time.time(),
            }
            self.registry[doc_id] = meta
            self._persist()
            return self.public_meta(meta)

    def delete_document(self, doc_id: str) -> bool:
        with self._lock:
            meta = self.registry.pop(doc_id, None)
            if meta is None:
                return False
            if self.store is not None:
                self.store.delete(meta["chunk_ids"])
            if not self.registry:
                self.store = None
            self._persist()
            return True

    def clear(self) -> None:
        with self._lock:
            self.registry.clear()
            self.store = None
            self._persist()

    @staticmethod
    def public_meta(meta: Dict) -> Dict:
        return {k: v for k, v in meta.items() if k != "chunk_ids"}

    def list_documents(self) -> List[Dict]:
        with self._lock:
            docs = sorted(self.registry.values(), key=lambda m: m["uploaded_at"])
            return [self.public_meta(m) for m in docs]

    def get_document_chunks(self, doc_id: str) -> List[Document]:
        """All chunks of one document in reading order."""
        with self._lock:
            meta = self.registry.get(doc_id)
            if meta is None or self.store is None:
                return []
            out = []
            for cid in meta["chunk_ids"]:
                doc = self.store.docstore.search(cid)
                if isinstance(doc, Document):
                    out.append(doc)
            return out

    # ---------- retrieval ----------
    def search(self, query: str, k: int, doc_ids: Optional[List[str]] = None
               ) -> List[Tuple[Document, float]]:
        """Return (chunk, similarity 0..1) pairs. Embeddings are normalised, so
        squared-L2 distance d maps to cosine similarity 1 - d/2."""
        with self._lock:
            if self.store is None:
                return []
            total = self.store.index.ntotal
            kwargs = {}
            if doc_ids:
                kwargs["filter"] = {"doc_id": list(doc_ids)}
                kwargs["fetch_k"] = total
            results = self.store.similarity_search_with_score(query, k=k, **kwargs)
        return [(doc, max(0.0, min(1.0, 1.0 - float(dist) / 2.0))) for doc, dist in results]
