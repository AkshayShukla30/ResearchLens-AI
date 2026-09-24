from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from src.ingestion.pdf_processor import extract_pdf
from src.retrieval.vector_store import VectorStore


class DocumentService:
    def __init__(self, upload_dir: Path, index_dir: Path, metadata_file: Path):
        self.upload_dir = Path(upload_dir)
        self.index_dir = Path(index_dir)
        self.metadata_file = Path(metadata_file)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        self.store = VectorStore(self.index_dir)

    def _read_meta(self) -> List[Dict[str, Any]]:
        if not self.metadata_file.exists():
            return []
        try:
            return json.loads(self.metadata_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _write_meta(self, data: List[Dict[str, Any]]) -> None:
        self.metadata_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_documents(self) -> List[Dict[str, Any]]:
        return self._read_meta()

    def has_index(self) -> bool:
        return self.store.exists()

    def add_uploaded_files(self, uploaded_files, settings: Dict[str, int]) -> Dict[str, list]:
        existing = {d["filename"] for d in self._read_meta()}
        added, errors = [], []
        for uploaded in uploaded_files:
            safe_name = Path(uploaded.name).name
            path = self.upload_dir / safe_name
            try:
                path.write_bytes(uploaded.getbuffer())
                chunks, pages = extract_pdf(path, settings["chunk_size"], settings["chunk_overlap"])
                if not chunks:
                    raise ValueError("No extractable text was found. Scanned/image-only PDFs need OCR support.")
                existing.discard(safe_name)
                added.append({"filename": safe_name, "pages": pages, "chunks": len(chunks), "status": "ready"})
            except Exception as exc:
                errors.append(f"{safe_name}: {exc}")

        # Preserve documents not re-uploaded, then rebuild using all files.
        current = [d for d in self._read_meta() if d["filename"] in {p.name for p in self.upload_dir.glob("*.pdf")}]
        by_name = {d["filename"]: d for d in current}
        for item in added:
            by_name[item["filename"]] = item
        self._write_meta(list(by_name.values()))

        if added:
            self.rebuild_index(settings)
        return {"added": added, "errors": errors}

    def _all_chunks(self, settings: Dict[str, int]):
        all_chunks = []
        for path in sorted(self.upload_dir.glob("*.pdf")):
            chunks, _ = extract_pdf(path, settings["chunk_size"], settings["chunk_overlap"])
            all_chunks.extend(chunks)
        return all_chunks

    def rebuild_index(self, settings: Dict[str, int]) -> None:
        chunks = self._all_chunks(settings)
        if chunks:
            self.store.build(chunks)
        else:
            shutil.rmtree(self.index_dir, ignore_errors=True)

        metadata = []
        for path in sorted(self.upload_dir.glob("*.pdf")):
            try:
                chunks, pages = extract_pdf(path, settings["chunk_size"], settings["chunk_overlap"])
                metadata.append({
                    "filename": path.name,
                    "pages": pages,
                    "chunks": len(chunks),
                    "status": "ready" if chunks else "error",
                })
            except Exception as exc:
                metadata.append({"filename": path.name, "pages": 0, "chunks": 0, "status": f"error: {exc}"})
        self._write_meta(metadata)

    def delete_document(self, filename: str, settings: Dict[str, int]) -> None:
        path = self.upload_dir / Path(filename).name
        if path.exists():
            path.unlink()
        self.rebuild_index(settings)

    def clear_all(self) -> None:
        for path in self.upload_dir.glob("*.pdf"):
            path.unlink()
        shutil.rmtree(self.index_dir, ignore_errors=True)
        self._write_meta([])
