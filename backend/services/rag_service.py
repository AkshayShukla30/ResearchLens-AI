"""RAG orchestration: ask, compare, summarize and semantic search."""
import logging
import time
from typing import Dict, List, Optional, Tuple

from langchain_core.documents import Document

import config
from core.vector_store import VectorStoreManager
from llm import LLMProvider

logger = logging.getLogger(__name__)

Hit = Tuple[Document, float]

ASK_SYSTEM = (
    "You are ResearchLens, an assistant that answers questions about research papers. "
    "Answer ONLY from the provided context. If the context does not contain the answer, say so plainly. "
    "Cite evidence inline as [filename, p.N]. Be precise and do not invent facts, numbers or citations."
)

SUMMARY_STYLES = {
    "concise": "Write a concise summary (about 150-200 words) covering problem, method, key results and conclusion.",
    "detailed": (
        "Write a detailed structured summary with these sections: Problem & Motivation, Methodology, "
        "Experiments & Results, Contributions, Limitations, Conclusion."
    ),
    "key_points": "Write 6-10 bullet points capturing the most important findings, methods and takeaways.",
}

BATCH_SIZE = 12  # chunks per map step
MAX_CHUNKS = 96  # cap on chunks used for one summary (evenly sampled)


class NotFound(ValueError):
    pass


class RetrievalError(RuntimeError):
    pass


def _fmt_context(hits: List[Hit]) -> str:
    return "\n\n".join(
        f"[{doc.metadata['source']}, p.{doc.metadata['page']}]\n{doc.page_content}" for doc, _ in hits
    )


def _diagnostics(hits: List[Hit], top_k: int, t_ret: float, t_gen: float, t_total: float,
                 llm: LLMProvider, calls: int) -> Dict:
    scores = [s for _, s in hits]
    return {
        "retrieval_ms": round(t_ret * 1000, 1),
        "generation_ms": round(t_gen * 1000, 1),
        "total_ms": round(t_total * 1000, 1),
        "top_k": top_k,
        "chunks_retrieved": len(hits),
        "avg_score": round(sum(scores) / len(scores), 4) if scores else 0,
        "max_score": round(max(scores), 4) if scores else 0,
        "min_score": round(min(scores), 4) if scores else 0,
        "documents_hit": sorted({d.metadata["source"] for d, _ in hits}),
        "context_chars": sum(len(d.page_content) for d, _ in hits),
        "embedding_model": config.EMBEDDING_MODEL,
        "llm_provider": llm.name,
        "llm_model": llm.model,
        "llm_calls": calls,
    }


def _contexts(hits: List[Hit]) -> List[Dict]:
    return [
        {"doc_id": d.metadata["doc_id"], "source": d.metadata["source"], "page": d.metadata["page"],
         "chunk_id": d.metadata.get("chunk_id", ""), "score": round(s, 4), "text": d.page_content}
        for d, s in hits
    ]


def _sources(hits: List[Hit]) -> List[Dict]:
    """One source entry per (file, page), keeping the best score."""
    best: Dict[Tuple[str, int], Dict] = {}
    for d, s in hits:
        key = (d.metadata["doc_id"], d.metadata["page"])
        if key not in best or s > best[key]["score"]:
            best[key] = {
                "doc_id": d.metadata["doc_id"], "source": d.metadata["source"],
                "page": d.metadata["page"], "score": round(s, 4),
                "snippet": d.page_content[:240].replace("\n", " ") + ("..." if len(d.page_content) > 240 else ""),
            }
    return sorted(best.values(), key=lambda x: -x["score"])


