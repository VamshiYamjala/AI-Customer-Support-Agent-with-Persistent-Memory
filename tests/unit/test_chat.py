"""
tests/unit/test_chat.py
Unit tests for the chat API, LLM service, validation, and error handling.
"""

from unittest.mock import MagicMock, patch
import pytest
from groq import AuthenticationError, RateLimitError, APITimeoutError
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.prompts.system import BASE_SYSTEM_PROMPT
from backend.app.services.llm import LLMClient
from backend.app.core.errors import LLMAuthenticationError, LLMUnavailableError


from backend.app.services.llm import LLMClient, get_llm_client


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# 1. Validation Tests
@pytest.mark.unit
def test_chat_valid_message_mocked(client):
    """Verify valid request returns 200 and expected ChatResponse structure."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.return_value = "I would be happy to help you with your PayNest billing question."
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    response = client.post(
        "/api/chat",
        json={"message": "I have an issue with my subscription charge.", "use_memory": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert "PayNest billing question" in data["reply"]
    assert data["memory_status"] == "off"
    assert isinstance(data["memories_used"], list)
    assert len(data["memories_used"]) == 0
    assert data["session_id"] is not None


@pytest.mark.unit
def test_chat_empty_message_rejected(client):
    """Verify empty message triggers 422 Unprocessable Entity."""
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422


@pytest.mark.unit
def test_chat_whitespace_only_rejected(client):
    """Verify whitespace-only message triggers 422."""
    response = client.post("/api/chat", json={"message": "    \n\t   "})
    assert response.status_code == 422


@pytest.mark.unit
def test_chat_oversized_message_rejected(client):
    """Verify message > 2000 characters triggers 422."""
    huge_message = "A" * 2001
    response = client.post("/api/chat", json={"message": huge_message})
    assert response.status_code == 422


# 2. LLM Service Retry & Error Mapping Tests
@pytest.mark.unit
def test_llm_retry_on_429_then_success():
    """Verify LLMClient retries once on RateLimitError (429) with backoff and succeeds."""
    with patch("backend.app.services.llm.Groq") as mock_groq_cls:
        with patch("time.sleep", return_value=None):  # Fast test
            mock_instance = MagicMock()
            mock_groq_cls.return_value = mock_instance

            # Mock 429 on first call, success on second call
            rate_limit_err = RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429, headers={}),
                body={"error": {"message": "Rate limit exceeded"}},
            )
            success_resp = MagicMock(choices=[MagicMock(message=MagicMock(content="Recovery response"))])
            mock_instance.chat.completions.create.side_effect = [rate_limit_err, success_resp]

            llm = LLMClient(api_key="gsk_test", model="test_model")
            reply = llm.complete([{"role": "user", "content": "Hi"}])

            assert reply == "Recovery response"
            assert mock_instance.chat.completions.create.call_count == 2


@pytest.mark.unit
def test_llm_auth_error_no_retry():
    """Verify AuthenticationError (401) is never retried and maps to LLMAuthenticationError."""
    with patch("backend.app.services.llm.Groq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance

        auth_err = AuthenticationError(
            message="Invalid API Key",
            response=MagicMock(status_code=401, headers={}),
            body={"error": {"message": "Invalid API Key"}},
        )
        mock_instance.chat.completions.create.side_effect = auth_err

        llm = LLMClient(api_key="gsk_bad_key", model="test_model")
        with pytest.raises(LLMAuthenticationError) as exc_info:
            llm.complete([{"role": "user", "content": "Hi"}])

        # Exactly 1 call (no retries)
        assert mock_instance.chat.completions.create.call_count == 1
        assert "temporarily unavailable" in str(exc_info.value)


@pytest.mark.unit
def test_llm_timeout_maps_to_503(client):
    """Verify LLM failure maps to HTTP 503 without leaking provider stack trace."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.side_effect = LLMUnavailableError()
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    response = client.post("/api/chat", json={"message": "Hello?"})

    assert response.status_code == 503
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "llm_unavailable"
    assert "temporarily unavailable" in data["error"]["message"]


# 3. System Prompt & Honesty Guardrail Tests
@pytest.mark.unit
def test_system_prompt_rules():
    """Verify system prompt enforces PayNest support honesty rules."""
    assert "You are the PayNest support assistant" in BASE_SYSTEM_PROMPT
    assert "Never claim you have processed a refund" in BASE_SYSTEM_PROMPT
    assert "NO access to internal payment systems" in BASE_SYSTEM_PROMPT
