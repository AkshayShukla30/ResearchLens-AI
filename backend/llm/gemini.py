import logging
from typing import Optional

import httpx

import config
from llm.base import (LLMConfigError, LLMError, LLMProvider, LLMRateLimitError,
                      LLMTimeoutError)

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        super().__init__(model or config.GEMINI_MODEL, retries=config.LLM_MAX_RETRIES)
        self.api_key = config.GEMINI_API_KEY if api_key is None else api_key
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None:
            if not self.is_configured:
                raise LLMConfigError("GEMINI_API_KEY is not set. Add it to your .env file.")
            from google import genai
            from google.genai import types

            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=int(config.LLM_TIMEOUT_S * 1000)),
            )
        return self._client

    def _generate_once(self, prompt: str, system: str, temperature: float) -> str:
        from google.genai import errors, types

        client = self._get_client()
        try:
            resp = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system or None,
                    temperature=temperature,
                    max_output_tokens=config.LLM_MAX_OUTPUT_TOKENS,
                ),
            )
            return resp.text or ""
        except errors.APIError as exc:
            raise self._translate(exc) from exc
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("Gemini request timed out. Try again.") from exc
        except httpx.TransportError as exc:
            raise LLMError("Could not reach the Gemini API.") from exc

    def _translate(self, exc) -> LLMError:
        code = getattr(exc, "code", None)
        text = str(getattr(exc, "message", "") or exc)
        logger.error("Gemini API error %s: %s", code, text)
        if code == 429:
            return LLMRateLimitError("Gemini rate limit or quota reached. Wait a bit and retry.")
        if code == 404:
            return LLMConfigError(f"Gemini model '{self.model}' was not found. Check GEMINI_MODEL.")
        # Gemini reports a bad key as 400 rather than 401.
        if code in (401, 403) or "API key" in text:
            return LLMConfigError("Gemini rejected the API key. Check GEMINI_API_KEY.")
        if code == 408 or code == 504:
            return LLMTimeoutError("Gemini request timed out. Try again.")
        err = LLMError("Gemini request failed. Check the server logs for details.")
        err.retryable = bool(code and code >= 500)
        return err
