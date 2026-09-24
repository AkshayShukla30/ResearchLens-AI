import config
from llm.base import LLMConfigError, LLMProvider
from llm.fake import FakeProvider
from llm.gemini import GeminiProvider
from llm.groq import GroqProvider

_PROVIDERS = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "fake": FakeProvider,  # tests only
}


def get_llm_provider(name: str | None = None) -> LLMProvider:
    """Build the provider named in LLM_PROVIDER. No silent fallback."""
    key = (name if name is not None else config.LLM_PROVIDER).strip().lower()
    cls = _PROVIDERS.get(key)
    if cls is None:
        supported = ", ".join(sorted(p for p in _PROVIDERS if p != "fake"))
        raise LLMConfigError(f"Unsupported LLM provider: {key or '(empty)'}. Use one of: {supported}.")
    return cls()
