"""
backend/app/services/llm.py
Service wrapping Groq LLM API with timeouts, retry logic, and error sanitization.
"""

import time
from typing import Any, Dict, List, Optional
from groq import Groq, AuthenticationError, RateLimitError, APIError, APITimeoutError, APIConnectionError

from backend.app.config import get_settings
from backend.app.core.errors import LLMAuthenticationError, LLMUnavailableError


class LLMClient:
    """Wrapper around Groq API with robust retry and error masking."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: float = 30.0):
        settings = get_settings()
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.timeout = timeout
        self.client = Groq(api_key=self.api_key, timeout=self.timeout)

    def complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 700,
        temperature: float = 0.2,
    ) -> str:
        """
        Sends messages to Groq chat completions.
        Retries once on 429 (RateLimitError) or 5xx server errors with backoff.
        Never retries on 4xx authentication errors.
        """
        backoffs = [1.0, 3.0]
        last_exception: Optional[Exception] = None

        for attempt, delay in enumerate(backoffs):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                content = response.choices[0].message.content
                return (content or "").strip()

            except AuthenticationError as e:
                # 401/403: Never retry credential errors
                raise LLMAuthenticationError("The assistant is temporarily unavailable. Please try again.") from e

            except (RateLimitError, APITimeoutError, APIConnectionError, APIError) as e:
                # Retry on 429 or network/server issues if attempts remain
                status_code = getattr(e, "status_code", None)
                if status_code and 400 <= status_code < 500 and status_code != 429:
                    # Client-side 4xx errors other than rate limit should not retry
                    raise LLMUnavailableError("The assistant is temporarily unavailable. Please try again.") from e

                last_exception = e
                if attempt < len(backoffs) - 1:
                    time.sleep(delay)
                    continue

            except Exception as e:
                last_exception = e
                break

        # If retries exhausted or unexpected error occurred
        raise LLMUnavailableError("The assistant is temporarily unavailable. Please try again.") from last_exception


_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Returns singleton LLMClient instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
