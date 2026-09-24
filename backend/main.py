"""ResearchLens AI - FastAPI backend (also serves the built React frontend)."""
import logging
import uuid
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import config
from core.chunker import chunk_pages
from core.pdf_loader import PDFError, extract_pages
from core.vector_store import VectorStoreManager
from llm import (LLMConfigError, LLMError, LLMRateLimitError, LLMTimeoutError,
                 get_llm_provider)
from schemas import (AskRequest, CompareRequest, DocumentInfo, RAGResponse, SearchRequest,
                     SearchResponse, SummarizeRequest, UploadResult)
from services.rag_service import NotFound, RAGService, RetrievalError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="ResearchLens AI", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])

_store: Optional[VectorStoreManager] = None
_service: Optional[RAGService] = None


def get_store() -> VectorStoreManager:
    global _store
    if _store is None:
        _store = VectorStoreManager()
    return _store


def get_service() -> RAGService:
    global _service
    if _service is None:
        _service = RAGService(get_store(), get_llm_provider())
    return _service


def _error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": message})


@app.exception_handler(NotFound)
def _not_found(_: Request, exc: NotFound):
    return _error(404, str(exc))


@app.exception_handler(LLMError)
def _llm_error(_: Request, exc: LLMError):
    if isinstance(exc, LLMConfigError):
        status = 503
    elif isinstance(exc, LLMRateLimitError):
        status = 429
    elif isinstance(exc, LLMTimeoutError):
        status = 504
    else:
        status = 502
    return _error(status, str(exc))


@app.exception_handler(RetrievalError)
def _retrieval_error(_: Request, exc: RetrievalError):
    return _error(500, str(exc))


@app.exception_handler(Exception)
def _unexpected(_: Request, exc: Exception):
    logger.exception("Unhandled error")
    return _error(500, "Something went wrong on the server. Check the server logs.")


@app.get("/api/health")
def health():
    try:
        llm = get_service().llm
        llm_info = {"llm_provider": llm.name, "llm_model": llm.model, "llm_configured": llm.is_configured}
    except LLMConfigError as exc:
        llm_info = {"llm_provider": config.LLM_PROVIDER, "llm_model": "", "llm_configured": False,
                    "llm_error": str(exc)}
    return {
        "status": "ok",
        **llm_info,
        "embedding_model": config.EMBEDDING_MODEL,
        "documents": len(get_store().registry),
        "defaults": {"chunk_size": config.DEFAULT_CHUNK_SIZE, "chunk_overlap": config.DEFAULT_CHUNK_OVERLAP,
                     "top_k": config.DEFAULT_TOP_K},
    }


@app.post("/api/documents", response_model=UploadResult)
def upload_documents(
    files: List[UploadFile] = File(...),
    chunk_size: int = Form(config.DEFAULT_CHUNK_SIZE),
    chunk_overlap: int = Form(config.DEFAULT_CHUNK_OVERLAP),
):
    store = get_store()
    uploaded, errors = [], []
    for f in files:
        name = f.filename or "unnamed.pdf"
        try:
            if not name.lower().endswith(".pdf"):
                raise ValueError("Only PDF files are supported.")
            data = f.file.read()
            if len(data) > config.MAX_UPLOAD_MB * 1024 * 1024:
                raise ValueError(f"File exceeds {config.MAX_UPLOAD_MB} MB limit.")
            if any(m["filename"] == name for m in store.registry.values()):
                raise ValueError("A document with this name is already uploaded.")
            pages = extract_pages(data)
            doc_id = uuid.uuid4().hex[:12]
            chunks = chunk_pages(pages, doc_id, name, chunk_size, chunk_overlap)
            meta = store.add_document(doc_id, name, pages[0]["total_pages"], chunks, chunk_size, chunk_overlap)
            uploaded.append(meta)
        except (PDFError, ValueError) as exc:
            errors.append({"filename": name, "error": str(exc)})
        except Exception:
            logger.exception("Failed to index %s", name)
            errors.append({"filename": name, "error": "Could not index this file. Check the server logs."})
    if not uploaded and errors:
        raise HTTPException(400, errors)
    return {"uploaded": uploaded, "errors": errors}


@app.get("/api/documents", response_model=List[DocumentInfo])
def list_documents():
    return get_store().list_documents()


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    if not get_store().delete_document(doc_id):
        raise HTTPException(404, "Document not found")
    return {"deleted": doc_id}


@app.delete("/api/documents")
def clear_documents():
    get_store().clear()
    return {"cleared": True}


@app.post("/api/ask", response_model=RAGResponse)
def ask(req: AskRequest):
    return get_service().ask(req.question, req.top_k, req.doc_ids)


@app.post("/api/compare", response_model=RAGResponse)
def compare(req: CompareRequest):
    return get_service().compare(req.doc_ids, req.question, req.top_k)


@app.post("/api/summarize", response_model=RAGResponse)
def summarize(req: SummarizeRequest):
    return get_service().summarize(req.doc_id, req.style)


@app.post("/api/search", response_model=SearchResponse)
def search(req: SearchRequest):
    return get_service().search(req.query, req.top_k, req.doc_ids)


# ---- serve built frontend (production / Docker) ----
if (config.FRONTEND_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=config.FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        candidate = config.FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(config.FRONTEND_DIST / "index.html")
