const BASE = import.meta.env.VITE_API_URL || "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
      if (Array.isArray(detail)) {
        detail = detail.map((d) => (d.error ? `${d.filename}: ${d.error}` : d.msg || JSON.stringify(d))).join("; ");
      }
    } catch { /* non-JSON error body */ }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

const post = (path, body) =>
  request(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

export const api = {
  health: () => request("/health"),
  listDocuments: () => request("/documents"),
  upload: (files, chunkSize, chunkOverlap) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    form.append("chunk_size", chunkSize);
    form.append("chunk_overlap", chunkOverlap);
    return request("/documents", { method: "POST", body: form });
  },
  deleteDocument: (id) => request(`/documents/${id}`, { method: "DELETE" }),
  clearDocuments: () => request("/documents", { method: "DELETE" }),
  ask: (question, topK, docIds) => post("/ask", { question, top_k: topK, doc_ids: docIds?.length ? docIds : null }),
  compare: (docIds, question, topK) => post("/compare", { doc_ids: docIds, question, top_k: topK }),
  summarize: (docId, style) => post("/summarize", { doc_id: docId, style }),
  search: (query, topK, docIds) => post("/search", { query, top_k: topK, doc_ids: docIds?.length ? docIds : null }),
};
