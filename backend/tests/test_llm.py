"""Provider tests. The SDK clients are replaced with fakes, so no API keys are needed."""
from types import SimpleNamespace

import groq
import httpx
import pytest
from google.genai import errors as genai_errors

import config
import main
from llm import (LLMConfigError, LLMError, LLMProvider, LLMRateLimitError,
                 LLMTimeoutError, get_llm_provider)
from llm.gemini import GeminiProvider
from llm.groq import GroqProvider
from services.rag_service import RAGService

from .test_api import PAPER_A, client, upload  # noqa: F401  (client is a fixture)


class FakeGeminiClient:
    def __init__(self, result=None, error=None):
        self.calls = []
        self.models = SimpleNamespace(generate_content=self._generate)
        self._result, self._error = result, error

    def _generate(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return SimpleNamespace(text=self._result)


class FakeGroqClient:
    def __init__(self, result=None, error=None):
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self._result, self._error = result, error

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        message = SimpleNamespace(content=self._result)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def groq_status_error(cls, status):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    return cls("boom", response=httpx.Response(status, request=request), body=None)


# ---------- factory ----------

def test_factory_returns_selected_provider(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "gemini")
    assert isinstance(get_llm_provider(), GeminiProvider)
    monkeypatch.setattr(config, "LLM_PROVIDER", "Groq ")
    assert isinstance(get_llm_provider(), GroqProvider)
    assert get_llm_provider("gemini").name == "gemini"


def test_factory_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "xyz")
    with pytest.raises(LLMConfigError, match="Unsupported LLM provider: xyz"):
        get_llm_provider()


# ---------- configuration ----------

def test_models_come_from_config(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_MODEL", "gem-test")
    monkeypatch.setattr(config, "GROQ_MODEL", "groq-test")
    assert GeminiProvider(api_key="k").model == "gem-test"
    assert GroqProvider(api_key="k").model == "groq-test"
    assert GroqProvider(api_key="k", model="other").model == "other"


@pytest.mark.parametrize("cls,var", [(GeminiProvider, "GEMINI_API_KEY"), (GroqProvider, "GROQ_API_KEY")])
def test_missing_key_gives_clear_error(cls, var):
    provider = cls(api_key="")
    assert not provider.is_configured
    with pytest.raises(LLMConfigError, match=var):
        provider.generate("hi")


# ---------- generation ----------

def test_gemini_generate():
    provider = GeminiProvider(api_key="k", model="m")
    provider._client = FakeGeminiClient(result="  hello  ")
    assert provider.generate("question", system="be brief") == "hello"
    call = provider._client.calls[0]
    assert call["model"] == "m" and call["contents"] == "question"
    assert call["config"].system_instruction == "be brief"


def test_groq_generate():
    provider = GroqProvider(api_key="k", model="m")
    provider._client = FakeGroqClient(result="hello")
    assert provider.generate("question", system="be brief", temperature=0.5) == "hello"
    call = provider._client.calls[0]
    assert call["model"] == "m" and call["temperature"] == 0.5
    assert call["messages"] == [{"role": "system", "content": "be brief"},
                                {"role": "user", "content": "question"}]


def test_empty_response_is_an_error():
    provider = GroqProvider(api_key="k")
    provider._client = FakeGroqClient(result="")
    with pytest.raises(LLMError, match="empty"):
        provider.generate("hi")


# ---------- error handling ----------

def test_gemini_error_mapping():
    def run(code):
        provider = GeminiProvider(api_key="k", model="m")
        provider.retries = 0
        provider._client = FakeGeminiClient(error=genai_errors.APIError(code, {"error": {"message": "x"}}))
        return provider

    with pytest.raises(LLMRateLimitError):
        run(429).generate("hi")
    with pytest.raises(LLMConfigError, match="not found"):
        run(404).generate("hi")
    with pytest.raises(LLMConfigError, match="API key"):
        run(403).generate("hi")


def test_groq_error_mapping():
    def run(cls, status):
        provider = GroqProvider(api_key="k", model="m")
        provider.retries = 0
        provider._client = FakeGroqClient(error=groq_status_error(cls, status))
        return provider

    with pytest.raises(LLMRateLimitError):
        run(groq.RateLimitError, 429).generate("hi")
    with pytest.raises(LLMConfigError, match="not found"):
        run(groq.NotFoundError, 404).generate("hi")
    with pytest.raises(LLMConfigError, match="API key"):
        run(groq.AuthenticationError, 401).generate("hi")


def test_timeout_is_reported():
    provider = GroqProvider(api_key="k")
    provider.retries = 0
    provider._client = FakeGroqClient(error=groq.APITimeoutError(request=httpx.Request("POST", "http://x")))
    with pytest.raises(LLMTimeoutError):
        provider.generate("hi")


def test_transient_errors_are_retried(monkeypatch):
    provider = GroqProvider(api_key="k")
    provider.retry_delay = 0
    responses = iter([groq_status_error(groq.RateLimitError, 429), "finally"])
    client = FakeGroqClient()

    def create(**kwargs):
        item = next(responses)
        if isinstance(item, Exception):
            raise item
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=item))])

    client.chat.completions.create = create
    provider._client = client
    assert provider.generate("hi") == "finally"


