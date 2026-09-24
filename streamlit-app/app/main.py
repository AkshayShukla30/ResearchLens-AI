from __future__ import annotations

import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

from src.services.document_service import DocumentService
from src.services.rag_service import RAGService
from src.services.chat_service import ChatService
from src.services.summary_service import SummaryService
from src.utils.state import init_state, clear_conversation
from src.utils.ui import inject_css, render_brand, render_source_cards, render_retrieved_chunks

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = ROOT / "data" / "uploads"
INDEX_DIR = ROOT / "data" / "vector_index"
META_FILE = ROOT / "data" / "documents.json"

st.set_page_config(
    page_title="ResearchLens AI",
    page_icon="RL",
    layout="wide",
    initial_sidebar_state="expanded",
)

def _llm_config():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    return model, api_key

def run():
    inject_css()
    init_state()

    doc_service = DocumentService(UPLOAD_DIR, INDEX_DIR, META_FILE)
    model, gemini_key = _llm_config()

    with st.sidebar:
        render_brand()
        st.divider()

        st.subheader("Add research papers")
        uploads = st.file_uploader(
            "Upload one or more PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if st.button("Process selected papers", type="primary", use_container_width=True):
            if not uploads:
                st.warning("Select at least one PDF.")
            else:
                result = doc_service.add_uploaded_files(uploads, st.session_state.settings)
                if result["errors"]:
                    for error in result["errors"]:
                        st.error(error)
                if result["added"]:
                    st.success(f"Processed {len(result['added'])} paper(s).")
                st.rerun()

        docs = doc_service.list_documents()
        st.caption(f"{len(docs)} paper(s) in your research library")

        st.divider()
        st.subheader("Retrieval settings")
        st.session_state.settings["top_k"] = st.slider(
            "Top-K", 2, 15, st.session_state.settings["top_k"]
        )
        st.session_state.settings["chunk_size"] = st.slider(
            "Chunk size", 400, 1600, st.session_state.settings["chunk_size"], step=100
        )
        st.session_state.settings["chunk_overlap"] = st.slider(
            "Chunk overlap", 50, 400, st.session_state.settings["chunk_overlap"], step=50
        )
        st.caption("Changing chunk settings applies to the next index rebuild.")

        st.divider()
        if st.button("New conversation", use_container_width=True):
            clear_conversation()
            st.rerun()
        if st.button("Clear all documents", use_container_width=True):
            doc_service.clear_all()
            clear_conversation()
            st.rerun()

    st.markdown(
        '<div class="eyebrow">RESEARCH WORKSPACE</div>'
        '<h1>ResearchLens AI</h1>'
        '<p class="subtitle">AI-Powered Research Paper Assistant</p>',
        unsafe_allow_html=True,
    )

    docs = doc_service.list_documents()
    if not docs:
        st.markdown(
            '<div class="hero-card">'
            '<div class="hero-kicker">READ • SEARCH • COMPARE</div>'
            '<h2>Turn a folder of papers into a research workspace.</h2>'
            '<p>Upload papers, ask grounded questions, inspect retrieved evidence, and compare findings across documents.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(3)
        for col, title, body in zip(
            cols,
            ["Ask grounded questions", "Inspect evidence", "Compare papers"],
            ["Answers are generated from retrieved paper content.",
             "Every answer exposes document and page metadata when available.",
             "Use one query across your entire uploaded research library."],
        ):
            with col:
                st.markdown(f'<div class="feature-card"><b>{title}</b><p>{body}</p></div>', unsafe_allow_html=True)
        return

    active_names = [d["filename"] for d in docs if d.get("status") == "ready"]
    st.markdown(
        f'<div class="library-strip"><b>{len(active_names)} active paper(s)</b>'
        f'<span>Ask about one paper or compare the whole library.</span></div>',
        unsafe_allow_html=True,
    )

    tab_chat, tab_library, tab_summary, tab_eval = st.tabs(
        ["Research Chat", "Paper Library", "Summaries", "Retrieval Diagnostics"]
    )

    with tab_library:
        st.subheader("Paper library")
        for doc in docs:
            c1, c2, c3, c4 = st.columns([4, 1.1, 1.1, 1.1])
            with c1:
                st.markdown(f"**{doc['filename']}**")
                st.caption(
                    f"{doc.get('pages', 0)} pages · {doc.get('chunks', 0)} chunks · {doc.get('status', 'unknown')}"
                )
            with c2:
                if st.button("Rebuild", key=f"rebuild_{doc['filename']}"):
                    doc_service.rebuild_index(st.session_state.settings)
                    st.success("Index rebuilt.")
                    st.rerun()
            with c3:
                if st.button("Delete", key=f"delete_{doc['filename']}"):
                    doc_service.delete_document(doc["filename"], st.session_state.settings)
                    st.rerun()
            with c4:
                st.write("Ready" if doc.get("status") == "ready" else "Needs attention")

    with tab_chat:
        st.subheader("Ask your research papers")
        suggestions = [
            "What is the main contribution of this paper?",
            "What dataset was used and how was it evaluated?",
            "What methodology was proposed?",
            "What are the key results and limitations?",
            "Compare the methodologies of these papers.",
        ]
        prompt_col = st.columns(3)
        for i, question in enumerate(suggestions[:3]):
            with prompt_col[i]:
                if st.button(question, key=f"suggest_{i}", use_container_width=True):
                    st.session_state.pending_query = question

        if len(suggestions) > 3:
            prompt_col2 = st.columns(2)
            for i, question in enumerate(suggestions[3:], start=3):
                with prompt_col2[i - 3]:
                    if st.button(question, key=f"suggest_{i}", use_container_width=True):
                        st.session_state.pending_query = question

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant":
                    render_source_cards(message.get("sources", []))
                    if message.get("chunks"):
                        with st.expander("Retrieved context"):
                            render_retrieved_chunks(message["chunks"])

        pending = st.session_state.pop("pending_query", None)
        query = st.chat_input("Ask a question about your research papers...")
        query = query or pending

        if query:
            if not doc_service.has_index():
                st.warning("Your papers are uploaded but the vector index is not ready. Rebuild the index.")
                return
            if not gemini_key:
                st.error("GEMINI_API_KEY is missing. Add your Google Gemini API key to .env.")
                return

            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)

            with st.chat_message("assistant"):
                with st.spinner("Searching the research library..."):
                    rag = RAGService(doc_service, st.session_state.settings)
                    try:
                        retrieved, retrieval_ms = rag.retrieve(query)
                        chat = ChatService(gemini_key, model)
                        answer = chat.answer(query, retrieved, st.session_state.messages[:-1])
                        sources = rag.build_sources(retrieved)
                        st.markdown(answer)
                        render_source_cards(sources)
                        with st.expander("Retrieved context"):
                            render_retrieved_chunks(retrieved)
                        st.caption(f"Retrieved {len(retrieved)} chunks in {retrieval_ms:.0f} ms.")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources,
                            "chunks": retrieved,
                            "retrieval_ms": retrieval_ms,
                        })
                    except Exception as exc:
                        st.error(f"Unable to answer this question: {exc}")

    with tab_summary:
        st.subheader("Paper summary")
        choices = [d["filename"] for d in docs if d.get("status") == "ready"]
        if not choices:
            st.info("No ready papers available.")
        else:
            selected = st.selectbox("Select a paper", choices)
            if st.button("Generate research summary", type="primary"):
                with st.spinner("Preparing summary from the paper..."):
                    try:
                        rag = RAGService(doc_service, st.session_state.settings)
                        content = rag.document_content(selected)
                        chat = ChatService(gemini_key, model)
                        summary = SummaryService(chat).summarize(selected, content)
                        st.markdown(summary)
                    except Exception as exc:
                        st.error(f"Could not generate the summary: {exc}")

    with tab_eval:
        st.subheader("Retrieval diagnostics")
        if st.session_state.messages:
            assistant_messages = [m for m in st.session_state.messages if m["role"] == "assistant"]
            if assistant_messages:
                last = assistant_messages[-1]
                chunks = last.get("chunks", [])
                cols = st.columns(4)
                cols[0].metric("Retrieved chunks", len(chunks))
                cols[1].metric("Retrieval latency", f"{last.get('retrieval_ms', 0):.0f} ms")
                cols[2].metric("Unique papers", len({c.get("source") for c in chunks}))
                cols[3].metric("Pages represented", len({(c.get("source"), c.get("page")) for c in chunks}))
                st.caption("FAISS distances are shown below when available; lower distance means closer vector similarity. These are retrieval diagnostics, not benchmark accuracy metrics.")
                render_retrieved_chunks(chunks)
            else:
                st.info("Ask a question to populate retrieval diagnostics.")
        else:
            st.info("Ask a question to populate retrieval diagnostics.")
