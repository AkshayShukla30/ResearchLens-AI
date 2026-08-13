import streamlit as st

DEFAULT_SETTINGS = {
    "top_k": 6,
    "chunk_size": 800,
    "chunk_overlap": 150,
}

def init_state():
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("settings", DEFAULT_SETTINGS.copy())
    st.session_state.setdefault("pending_query", None)

def clear_conversation():
    st.session_state.messages = []
    st.session_state.pending_query = None