def test_config_errors_are_not_retried():
    provider = GroqProvider(api_key="k")
    provider._client = FakeGroqClient(error=groq_status_error(groq.NotFoundError, 404))
    with pytest.raises(LLMConfigError):
        provider.generate("hi")
    assert len(provider._client.calls) == 1


# ---------- RAG service only depends on the interface ----------

class StubProvider(LLMProvider):
    name = "stub"
    is_configured = True

    def __init__(self):
        super().__init__("stub-model", retries=0)
        self.prompts = []

    def _generate_once(self, prompt, system, temperature):
        self.prompts.append(prompt)
        return "stub answer"


def test_rag_service_uses_provider_interface(client):  # noqa: F811
    upload(client, "a.pdf", PAPER_A)
    stub = StubProvider()
    main._service = RAGService(main.get_store(), stub)
    body = client.post("/api/ask", json={"question": "What is self attention?", "top_k": 2}).json()
    assert body["answer"] == "stub answer"
    assert body["diagnostics"]["llm_provider"] == "stub"
    assert body["diagnostics"]["llm_model"] == "stub-model"
    assert "a.pdf, p." in stub.prompts[0]
    ctx = body["contexts"][0]
    assert ctx["source"] == "a.pdf" and ctx["page"] in (1, 2) and ctx["chunk_id"].count(":") == 1


# ---------- API behaviour ----------

def test_health_reports_active_provider(client, monkeypatch):  # noqa: F811
    assert client.get("/api/health").json()["llm_provider"] == "fake"
    main._service = None
    monkeypatch.setattr(config, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(config, "GROQ_API_KEY", "")
    h = client.get("/api/health").json()
    assert h["llm_provider"] == "groq" and h["llm_configured"] is False
    assert "api_key" not in str(h).lower()


def test_invalid_provider_does_not_break_health_and_ask_is_clean(client, monkeypatch):  # noqa: F811
    upload(client, "a.pdf", PAPER_A)
    main._service = None
    monkeypatch.setattr(config, "LLM_PROVIDER", "xyz")
    h = client.get("/api/health").json()
    assert h["llm_configured"] is False and "Unsupported LLM provider: xyz" in h["llm_error"]
    r = client.post("/api/ask", json={"question": "self attention?"})
    assert r.status_code == 503 and "Unsupported LLM provider" in r.json()["detail"]


def test_missing_key_and_rate_limit_status_codes(client, monkeypatch):  # noqa: F811
    upload(client, "a.pdf", PAPER_A)
    main._service = None
    monkeypatch.setattr(config, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    r = client.post("/api/ask", json={"question": "self attention?"})
    assert r.status_code == 503 and "GEMINI_API_KEY" in r.json()["detail"]

    class Limited(StubProvider):
        def _generate_once(self, prompt, system, temperature):
            raise LLMRateLimitError("slow down")

    main._service = RAGService(main.get_store(), Limited())
    r = client.post("/api/ask", json={"question": "self attention?"})
    assert r.status_code == 429 and r.json()["detail"] == "slow down"


def test_retrieval_failure_is_reported_cleanly(client, monkeypatch):  # noqa: F811
    upload(client, "a.pdf", PAPER_A)
    store = main.get_store()
    monkeypatch.setattr(store, "search", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("faiss exploded")))
    r = client.post("/api/search", json={"query": "attention"})
    assert r.status_code == 500 and "faiss exploded" not in r.text
