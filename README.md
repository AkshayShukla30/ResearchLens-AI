# ResearchLens AI

**AI-Powered Research Paper Assistant**

ResearchLens AI is a portfolio-focused multi-PDF research assistant built with **Python + Streamlit + RAG**. It turns uploaded academic papers into a searchable research workspace where you can ask grounded questions, inspect retrieved evidence, summarize a paper, and compare information across documents.

## Problem Statement

Reading multiple research papers manually makes it difficult to quickly locate methodology details, datasets, results, limitations, and differences between approaches. ResearchLens AI provides a lightweight local workspace that uses retrieval-augmented generation to answer questions from the papers you upload.

## Features

- Multi-PDF upload and persistent local paper library
- Page-aware PDF extraction with PyMuPDF
- Configurable chunk size, overlap, and Top-K retrieval
- FAISS semantic search with HuggingFace embeddings
- Google Gemini API support
- Source citations with actual document/page metadata when available
- Expandable retrieved-context/debug view
- Paper document manager with status, pages, chunks, delete and rebuild
- Research-oriented question suggestions
- Paper summary: overview, contributions, methodology, results, limitations, conclusion
- Multi-paper comparison through a shared retrieval index
- Lightweight retrieval diagnostics: retrieved chunks, latency, document distribution and FAISS distance
- Session chat history
- No fake Precision/Recall evaluation metrics

## Architecture

```text
Streamlit UI
    |
    +--> Document Manager
    |      |
    |      +--> PyMuPDF page extraction
    |      +--> Recursive text chunking
    |      +--> HuggingFace embeddings
    |      +--> FAISS vector index
    |
    +--> Research Chat
    |      |
    |      +--> Query
    |      +--> Top-K semantic retrieval
    |      +--> Evidence-aware prompt
    |      +--> Google Gemini LLM
    |      +--> Answer + source metadata
    |
    +--> Summary
    |
    +--> Retrieval Diagnostics
```

## RAG Pipeline

1. **Upload**: PDFs are stored under `data/uploads/`.
2. **Extract**: PyMuPDF extracts text page-by-page.
3. **Metadata**: Each chunk retains the original filename and page number.
4. **Chunk**: Recursive character splitting creates overlapping retrieval units.
5. **Embed**: `all-mpnet-base-v2` converts chunks into vectors.
6. **Index**: FAISS stores the vectors locally.
7. **Retrieve**: A user question is embedded and the Top-K nearest chunks are returned.
8. **Generate**: The retrieved evidence is passed to the selected LLM with instructions to avoid unsupported claims.
9. **Cite**: The UI displays source document and page metadata from the retrieved chunks.

## Technology Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| PDF extraction | PyMuPDF |
| Chunking | LangChain Text Splitters |
| Embeddings | HuggingFace `all-mpnet-base-v2` |
| Vector store | FAISS |
| LLM | Google Gemini |
| Configuration | python-dotenv |
| Testing | pytest |

## Installation

### Windows

```bat
setup.bat
```

Then edit `.env` and add your API key.

Run:

```bat
run.bat
```

### Manual

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

## Environment Setup

Required depending on the selected provider:

```env
GEMINI_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-2.5-flash
```

Optional RAG defaults:

```env
TOP_K=6
CHUNK_SIZE=800
CHUNK_OVERLAP=150
```

The current UI also lets you change retrieval settings during a session.

## Usage

1. Start ResearchLens AI.
2. Upload one or more research papers.
3. Click **Process selected papers**.
4. Open **Research Chat**.
5. Ask questions about contributions, datasets, methodology, results, limitations, or comparisons.
6. Expand **Sources** to inspect document/page evidence.
7. Expand **Retrieved context** to debug the retrieval step.
8. Use **Summaries** to generate a structured paper summary.
9. Use **Paper Library** to rebuild or delete documents.

## Screenshots

Add project screenshots here after running the application:

```text
docs/screenshots/dashboard.png
docs/screenshots/chat-with-sources.png
docs/screenshots/paper-library.png
docs/screenshots/retrieval-diagnostics.png
```

## Limitations

- Text extraction currently focuses on text-based PDFs. Scanned/image-only PDFs are reported as unsupported rather than pretending OCR succeeded.
- Page-level citation is metadata-based; the system does not yet identify exact section headings reliably.
- FAISS is local and does not provide production-grade multi-user document isolation.
- Chat history is session-based and is not persisted to a database.
- Retrieval diagnostics are useful for debugging but are not benchmark evaluation metrics.
- Summary generation sends extracted paper content to the configured LLM provider.
- Very long papers are truncated for the summary prompt to keep the implementation lightweight.

## Future Improvements

- Add optional OCR for scanned research papers.
- Add section-aware parsing for Abstract, Methods, Results, and Conclusion.
- Add a reranking model after FAISS retrieval.
- Add a small human-labelled evaluation set for Recall@K, MRR and answer-grounding evaluation.
- Add persistent user workspaces and authentication only if deployment requirements justify them.
- Add downloadable citation notes / BibTeX generation.
- Add paper-level filters before retrieval.
- Add a local embedding model option for privacy-sensitive workflows.

## Project Structure

```text
ResearchLens-AI/
├── app/
│   └── main.py
├── src/
│   ├── ingestion/
│   ├── embeddings/
│   ├── retrieval/
│   ├── services/
│   └── utils/
├── data/
│   └── uploads/
├── tests/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── run.bat
├── setup.bat
└── README.md
```
