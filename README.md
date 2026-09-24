# ResearchLens AI

### AI-Powered Research Paper Assistant

ResearchLens AI is a multi-PDF research assistant that helps users read, search, summarize, and compare research papers using Retrieval-Augmented Generation (RAG).

Upload research papers, ask questions, compare multiple papers, generate summaries, and inspect the sources used to generate answers — all grounded in the actual paper content with page-level citations.

This repository contains **two versions** of the project:
1. **Streamlit prototype** (`streamlit-app/`) — the original MVP, currently live
2. **Full-stack version** (`backend/` + `frontend/`) — FastAPI backend + React (Vite) frontend, built as a production-style evolution of the prototype

---

## Live Demo

🔗 [https://researchlensaii.streamlit.app/](https://researchlens-ai.streamlit.app/)
*(Streamlit prototype — see `streamlit-app/` for its code)*

## GitHub

https://github.com/AkshayShukla30/ResearchLens-AI

---

## Features

- Multi-PDF Upload
- Research Paper Q&A
- Multi-Paper Comparison
- Paper Summarization (concise / detailed / key points)
- Semantic Search
- Source & Page Citations
- Retrieved Context View
- Configurable Top-K Retrieval
- Configurable Chunk Size & Overlap
- Document Management (list / delete / clear)
- Dual LLM Support — switch between **Google Gemini** and **Groq** via a single config flag

---

## Tech Stack

**Streamlit Prototype** (`streamlit-app/`)
- Python, Streamlit, PyMuPDF, LangChain, HuggingFace Embeddings, FAISS, Google Gemini API

**Full-Stack Version** (`backend/` + `frontend/`)
- **Backend:** Python, FastAPI, PyMuPDF, LangChain, HuggingFace Embeddings, FAISS, Google Gemini API, Groq API
- **Frontend:** React (Vite), react-markdown

---

## RAG Pipeline

```
Research Papers (PDF)
      ↓
  PyMuPDF (text extraction)
      ↓
  Text Chunking (configurable size/overlap)
      ↓
HuggingFace Embeddings
      ↓
     FAISS Vector Store
      ↓
 Top-K Retrieval
      ↓
Retrieved Context + Page Citations
      ↓
LLM (Gemini or Groq — pluggable)
      ↓
Answer + Sources
```

---

## Project Structure

```
ResearchLens-AI/
│
├── streamlit-app/              # Original Streamlit prototype (live demo)
│   ├── app/
│   ├── src/
│   ├── data/
│   ├── app.py
│   ├── requirements.txt
│   └── streamlit.env.example
│
├── backend/                     # FastAPI backend (full-stack version)
│   ├── main.py                  # API routes + serves built frontend
│   ├── config.py                # Central env-based configuration
│   ├── schemas.py                # Pydantic request/response models
│   ├── llm/                      # Pluggable LLM providers
│   │   ├── base.py               # Common provider interface
│   │   ├── factory.py            # Provider selection (LLM_PROVIDER env)
│   │   ├── gemini.py
│   │   ├── groq.py
│   │   └── fake.py               # For offline tests
│   ├── core/
│   │   ├── pdf_loader.py         # PDF text extraction
│   │   ├── chunker.py            # Text chunking
│   │   ├── embeddings.py         # HuggingFace embeddings
│   │   └── vector_store.py       # FAISS vector store manager
│   ├── services/
│   │   └── rag_service.py        # Ask / compare / summarize / search logic
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                     # React + Vite frontend (full-stack version)
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── api.js
│   │   ├── styles.css
│   │   └── components/
│   │       ├── Sidebar.jsx
│   │       ├── Panels.jsx
│   │       └── Results.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── tests/
├── .gitignore
└── README.md
```

---

## Run Locally

### Option A — Streamlit Prototype

```bash
git clone https://github.com/AkshayShukla30/ResearchLens-AI.git
cd ResearchLens-AI/streamlit-app
pip install -r requirements.txt
```

Create a `.env` file inside `streamlit-app/`:
```
GEMINI_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-3.5-flash
```

Run the application:
```bash
streamlit run app.py
```

### Option B — Full-Stack Version (FastAPI + React)

**Backend:**
```bash
cd ResearchLens-AI/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` inside `backend/` and fill in the provider you want to use:
```
LLM_PROVIDER=gemini            # or "groq"

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

Run the backend:
```bash
uvicorn main:app --reload
```

**Frontend (in a new terminal):**
```bash
cd ResearchLens-AI/frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`, proxying API calls to the backend at `http://localhost:8000`.

### API Endpoints (backend)

| Method | Endpoint               | Description                        |
|--------|------------------------|-------------------------------------|
| GET    | `/api/health`          | Health check + current LLM config  |
| POST   | `/api/documents`       | Upload one or more PDFs            |
| GET    | `/api/documents`       | List uploaded documents            |
| DELETE | `/api/documents/{id}`  | Delete a document                  |
| DELETE | `/api/documents`       | Clear all documents                |
| POST   | `/api/ask`             | Ask a question                     |
| POST   | `/api/compare`         | Compare 2+ papers                  |
| POST   | `/api/summarize`       | Summarize a document               |
| POST   | `/api/search`          | Semantic search across documents   |

---

## Author

**Akshay Shukla**

**LinkedIn:** https://in.linkedin.com/in/akshayshukla-
**GitHub:** https://github.com/AkshayShukla30
