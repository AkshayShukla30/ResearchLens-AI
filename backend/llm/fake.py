from llm.base import LLMProvider


class FakeProvider(LLMProvider):
    """Offline stand-in for tests (LLM_PROVIDER=fake). Not for real use."""

    name = "fake"
    is_configured = True

    def __init__(self) -> None:
        super().__init__("fake-model", retries=0)

    def _generate_once(self, prompt: str, system: str, temperature: float) -> str:
        return "FAKE_LLM_RESPONSE\n" + prompt[:200]
