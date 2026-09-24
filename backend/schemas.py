from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

import config


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    pages: int
    chunks: int
    chunk_size: int
    chunk_overlap: int
    uploaded_at: float


class UploadResult(BaseModel):
    uploaded: List[DocumentInfo]
    errors: List[Dict[str, str]] = []


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=config.DEFAULT_TOP_K, ge=1, le=20)
    doc_ids: Optional[List[str]] = None


class CompareRequest(BaseModel):
    doc_ids: List[str] = Field(min_length=2)
    question: str = "Compare these papers: objectives, methodology, results, strengths and limitations."
    top_k: int = Field(default=config.DEFAULT_TOP_K, ge=1, le=20)


class SummarizeRequest(BaseModel):
    doc_id: str
    style: Literal["concise", "detailed", "key_points"] = "concise"


class SearchRequest(BaseModel):
    query: str = Field(min_length=2)
    top_k: int = Field(default=config.DEFAULT_TOP_K, ge=1, le=20)
    doc_ids: Optional[List[str]] = None


class Source(BaseModel):
    doc_id: str
    source: str
    page: int
    score: float
    snippet: str


class ContextChunk(BaseModel):
    doc_id: str
    source: str
    page: int
    chunk_id: str = ""
    score: float
    text: str


class Diagnostics(BaseModel):
    retrieval_ms: float = 0
    generation_ms: float = 0
    total_ms: float = 0
    top_k: int = 0
    chunks_retrieved: int = 0
    avg_score: float = 0
    max_score: float = 0
    min_score: float = 0
    documents_hit: List[str] = []
    context_chars: int = 0
    embedding_model: str = ""
    llm_provider: str = ""
    llm_model: str = ""
    llm_calls: int = 0


class RAGResponse(BaseModel):
    answer: str
    sources: List[Source]
    contexts: List[ContextChunk]
    diagnostics: Diagnostics


class SearchResponse(BaseModel):
    results: List[ContextChunk]
    diagnostics: Diagnostics
