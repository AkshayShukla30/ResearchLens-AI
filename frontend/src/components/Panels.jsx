import { useState } from "react";
import { api } from "../api.js";
import { Contexts, Diagnostics, RagResult } from "./Results.jsx";

function useRunner() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);
  const run = async (fn) => {
    setLoading(true); setError(""); setData(null);
    try { setData(await fn()); } catch (e) { setError(e.message); } finally { setLoading(false); }
  };
  return { loading, error, data, run };
}

const Status = ({ loading, error, label }) => (
  <>
    {loading && <p className="status" role="status">{label}</p>}
    {error && <p className="error" role="alert">{error}</p>}
  </>
);

export function AskPanel({ docs, selected, settings }) {
  const [q, setQ] = useState("");
  const { loading, error, data, run } = useRunner();
  const submit = (e) => { e.preventDefault(); if (q.trim().length > 2) run(() => api.ask(q, settings.topK, selected)); };
  return (
    <div>
      <p className="lede">Ask a question. Answers come only from the papers you added, with page citations.</p>
      <form onSubmit={submit} className="askbar">
        <textarea value={q} onChange={(e) => setQ(e.target.value)} rows={3} disabled={!docs.length}
                  placeholder={docs.length ? "What dataset was used, and how did the model perform?" : "Add a PDF first"}
                  onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit(e); }} />
        <button className="primary" disabled={loading || !docs.length || q.trim().length < 3}>Ask</button>
      </form>
      <Status loading={loading} error={error} label="Reading the papers…" />
      <RagResult data={data} />
    </div>
  );
}

export function ComparePanel({ docs, selected, settings }) {
  const [ids, setIds] = useState(null); // null = follow sidebar selection
  const [q, setQ] = useState("Compare these papers: objectives, methodology, results, strengths and limitations.");
  const { loading, error, data, run } = useRunner();
  const choose = ids ?? selected;
  const toggle = (id) => setIds(choose.includes(id) ? choose.filter((x) => x !== id) : [...choose, id]);
  return (
    <div>
      <p className="lede">Pick two or more papers and compare them side by side.</p>
      <fieldset className="picker">
        <legend>Papers to compare</legend>
        {docs.length < 2 && <p className="muted small">Add at least two papers to compare.</p>}
        {docs.map((d) => (
          <label key={d.doc_id} className={choose.includes(d.doc_id) ? "chip on" : "chip"}>
            <input type="checkbox" checked={choose.includes(d.doc_id)}
                   onChange={() => toggle(d.doc_id)} />
            {d.filename}
          </label>
        ))}
      </fieldset>
      <label className="field"><span>Focus of the comparison</span>
        <textarea rows={2} value={q} onChange={(e) => setQ(e.target.value)} />
      </label>
      <button className="primary" disabled={loading || choose.length < 2}
              onClick={() => run(() => api.compare(choose, q, settings.topK))}>
        Compare {choose.length >= 2 ? `${choose.length} papers` : ""}
      </button>
      <Status loading={loading} error={error} label="Comparing papers…" />
      <RagResult data={data} />
    </div>
  );
}

export function SummarizePanel({ docs, selected }) {
  const [docId, setDocId] = useState("");
  const [style, setStyle] = useState("concise");
  const { loading, error, data, run } = useRunner();
  const current = docId || selected[0] || docs[0]?.doc_id || "";
  return (
    <div>
      <p className="lede">Summarize a whole paper. Long papers are summarized section by section, then merged.</p>
      <div className="grid2">
        <label className="field"><span>Paper</span>
          <select value={current} onChange={(e) => setDocId(e.target.value)} disabled={!docs.length}>
            {docs.map((d) => <option key={d.doc_id} value={d.doc_id}>{d.filename}</option>)}
          </select>
        </label>
        <label className="field"><span>Style</span>
          <select value={style} onChange={(e) => setStyle(e.target.value)}>
            <option value="concise">Concise</option>
            <option value="detailed">Detailed, by section</option>
            <option value="key_points">Key points</option>
          </select>
        </label>
      </div>
      <button className="primary" disabled={loading || !current} onClick={() => run(() => api.summarize(current, style))}>
        Summarize
      </button>
      <Status loading={loading} error={error} label="Summarizing…" />
      {data && (
        <div className="result">
          <RagResult data={{ ...data, sources: [], contexts: [] }} />
          <p className="muted small">Based on pages: {data.sources.map((s) => s.page).join(", ")}</p>
        </div>
      )}
    </div>
  );
}

export function SearchPanel({ docs, selected, settings }) {
  const [q, setQ] = useState("");
  const { loading, error, data, run } = useRunner();
  const submit = (e) => { e.preventDefault(); if (q.trim().length > 1) run(() => api.search(q, settings.topK, selected)); };
  return (
    <div>
      <p className="lede">Semantic search finds passages by meaning, without generating an answer.</p>
      <form onSubmit={submit} className="askbar single">
        <input value={q} onChange={(e) => setQ(e.target.value)} disabled={!docs.length}
               placeholder="e.g. limitations of the proposed approach" />
        <button className="primary" disabled={loading || !docs.length || q.trim().length < 2}>Search</button>
      </form>
      <Status loading={loading} error={error} label="Searching…" />
      {data && (
        <div className="result">
          {data.results.length === 0 && <p className="muted">No matching passages.</p>}
          <ol className="contexts open">
            {data.results.map((c, i) => (
              <li key={i}>
                <div className="src-head">
                  <span className="cite">{c.source}, p.{c.page}</span>
                  <span className="score">match {(c.score * 100).toFixed(0)}%</span>
                </div>
                <pre>{c.text}</pre>
              </li>
            ))}
          </ol>
          <Diagnostics d={data.diagnostics} />
        </div>
      )}
    </div>
  );
}
