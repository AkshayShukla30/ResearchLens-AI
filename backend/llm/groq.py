import logging
from typing import Optional

import config
from llm.base import (LLMConfigError, LLMError, LLMProvider, LLMRateLimitError,
                      LLMTimeoutError)

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        super().__init__(model or config.GROQ_MODEL, retries=config.LLM_MAX_RETRIES)
        self.api_key = config.GROQ_API_KEY if api_key is None else api_key
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None:
            if not self.is_configured:
                raise LLMConfigError("GROQ_API_KEY is not set. Add it to your .env file.")
            from groq import Groq

            # Retries are handled in LLMProvider.generate, so turn off the SDK's own.
            self._client = Groq(api_key=self.api_key, timeout=config.LLM_TIMEOUT_S, max_retries=0)
        return self._client

    def _generate_once(self, prompt: str, system: str, temperature: float) -> str:
        import groq

        client = self._get_client()
        messages = [{"role": "user", "content": prompt}]
        if system:
            messages.insert(0, {"role": "system", "content": system})
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=config.LLM_MAX_OUTPUT_TOKENS,
            )
            return resp.choices[0].message.content or ""
        except groq.APITimeoutError as exc:
            raise LLMTimeoutError("Groq request timed out. Try again.") from exc
        except groq.APIConnectionError as exc:
            raise LLMError("Could not reach the Groq API.") from exc
        except groq.APIStatusError as exc:
            raise self._translate(exc) from exc

    def _translate(self, exc) -> LLMError:
        code = exc.status_code
        logger.error("Groq API error %s: %s", code, exc)
        if code == 429:
            return LLMRateLimitError("Groq rate limit reached. Wait a bit and retry.")
        if code in (401, 403):
            return LLMConfigError("Groq rejected the API key. Check GROQ_API_KEY.")
        if code == 404:
            return LLMConfigError(f"Groq model '{self.model}' was not found. Check GROQ_MODEL.")
        err = LLMError("Groq request failed. Check the server logs for details.")
        err.retryable = code >= 500
        return err
