# ResearchLens AI

### AI-Powered Research Paper Assistant

ResearchLens AI is a multi-PDF research assistant that helps users read, search, summarize, and compare research papers using Retrieval-Augmented Generation (RAG).

Upload research papers, ask questions, compare multiple papers, generate summaries, and inspect the sources used to generate answers.
## Live Demo

[https://researchlens-ai.streamlit.app/](https://researchlens-ai.streamlit.app/)

## GitHub

[https://github.com/AkshayShukla30/ResearchLens-AI](https://github.com/AkshayShukla30/ResearchLens-AI)
## Features

- Multi-PDF Upload
- Research Paper Q&A
- Multi-Paper Comparison
- Paper Summarization
- Semantic Search
- Source & Page Citations
- Retrieved Context View
- Retrieval Diagnostics
- Configurable Top-K Retrieval
- Configurable Chunk Size & Overlap
- Document Management
- Google Gemini Powered Responses

## Tech Stack

- Python
- Streamlit
- PyMuPDF
- LangChain
- HuggingFace Embeddings
- FAISS
- Google Gemini API

## RAG Pipeline

```text
Research Papers
      ↓
   PyMuPDF
      ↓
  Text Chunking
      ↓
HuggingFace Embeddings
      ↓
     FAISS
      ↓
 Top-K Retrieval
      ↓
Retrieved Context
      ↓
 Google Gemini
      ↓
Answer + Sources
```
## Project Structure

```text
ResearchLens-AI/
│
├── app/
│   └── main.py
│
├── src/
│   ├── ingestion/
│   ├── embeddings/
│   ├── retrieval/
│   ├── services/
│   └── utils/
│
├── data/
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

## Run Locally

```bash
git clone https://github.com/AkshayShukla30/ResearchLens-AI.git
cd ResearchLens-AI
pip install -r requirements.txt
```

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-3.5-flash
```

Run the application:

```bash
streamlit run app.py
```



## Author

### Akshay Shukla

**LinkedIn:**  
[https://in.linkedin.com/in/akshayshukla-](https://in.linkedin.com/in/akshayshukla-)

**GitHub:**  
[https://github.com/AkshayShukla30](https://github.com/AkshayShukla30)
```

