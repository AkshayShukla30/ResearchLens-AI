import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function Answer({ text }) {
  return (
    <article className="answer">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
    </article>
  );
}

export function Sources({ sources }) {
  if (!sources?.length) return null;
  return (
    <section className="block">
      <h3>Sources</h3>
      <ul className="sources">
        {sources.map((s) => (
          <li key={`${s.doc_id}-${s.page}`}>
            <div className="src-head">
              <span className="cite">{s.source}, p.{s.page}</span>
              {s.score < 1 && <span className="score">match {(s.score * 100).toFixed(0)}%</span>}
            </div>
            {s.snippet && <p>{s.snippet}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function Contexts({ contexts, title = "Retrieved context" }) {
  const [open, setOpen] = useState(false);
  if (!contexts?.length) return null;
  return (
    <section className="block">
      <button className="disclose" aria-expanded={open} onClick={() => setOpen(!open)}>
        {open ? "Hide" : "Show"} {title.toLowerCase()} ({contexts.length} chunks)
      </button>
      {open && (
        <ol className="contexts">
          {contexts.map((c, i) => (
            <li key={i}>
              <div className="src-head">
                <span className="cite">{c.source}, p.{c.page}</span>
                <span className="score">match {(c.score * 100).toFixed(0)}%</span>
              </div>
              <pre>{c.text}</pre>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

export function Diagnostics({ d }) {
  const [open, setOpen] = useState(false);
  if (!d) return null;
  const rows = [
    ["Retrieval time", `${d.retrieval_ms} ms`],
    ["Generation time", d.generation_ms ? `${d.generation_ms} ms` : "n/a"],
    ["Total time", `${d.total_ms} ms`],
    ["Chunks retrieved", `${d.chunks_retrieved} of ${d.top_k}`],
    ["Similarity avg / max / min", `${d.avg_score} / ${d.max_score} / ${d.min_score}`],
    ["Context size", `${d.context_chars.toLocaleString()} characters`],
    ["LLM calls", d.llm_calls],
    ["Papers hit", d.documents_hit.join(", ") || "none"],
    ["Embedding model", d.embedding_model],
    ["LLM", [d.llm_provider, d.llm_model].filter(Boolean).join(" / ")],
  ];
  return (
    <section className="block">
      <button className="disclose" aria-expanded={open} onClick={() => setOpen(!open)}>
        {open ? "Hide" : "Show"} retrieval diagnostics
      </button>
      {open && (
        <dl className="diag">
          {rows.map(([k, v]) => (
            <div key={k}><dt>{k}</dt><dd>{String(v)}</dd></div>
          ))}
        </dl>
      )}
    </section>
  );
}

export function RagResult({ data }) {
  if (!data) return null;
  return (
    <div className="result">
      <Answer text={data.answer} />
      <Sources sources={data.sources} />
      <Contexts contexts={data.contexts} />
      <Diagnostics d={data.diagnostics} />
    </div>
  );
}
