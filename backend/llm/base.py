"""Common interface for LLM providers."""
import logging
import time
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Provider failure. The message is safe to show to the user."""

    retryable = False


class LLMConfigError(LLMError):
    """Missing API key, unknown provider or unknown model."""


class LLMRateLimitError(LLMError):
    retryable = True


class LLMTimeoutError(LLMError):
    retryable = True


class LLMProvider(ABC):
    name = ""

    def __init__(self, model: str, retries: int = 2, retry_delay: float = 1.5) -> None:
        self.model = model
        self.retries = retries
        self.retry_delay = retry_delay

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """True when the provider has the credentials it needs."""

    @abstractmethod
    def _generate_once(self, prompt: str, system: str, temperature: float) -> str:
        """One request to the provider. Raise LLMError subclasses, not SDK errors."""

    def generate(self, prompt: str, system: str = "", temperature: float = 0.2) -> str:
        for attempt in range(self.retries + 1):
            try:
                text = (self._generate_once(prompt, system, temperature) or "").strip()
                if not text:
                    raise LLMError(f"{self.name} returned an empty response.")
                return text
            except LLMError as exc:
                logger.warning("%s request failed (attempt %d): %s", self.name, attempt + 1, exc)
                if not exc.retryable or attempt == self.retries:
                    raise
                time.sleep(self.retry_delay * (attempt + 1))
