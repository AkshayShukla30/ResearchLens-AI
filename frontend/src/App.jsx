import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import Sidebar from "./components/Sidebar.jsx";
import { AskPanel, ComparePanel, SearchPanel, SummarizePanel } from "./components/Panels.jsx";

const TABS = [
  ["ask", "Ask"],
  ["compare", "Compare"],
  ["summarize", "Summarize"],
  ["search", "Search"],
];

export default function App() {
  const [docs, setDocs] = useState([]);
  const [selected, setSelected] = useState([]);
  const [tab, setTab] = useState("ask");
  const [health, setHealth] = useState(null);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState({ kind: "", text: "" });
  const [settings, setSettings] = useState({ topK: 5, chunkSize: 1000, chunkOverlap: 150 });

  const refresh = useCallback(async () => {
    const list = await api.listDocuments();
    setDocs(list);
    setSelected((s) => s.filter((id) => list.some((d) => d.doc_id === id)));
  }, []);

  useEffect(() => {
    refresh().catch((e) => setNotice({ kind: "error", text: `Cannot reach the server: ${e.message}` }));
    api.health().then((h) => {
      setHealth(h);
      setSettings({ topK: h.defaults.top_k, chunkSize: h.defaults.chunk_size, chunkOverlap: h.defaults.chunk_overlap });
    }).catch(() => {});
  }, [refresh]);

  const onUpload = async (files) => {
    setBusy("upload"); setNotice({ kind: "", text: "" });
    try {
      const res = await api.upload(files, settings.chunkSize, settings.chunkOverlap);
      const errs = res.errors.map((e) => `${e.filename}: ${e.error}`).join("; ");
      setNotice({ kind: errs ? "error" : "ok", text: `Added ${res.uploaded.length} paper(s).${errs ? " Skipped: " + errs : ""}` });
      await refresh();
    } catch (e) {
      setNotice({ kind: "error", text: e.message });
    } finally { setBusy(""); }
  };

  const onDelete = async (id) => { await api.deleteDocument(id); await refresh(); };
  const onClear = async () => {
    if (window.confirm("Remove all papers from the library?")) { await api.clearDocuments(); setSelected([]); await refresh(); }
  };

  const shared = { docs, selected, settings };
  return (
    <div className="layout">
      <Sidebar docs={docs} selected={selected} setSelected={setSelected} settings={settings}
               setSettings={setSettings} onUpload={onUpload} onDelete={onDelete} onClear={onClear}
               busy={busy} health={health} />
      <main>
        {notice.text && <div className={`notice ${notice.kind}`} role="status">{notice.text}</div>}
        <nav className="tabs" role="tablist">
          {TABS.map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>
              {label}
            </button>
          ))}
        </nav>
        <div className="content">
          {tab === "ask" && <AskPanel {...shared} />}
          {tab === "compare" && <ComparePanel {...shared} />}
          {tab === "summarize" && <SummarizePanel {...shared} />}
          {tab === "search" && <SearchPanel {...shared} />}
        </div>
      </main>
    </div>
  );
}
