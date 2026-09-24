"""Central configuration, loaded from environment / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")

# "gemini" or "groq" for real use; "fake" only for offline tests.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# LLM_MODEL was the old name for the Gemini model, still honoured.
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or os.getenv("LLM_MODEL") or "gemini-3.5-flash"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "60"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
LLM_MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "8192"))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# "huggingface" for real use, "fake" only for offline tests.
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface")

DATA_DIR = Path(os.getenv("DATA_DIR", ROOT_DIR / "data" / "researchlens_store"))
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", ROOT_DIR / "frontend" / "dist"))

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "1000"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "150"))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
