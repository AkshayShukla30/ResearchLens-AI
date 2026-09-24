"""Embedding model factory (HuggingFace sentence-transformers)."""
import hashlib
from typing import List

from langchain_core.embeddings import Embeddings

import config


class FakeEmbeddings(Embeddings):
    """Deterministic hashing embeddings. Offline tests only (EMBEDDING_PROVIDER=fake)."""

    dim = 128

    def _vec(self, text: str) -> List[float]:
        v = [0.0] * self.dim
        for tok in text.lower().split():
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0
        norm = sum(x * x for x in v) ** 0.5 or 1.0
        return [x / norm for x in v]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._vec(text)


def get_embeddings() -> Embeddings:
    if config.EMBEDDING_PROVIDER == "fake":
        return FakeEmbeddings()
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )
