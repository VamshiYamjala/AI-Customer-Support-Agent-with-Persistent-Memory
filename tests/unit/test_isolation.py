"""
tests/unit/test_isolation.py
Unit tests verifying strict customer isolation across SQLite, API sessions, and MemoryService.
Ensures cross-customer data leakage is impossible by design.
"""

from unittest.mock import MagicMock
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import MemoryItem
from backend.app.services.identity import create_token
from backend.app.services.llm import LLMClient, get_llm_client
from backend.app.services.memory import MemoryService, get_memory_service


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_isolation_sqlite(client):
    """
    Verify customer A cannot access customer B's session or messages.
    Returns HTTP 404 when customer B attempts to read customer A's session.
    """
    token_priya = create_token("priya")
    token_arjun = create_token("arjun")

    # Priya creates a support session
    create_res = client.post(
        "/api/sessions",
        headers={"Authorization": f"Bearer {token_priya}"},
        json={"title": "Priya's Private Billing Inquiry"},
    )
    assert create_res.status_code == 201
    session_id = create_res.json()["id"]

    # Priya can read her session messages
    priya_read = client.get(
        f"/api/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {token_priya}"},
    )
    assert priya_read.status_code == 200

    # Arjun attempts to read Priya's session messages -> MUST FAIL (404)
    arjun_attempt = client.get(
        f"/api/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {token_arjun}"},
    )
    assert arjun_attempt.status_code == 404
    assert "not found or belongs to another customer" in arjun_attempt.json()["detail"].lower()


@pytest.mark.unit
def test_no_client_supplied_bank_id_or_customer_id(client):
    """
    Verify backend ignores any client-supplied customer_id or bank_id in request body.
    Identity and bank_id are computed strictly from the verified Authorization token.
    """
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.return_value = "Verified response."

    mock_memory = MagicMock(spec=MemoryService)
    mock_memory.recall.return_value = []
    mock_memory.recall_kb.return_value = []

    app.dependency_overrides[get_llm_client] = lambda: mock_llm
    app.dependency_overrides[get_memory_service] = lambda: mock_memory

    token_priya = create_token("priya")

    # Priya attempts to spoof identity as Arjun in the body
    client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token_priya}"},
        json={
            "message": "What is my account status?",
            "customer_id": "arjun",  # Spoofed
            "bank_id": "cs-arjun",    # Spoofed
            "use_memory": True,
        },
    )

    # Server must call recall strictly for 'priya', never 'arjun'
    mock_memory.recall.assert_called_once()
    assert mock_memory.recall.call_args.kwargs["customer_id"] == "priya"


@pytest.mark.unit
def test_isolation_memory_service():
    """
    Verify MemoryService routes to separate bank IDs and enforces strict customer tags.
    """
    with pytest.MonkeyPatch.context() as mp:
        mock_client = MagicMock()
        mp.setattr("backend.app.services.memory.Hindsight", lambda **kw: mock_client)

        service = MemoryService(
            base_url="https://api.hindsight.test",
            api_key="test_key",
            bank_prefix="cs-",
        )
        service.client = mock_client

        # Priya retains secret
        service.retain_turn(
            customer_id="priya",
            session_id="sess_p",
            turn_no=1,
            user_text="The secret word is purple-umbrella",
            agent_text="Noted.",
        )
        assert mock_client.retain.call_args.kwargs["bank_id"] == "cs-priya"
        assert "customer:priya" in mock_client.retain.call_args.kwargs["tags"]

        # Arjun recalls
        mock_client.recall.return_value = MagicMock(results=[])
        res_arjun = service.recall(customer_id="arjun", query="purple-umbrella")

        assert mock_client.recall.call_args.kwargs["bank_id"] == "cs-arjun"
        assert mock_client.recall.call_args.kwargs["tags"] == ["customer:arjun"]
        assert len(res_arjun) == 0