class RAGService:
    def __init__(self, store: VectorStoreManager, llm: LLMProvider) -> None:
        self.store = store
        self.llm = llm

    def _require_docs(self, doc_ids: Optional[List[str]]) -> None:
        if not self.store.registry:
            raise NotFound("No documents uploaded yet. Upload at least one PDF first.")
        for d in doc_ids or []:
            if d not in self.store.registry:
                raise NotFound(f"Document not found: {d}")

    def _retrieve(self, query: str, top_k: int, doc_ids: Optional[List[str]]) -> List[Hit]:
        try:
            return self.store.search(query, top_k, doc_ids)
        except Exception as exc:
            logger.exception("Retrieval failed")
            raise RetrievalError("Could not search the document index. Check the server logs.") from exc

    # ---------- semantic search ----------
    def search(self, query: str, top_k: int, doc_ids: Optional[List[str]]) -> Dict:
        self._require_docs(doc_ids)
        t0 = time.perf_counter()
        hits = self._retrieve(query, top_k, doc_ids)
        t_ret = time.perf_counter() - t0
        return {
            "results": _contexts(hits),
            "diagnostics": _diagnostics(hits, top_k, t_ret, 0, t_ret, self.llm, 0),
        }

    # ---------- question answering ----------
    def ask(self, question: str, top_k: int, doc_ids: Optional[List[str]]) -> Dict:
        self._require_docs(doc_ids)
        t0 = time.perf_counter()
        hits = self._retrieve(question, top_k, doc_ids)
        t_ret = time.perf_counter() - t0
        if not hits:
            raise NotFound("No relevant content found.")
        prompt = f"Context:\n{_fmt_context(hits)}\n\nQuestion: {question}\n\nAnswer:"
        t1 = time.perf_counter()
        answer = self.llm.generate(prompt, system=ASK_SYSTEM)
        t_gen = time.perf_counter() - t1
        return {
            "answer": answer,
            "sources": _sources(hits),
            "contexts": _contexts(hits),
            "diagnostics": _diagnostics(hits, top_k, t_ret, t_gen, time.perf_counter() - t0,
                                        self.llm, 1),
        }

    # ---------- multi-paper comparison ----------
    def compare(self, doc_ids: List[str], question: str, top_k: int) -> Dict:
        self._require_docs(doc_ids)
        t0 = time.perf_counter()
        all_hits: List[Hit] = []
        blocks = []
        for did in doc_ids:
            hits = self._retrieve(question, top_k, [did])
            all_hits.extend(hits)
            name = self.store.registry[did]["filename"]
            blocks.append(f"=== PAPER: {name} ===\n{_fmt_context(hits)}")
        t_ret = time.perf_counter() - t0
        names = ", ".join(self.store.registry[d]["filename"] for d in doc_ids)
        system = (
            "You are ResearchLens, an expert at comparing research papers. Use ONLY the provided excerpts. "
            "Cite evidence as [filename, p.N]. If a paper's excerpts do not cover a point, say 'not covered in retrieved text'."
        )
        prompt = (
            f"Papers: {names}\n\n" + "\n\n".join(blocks) +
            f"\n\nTask: {question}\n\nProduce a Markdown comparison with: a short overview per paper, "
            "a comparison table (objective, method, data, results, limitations), key similarities, "
            "key differences, and a concluding takeaway."
        )
        t1 = time.perf_counter()
        answer = self.llm.generate(prompt, system=system, temperature=0.3)
        t_gen = time.perf_counter() - t1
        return {
            "answer": answer,
            "sources": _sources(all_hits),
            "contexts": _contexts(all_hits),
            "diagnostics": _diagnostics(all_hits, top_k, t_ret, t_gen, time.perf_counter() - t0,
                                        self.llm, 1),
        }

    # ---------- summarization (map-reduce for long papers) ----------
    def summarize(self, doc_id: str, style: str) -> Dict:
        self._require_docs([doc_id])
        meta = self.store.registry[doc_id]
        t0 = time.perf_counter()
        chunks = self.store.get_document_chunks(doc_id)
        if not chunks:
            raise NotFound("Document has no content.")
        if len(chunks) > MAX_CHUNKS:  # evenly sample to bound cost
            step = len(chunks) / MAX_CHUNKS
            chunks = [chunks[int(i * step)] for i in range(MAX_CHUNKS)]
        hits: List[Hit] = [(c, 1.0) for c in chunks]
        t_ret = time.perf_counter() - t0

        system = "You are ResearchLens. Summarize research papers faithfully; never add information not in the text."
        instruction = SUMMARY_STYLES[style]
        calls = 0
        t1 = time.perf_counter()
        batches = [chunks[i:i + BATCH_SIZE] for i in range(0, len(chunks), BATCH_SIZE)]
        if len(batches) == 1:
            text = "\n\n".join(f"[p.{c.metadata['page']}]\n{c.page_content}" for c in batches[0])
            answer = self.llm.generate(f"Paper: {meta['filename']}\n\n{text}\n\n{instruction}", system=system)
            calls = 1
        else:
            partials = []
            for b in batches:
                text = "\n\n".join(f"[p.{c.metadata['page']}]\n{c.page_content}" for c in b)
                partials.append(self.llm.generate(
                    f"Summarize the key content of this section of '{meta['filename']}' in 120-180 words:\n\n{text}",
                    system=system))
                calls += 1
            joined = "\n\n".join(f"Section {i + 1}: {p}" for i, p in enumerate(partials))
            answer = self.llm.generate(
                f"Paper: {meta['filename']}\n\nSection summaries:\n{joined}\n\n{instruction}", system=system)
            calls += 1
        t_gen = time.perf_counter() - t1
        return {
            "answer": answer,
            "sources": [{"doc_id": doc_id, "source": meta["filename"], "page": p, "score": 1.0, "snippet": ""}
                        for p in sorted({c.metadata["page"] for c in chunks})],
            "contexts": [],
            "diagnostics": _diagnostics(hits, len(chunks), t_ret, t_gen, time.perf_counter() - t0,
                                        self.llm, calls),
        }
