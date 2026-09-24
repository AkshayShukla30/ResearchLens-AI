import { useRef, useState } from "react";

export default function Sidebar({ docs, selected, setSelected, settings, setSettings, onUpload, onDelete, onClear, busy, health }) {
  const input = useRef(null);
  const [drag, setDrag] = useState(false);

  const toggle = (id) =>
    setSelected(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);

  const handleFiles = (list) => {
    const files = [...list].filter((f) => f.name.toLowerCase().endsWith(".pdf"));
    if (files.length) onUpload(files);
  };

  const set = (k) => (e) => setSettings({ ...settings, [k]: Number(e.target.value) });

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">R</span>
        <div>
          <h1>ResearchLens</h1>
          <p>Read papers with evidence</p>
        </div>
      </div>

      <section>
        <h2>Library</h2>
        <div
          className={`drop ${drag ? "drag" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); handleFiles(e.dataTransfer.files); }}
          onClick={() => input.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && input.current?.click()}
        >
          <strong>{busy === "upload" ? "Indexing papers…" : "Add PDFs"}</strong>
          <span>Drop files here or click to browse</span>
          <input ref={input} type="file" accept="application/pdf" multiple hidden
                 onChange={(e) => { handleFiles(e.target.files); e.target.value = ""; }} />
        </div>

        {docs.length === 0 ? (
          <p className="muted small">No papers yet. Add a PDF to begin.</p>
        ) : (
          <ul className="doclist">
            {docs.map((d) => (
              <li key={d.doc_id} className={selected.includes(d.doc_id) ? "on" : ""}>
                <label>
                  <input type="checkbox" checked={selected.includes(d.doc_id)} onChange={() => toggle(d.doc_id)} />
                  <span className="docname" title={d.filename}>{d.filename}</span>
                </label>
                <span className="docmeta">{d.pages} pages, {d.chunks} chunks</span>
                <button className="icon" aria-label={`Remove ${d.filename}`} onClick={() => onDelete(d.doc_id)}>×</button>
              </li>
            ))}
          </ul>
        )}
        {docs.length > 0 && (
          <div className="row-between">
            <button className="link" onClick={() => setSelected(selected.length === docs.length ? [] : docs.map((d) => d.doc_id))}>
              {selected.length === docs.length ? "Clear selection" : "Select all"}
            </button>
            <button className="link danger" onClick={onClear}>Remove all</button>
          </div>
        )}
        <p className="muted small">
          {selected.length === 0 ? "Questions search every paper." : `Questions search ${selected.length} selected paper${selected.length > 1 ? "s" : ""}.`}
        </p>
      </section>

      <section>
        <h2>Retrieval settings</h2>
        <label className="field">
          <span>Top-K chunks <b>{settings.topK}</b></span>
          <input type="range" min="1" max="15" value={settings.topK} onChange={set("topK")} />
        </label>
        <label className="field">
          <span>Chunk size <b>{settings.chunkSize}</b></span>
          <input type="range" min="300" max="2000" step="100" value={settings.chunkSize} onChange={set("chunkSize")} />
        </label>
        <label className="field">
          <span>Chunk overlap <b>{settings.chunkOverlap}</b></span>
          <input type="range" min="0" max="400" step="25" value={settings.chunkOverlap} onChange={set("chunkOverlap")} />
        </label>
        <p className="muted small">Chunk size and overlap apply to papers you add next.</p>
      </section>

      {health && (
        <footer className="muted small">
          <div>LLM: {health.llm_provider}{health.llm_model && ` / ${health.llm_model}`}</div>
          <div>Embeddings: {health.embedding_model.split("/").pop()}</div>
          {health.llm_error && <div className="warn">{health.llm_error}</div>}
          {!health.llm_error && !health.llm_configured && (
            <div className="warn">API key for {health.llm_provider} is missing on the server.</div>
          )}
        </footer>
      )}
    </aside>
  );
}
