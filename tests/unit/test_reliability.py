"""
tests/unit/test_reliability.py
Comprehensive reliability, boundary condition, security, and edge-case tests
for PayNest Support Assistant.
"""

from unittest.mock import MagicMock, patch
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.core.errors import MemoryUnavailableError, LLMUnavailableError
from backend.app.db.store import DatabaseStore, get_store
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
def auth_priya():
    app.dependency_overrides.clear()
    token = create_token("priya")
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_arjun():
    app.dependency_overrides.clear()
    token = create_token("arjun")
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as c:
        yield c
    app.dependency_overrides.clear()


# ============================================================================
# 1. Chat Boundary & Malformed Input Tests
# ============================================================================

@pytest.mark.unit
def test_chat_message_exact_max_boundary(auth_priya):
    """Verify exactly 2,000 characters is accepted with 200 OK."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.return_value = "Received long message."
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    max_message = "A" * 2000
    resp = auth_priya.post("/api/chat", json={"message": max_message, "use_memory": False})
    assert resp.status_code == 200
    assert resp.json()["reply"] == "Received long message."


@pytest.mark.unit
def test_chat_message_exceeds_max_boundary(auth_priya):
    """Verify 2,001 characters is rejected with 422 Unprocessable Entity."""
    resp = auth_priya.post("/api/chat", json={"message": "A" * 2001})
    assert resp.status_code == 422


@pytest.mark.unit
def test_chat_unicode_and_emojis(auth_priya):
    """Verify unicode characters, emojis, and non-ASCII scripts process safely without encoding crashes."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.return_value = "Namaste Priya! 💳 I can help with your subscription ₹500 charge."
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    unicode_msg = "नमस्ते! I need help with ₹500 PayNest charge 🙏 💳."
    resp = auth_priya.post("/api/chat", json={"message": unicode_msg, "use_memory": False})
    assert resp.status_code == 200
    assert "Namaste Priya!" in resp.json()["reply"]


