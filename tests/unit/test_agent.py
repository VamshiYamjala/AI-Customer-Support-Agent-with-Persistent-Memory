"""
tests/unit/test_agent.py
Unit tests for Core Support Agent orchestration, honesty guardrails, citation validation,
query building, and outcome tracking.
"""

from unittest.mock import MagicMock
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import MemoryItem
from backend.app.services.agent import (
    AgentService,
    SAFE_ACTION_REPLACEMENT,
    build_recall_query,
    get_agent_service,
    post_check_honesty,
)
from backend.app.services.identity import create_token
from backend.app.services.llm import LLMClient, get_llm_client
from backend.app.services.memory import MemoryService, get_memory_service


@pytest.fixture
def auth_client():
    app.dependency_overrides.clear()
    token = create_token("priya")
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as c:
        yield c
    app.dependency_overrides.clear()


# 1. Query Builder Tests
@pytest.mark.unit
def test_build_recall_query_empty_history():
    query = build_recall_query("My subscription renewal failed", [])
    assert query == "My subscription renewal failed"


@pytest.mark.unit
def test_build_recall_query_with_context():
    history = [
        {"role": "user", "content": "I am having trouble with my Visa ending 4242."},
        {"role": "assistant", "content": "Could you provide more details?"},
    ]
    query = build_recall_query("It failed again today", history)
    assert "It failed again today" in query
    assert "Visa ending 4242" in query
    # Check word limit adherence
    assert len(query.split()) <= 35


# 2. Honesty Guardrail Tests
@pytest.mark.unit
def test_post_check_honesty_replaces_unauthorized_action_claims():
    """Verify false claims like 'I have refunded' or 'I cancelled your subscription' are sanitized."""
    bad_reply = "I apologize for the issue. I have refunded your card for the $49 charge."
    cleaned = post_check_honesty(bad_reply, allowed_citations=set())

    assert "I have refunded your card" not in cleaned
    assert SAFE_ACTION_REPLACEMENT in cleaned


@pytest.mark.unit
def test_post_check_honesty_preserves_honest_replies():
    """Verify standard helpful support responses without false claims are preserved."""
    honest_reply = (
        "I understand your payment failed. Please check Settings > Billing Methods to update your card. "
        "I can submit a ticket to our human team if you need a refund review."
    )
    cleaned = post_check_honesty(honest_reply, allowed_citations=set())
    assert cleaned == honest_reply


# 3. Citation Validation Tests
@pytest.mark.unit
def test_post_check_honesty_validates_citations():
    """Verify citations in allowed_citations are kept, and hallucinated citations are stripped."""
    allowed = {"M1", "K2"}
    reply_with_citations = "Based on your past issue [M1] and policy [K2], you should also check [M99] and [K5]."
    cleaned = post_check_honesty(reply_with_citations, allowed_citations=allowed)

    assert "[M1]" in cleaned
    assert "[K2]" in cleaned
    assert "[M99]" not in cleaned
    assert "[K5]" not in cleaned


# 4. Outcome Recording Tests
@pytest.mark.unit
def test_record_outcome_resolved(auth_client):
    """Verify POST /api/outcome records resolution and updates ticket in SQLite."""
    mock_memory = MagicMock(spec=MemoryService)
    app.dependency_overrides[get_memory_service] = lambda: mock_memory

    # Send a chat message first to create session and ticket
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.return_value = "Try updating your billing address."
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    chat_resp = auth_client.post("/api/chat", json={"message": "Help with card failure"})
    assert chat_resp.status_code == 200
    session_id = chat_resp.json()["session_id"]

    # Record outcome for this session
    outcome_resp = auth_client.post(
        "/api/outcome",
        json={
            "session_id": session_id,
            "outcome": "resolved",
            "note": "Updating billing address worked!",
        },
    )

    assert outcome_resp.status_code == 200
    data = outcome_resp.json()
    assert data["status"] == "recorded"
    assert data["outcome"] == "resolved"
    assert data["ticket_id"].startswith("tkt_")

    # Verify memory.retain_outcome was called with correct arguments
    mock_memory.retain_outcome.assert_called_once()
    call_kwargs = mock_memory.retain_outcome.call_args.kwargs
    assert call_kwargs["customer_id"] == "priya"
    assert call_kwargs["outcome"] == "resolved"
    assert "Updating billing address worked!" in call_kwargs["note"]


@pytest.mark.unit
def test_record_outcome_not_resolved(auth_client):
    """Verify POST /api/outcome records non-resolution ('Still broken')."""
    mock_memory = MagicMock(spec=MemoryService)
    app.dependency_overrides[get_memory_service] = lambda: mock_memory

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.return_value = "Try refreshing your browser."
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    chat_resp = auth_client.post("/api/chat", json={"message": "Still not working"})
    session_id = chat_resp.json()["session_id"]

    outcome_resp = auth_client.post(
        "/api/outcome",
        json={
            "session_id": session_id,
            "outcome": "not_resolved",
            "note": "Still broken after refreshing",
        },
    )

    assert outcome_resp.status_code == 200
    data = outcome_resp.json()
    assert data["outcome"] == "not_resolved"


@pytest.mark.unit
def test_record_outcome_invalid_value(auth_client):
    """Verify invalid outcome string is rejected with HTTP 422."""
    outcome_resp = auth_client.post(
        "/api/outcome",
        json={
            "session_id": "sess_dummy",
            "outcome": "maybe_fixed",
        },
    )
    assert outcome_resp.status_code == 422


# 5. Customer History Tests
@pytest.mark.unit
def test_get_customer_history(auth_client):
    """Verify GET /api/customer/history returns sessions, messages, and outcomes."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.return_value = "I can assist you with that."
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    auth_client.post("/api/chat", json={"message": "Inquiring about invoice #1001"})

    history_resp = auth_client.get("/api/customer/history")
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert isinstance(history, list)
    assert len(history) >= 1
    latest_item = history[0]
    assert "session" in latest_item
    assert "messages" in latest_item
    assert "ticket" in latest_item
    assert "outcomes" in latest_item
