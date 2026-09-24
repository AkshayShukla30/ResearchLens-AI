import html
import streamlit as st

def inject_css():
    st.markdown(
        """
        <style>
        :root { --ink:#1f2937; --muted:#6b7280; --line:#e5e7eb; --paper:#ffffff; --accent:#315c72; }
        .stApp { background:#f7f8f9; }
        .block-container { max-width:1200px; padding-top:2.5rem; }
        [data-testid="stSidebar"] { background:#f0f3f4; border-right:1px solid #dde3e6; }
        h1 { color:var(--ink); font-weight:750; letter-spacing:-.035em; margin-bottom:0; }
        h2,h3 { color:var(--ink); }
        .eyebrow { color:var(--accent); font-size:.75rem; font-weight:750; letter-spacing:.14em; margin-bottom:.35rem; }
        .subtitle { color:var(--muted); font-size:1.05rem; margin-top:.15rem; }
        .hero-card { background:#fff; border:1px solid var(--line); border-radius:16px; padding:2rem; margin:1.5rem 0; box-shadow:0 8px 24px rgba(31,41,55,.05); }
        .hero-card h2 { font-size:2rem; margin:.35rem 0 .7rem; }
        .hero-card p { color:#59636e; max-width:760px; }
        .hero-kicker { font-size:.72rem; letter-spacing:.14em; color:var(--accent); font-weight:750; }
        .feature-card { background:#fff; border:1px solid var(--line); border-radius:14px; padding:1.2rem; min-height:130px; }
        .feature-card p { color:#66717b; font-size:.92rem; }
        .library-strip { display:flex; gap:14px; align-items:center; background:#fff; border:1px solid var(--line); border-radius:12px; padding:.8rem 1rem; margin:1rem 0 1.25rem; }
        .library-strip span { color:#737d86; }
        .source-card { background:#fbfcfc; border:1px solid #dce3e6; border-left:3px solid var(--accent); border-radius:10px; padding:.75rem .9rem; margin:.5rem 0; }
        .source-name { font-weight:700; color:#25313a; }
        .source-meta { color:#69747c; font-size:.84rem; }
        .chunk-card { background:#fafafa; border:1px solid #e4e7e9; border-radius:9px; padding:.75rem; margin:.5rem 0; }
        .chunk-meta { color:#68737b; font-size:.8rem; margin-bottom:.35rem; }
        [data-testid="stFileUploader"] { background:#fff; border:1px dashed #b8c5cb; border-radius:12px; padding:.4rem; }
        .stButton > button { border-radius:9px; font-weight:600; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_brand():
    st.markdown(
        '<div class="eyebrow">RESEARCH WORKSPACE</div>'
        '<h2 style="margin:0;">ResearchLens AI</h2>'
        '<div style="color:#68737b;font-size:.88rem;margin-top:.2rem;">AI-Powered Research Paper Assistant</div>',
        unsafe_allow_html=True,
    )

def render_source_cards(sources):
    if not sources:
        return
    with st.expander("Sources", expanded=False):
        for source in sources:
            page = f"Page {source['page']}" if source.get("page") else "Page metadata unavailable"
            st.markdown(
                f'<div class="source-card"><div class="source-name">{html.escape(source.get("source","Unknown"))}</div>'
                f'<div class="source-meta">{page} · {html.escape(source.get("context","Retrieved evidence"))}</div></div>',
                unsafe_allow_html=True,
            )

def render_retrieved_chunks(chunks):
    if not chunks:
        st.info("No chunks retrieved.")
        return
    for i, chunk in enumerate(chunks, start=1):
        page = chunk.get("page") if chunk.get("page") else "N/A"
        distance = chunk.get("distance")
        score = f"{distance:.4f}" if isinstance(distance, float) else "N/A"
        st.markdown(
            f'<div class="chunk-card"><div class="chunk-meta">'
            f'Chunk {i} · {html.escape(str(chunk.get("source","Unknown")))} · Page {page} · FAISS distance {score}'
            f'</div>{html.escape(chunk.get("text",""))}</div>',
            unsafe_allow_html=True,
        )