@pytest.mark.unit
def test_chat_malformed_json_body(auth_priya):
    """Verify malformed JSON body returns 422 without leaking server stack trace."""
    resp = auth_priya.post(
        "/api/chat",
        content="not a valid json string",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422


# ============================================================================
# 2. Outcome API Boundary & Security Isolation
# ============================================================================

@pytest.mark.unit
def test_outcome_auto_creates_ticket_when_session_provided(auth_priya):
    """Verify /api/outcome automatically associates or creates a ticket for a valid session."""
    mock_memory = MagicMock(spec=MemoryService)
    app.dependency_overrides[get_memory_service] = lambda: mock_memory

    # Create session first
    store = get_store()
    session = store.create_session("priya", "sess_auto_tkt_test")

    resp = auth_priya.post(
        "/api/outcome",
        json={"session_id": "sess_auto_tkt_test", "outcome": "resolved", "note": "All good"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "recorded"
    assert data["outcome"] == "resolved"
    assert data["ticket_id"].startswith("tkt_")


@pytest.mark.unit
def test_outcome_cross_customer_ticket_rejected(auth_priya, auth_arjun):
    """Verify customer Priya cannot record an outcome on customer Arjun's ticket (HTTP 404)."""
    store = get_store()
    arjun_sess = store.create_session("arjun", "sess_arjun_tkt_sec")
    arjun_ticket = store.create_ticket("arjun", "sess_arjun_tkt_sec", "Enterprise Invoicing", ticket_id="tkt_arjun_sec")

    # Priya tries to tamper with Arjun's ticket
    resp = auth_priya.post(
        "/api/outcome",
        json={"ticket_id": "tkt_arjun_sec", "outcome": "resolved", "note": "Tamper attempt"},
    )
    assert resp.status_code == 404
    assert "not found or belongs to another customer" in resp.json()["detail"].lower()


@pytest.mark.unit
def test_outcome_missing_session_and_ticket_rejected(auth_priya):
    """Verify /api/outcome returns 400 when neither session_id nor ticket_id is provided."""
    resp = auth_priya.post(
        "/api/outcome",
        json={"outcome": "resolved", "note": "Orphan outcome"},
    )
    assert resp.status_code == 400


# ============================================================================
# 3. Session Isolation & History Audit
# ============================================================================

@pytest.mark.unit
def test_session_messages_cross_customer_isolation(auth_priya, auth_arjun):
    """Verify customer Priya cannot view Arjun's message history (returns 404)."""
    store = get_store()
    store.create_session("arjun", "sess_arjun_private")
    store.save_message("sess_arjun_private", "arjun", "user", "Confidential tax details")

    # Priya requests Arjun's session
    resp = auth_priya.get("/api/sessions/sess_arjun_private/messages")
    assert resp.status_code == 404


@pytest.mark.unit
def test_customer_history_scoped_to_bearer_token(auth_priya, auth_arjun):
    """Verify /api/customer/history returns only the caller's data."""
    store = get_store()
    store.create_session("priya", "sess_p_hist_1", title="Priya Issue")
    store.create_session("arjun", "sess_a_hist_1", title="Arjun Issue")

    p_resp = auth_priya.get("/api/customer/history")
    assert p_resp.status_code == 200
    p_data = p_resp.json()
    assert all(item["session"]["customer_id"] == "priya" for item in p_data)

    a_resp = auth_arjun.get("/api/customer/history")
    assert a_resp.status_code == 200
    a_data = a_resp.json()
    assert all(item["session"]["customer_id"] == "arjun" for item in a_data)


# ============================================================================
# 4. Authentication Edge Cases
# ============================================================================

@pytest.mark.unit
def test_login_unknown_customer_rejected():
    """Verify login with unregistered customer ID returns 404."""
    with TestClient(app) as client:
        resp = client.post("/api/login", json={"customer_id": "unknown_hacker"})
        assert resp.status_code == 404


@pytest.mark.unit
def test_login_whitespace_customer_trimmed():
    """Verify login trims customer ID cleanly."""
    with TestClient(app) as client:
        resp = client.post("/api/login", json={"customer_id": "  priya  "})
        assert resp.status_code == 200
        assert resp.json()["customer"]["id"] == "priya"


@pytest.mark.unit
def test_missing_auth_header_rejected():
    """Verify calling protected endpoints without Authorization header returns 401."""
    with TestClient(app) as client:
        resp = client.get("/api/me")
        assert resp.status_code == 401
        assert "not authenticated" in resp.json()["detail"].lower() or "missing" in resp.json()["detail"].lower()


# ============================================================================
# 5. Agent Honesty Guardrail Edge Cases
# ============================================================================

@pytest.mark.unit
def test_honesty_guard_handles_case_variations():
    """Verify various casing and phrasing of unauthorized actions are sanitized."""
    variations = [
        "I have refunded your payment.",
        "I've refunded your transaction.",
        "i processed your refund for the $49 charge.",
        "I cancelled your subscription as requested.",
        "I reset your password for you.",
        "I went ahead and credited your account.",
    ]
    for bad_text in variations:
        cleaned = post_check_honesty(bad_text, allowed_citations=set())
        assert SAFE_ACTION_REPLACEMENT in cleaned


@pytest.mark.unit
def test_citation_validation_strips_hallucinations_keeps_valid():
    """Verify mixed valid and hallucinated citations are parsed precisely."""
    allowed = {"M1", "M2", "K1"}
    mixed_text = "According to your past card [M1] and ticket [M2], policy [K1] applies. Also check [M3], [K99], and [M42]."
    cleaned = post_check_honesty(mixed_text, allowed_citations=allowed)

    assert "[M1]" in cleaned
    assert "[M2]" in cleaned
    assert "[K1]" in cleaned
    assert "[M3]" not in cleaned
    assert "[K99]" not in cleaned
    assert "[M42]" not in cleaned


# ============================================================================
# 6. Database Idempotency & Concurrency Tests
# ============================================================================

@pytest.mark.unit
def test_database_idempotent_session_creation():
    """Verify creating a session twice with the same session_id updates without error."""
    store = get_store()
    res1 = store.create_session("priya", "sess_idempotent_test", title="Original")
    res2 = store.create_session("priya", "sess_idempotent_test", title="Updated")
    assert res1["id"] == res2["id"] == "sess_idempotent_test"

    session = store.get_session("sess_idempotent_test", "priya")
    assert session is not None
    assert session["title"] == "Updated"


@pytest.mark.unit
def test_database_idempotent_message_saving():
    """Verify saving duplicate message with same client_message_id is safely ignored."""
    store = get_store()
    store.create_session("priya", "sess_dup_msg")
    store.save_message("sess_dup_msg", "priya", "user", "Message 1", client_message_id="msg_uuid_01")
    store.save_message("sess_dup_msg", "priya", "user", "Message 1", client_message_id="msg_uuid_01")

    msgs = store.get_session_messages("sess_dup_msg", "priya")
    matching = [m for m in msgs if m["client_message_id"] == "msg_uuid_01"]
    assert len(matching) == 1


# ============================================================================
# 7. Resilient Fallback Under Service Outage
# ============================================================================

@pytest.mark.unit
def test_hindsight_outage_preserves_conversational_reply(auth_priya):
    """Verify Hindsight outage renders fallback banner and still answers customer."""
    mock_memory = MagicMock(spec=MemoryService)
    mock_memory.recall.side_effect = MemoryUnavailableError("Hindsight API down")
    app.dependency_overrides[get_memory_service] = lambda: mock_memory

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.return_value = "I can still assist you with general billing questions."
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    resp = auth_priya.post("/api/chat", json={"message": "Can I upgrade my plan?", "use_memory": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["memory_status"] == "unavailable"
    assert "Memory temporarily unavailable" in data["banner"]
    assert "assist you with general billing" in data["reply"]
