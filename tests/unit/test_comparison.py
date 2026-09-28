"""
tests/unit/test_comparison.py
Unit tests verifying persistent-learning demonstration, memory ON vs OFF divergence,
cross-session memory recall, and customer isolation.
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
def auth_client():
    app.dependency_overrides.clear()
    token = create_token("priya")
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def arjun_client():
    app.dependency_overrides.clear()
    token = create_token("arjun")
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_memory_on_vs_off_prompt_divergence(auth_client):
    """
    Verify that the identical customer message produces different prompts and behavior
    between memory ON and memory OFF.
    """
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.return_value = "Response from assistant."
    mock_memory = MagicMock(spec=MemoryService)

    app.dependency_overrides[get_llm_client] = lambda: mock_llm
    app.dependency_overrides[get_memory_service] = lambda: mock_memory

    # Setup recalled memory for Memory ON
    mock_memory.recall.return_value = [
        MemoryItem(
            id="mem_visa_4242",
            text="Customer Visa ending 4242 failed on Pro subscription renewal. Updating address did not resolve it.",
            type="experience",
        )
    ]
    mock_memory.recall_kb.return_value = []

    # 1. Send with memory OFF
    resp_off = auth_client.post(
        "/api/chat",
        json={"message": "It is happening again today.", "use_memory": False},
    )
    assert resp_off.status_code == 200
    data_off = resp_off.json()
    assert data_off["memory_status"] == "off"
    assert len(data_off["memories_used"]) == 0
    prompt_off = mock_llm.complete.call_args_list[-1][1]["messages"][0]["content"]
    assert "<memories>" not in prompt_off
    assert "Visa ending 4242" not in prompt_off

    # 2. Send with memory ON
    resp_on = auth_client.post(
        "/api/chat",
        json={"message": "It is happening again today.", "use_memory": True},
    )
    assert resp_on.status_code == 200
    data_on = resp_on.json()
    assert data_on["memory_status"] == "active"
    assert len(data_on["memories_used"]) == 1
    assert data_on["memories_used"][0]["id"] == "mem_visa_4242"
    prompt_on = mock_llm.complete.call_args_list[-1][1]["messages"][0]["content"]
    assert "<memories>" in prompt_on
    assert "Visa ending 4242" in prompt_on


@pytest.mark.unit
def test_cross_session_memory_retrieval(auth_client):
    """
    Verify that in a brand-new session (Session 2), the agent retrieves memories
    established in an earlier session (Session 1).
    """
    mock_llm = MagicMock(spec=LLMClient)
    mock_memory = MagicMock(spec=MemoryService)
    app.dependency_overrides[get_llm_client] = lambda: mock_llm
    app.dependency_overrides[get_memory_service] = lambda: mock_memory

    # Mock historical memory recalled from Session 1
    mock_memory.recall.return_value = [
        MemoryItem(
            id="sess_priya_01-t1",
            text="Customer prefers email communications and never wants phone calls for billing updates.",
            type="observation",
        )
    ]
    mock_memory.recall_kb.return_value = []
    mock_llm.complete.return_value = "I have noted your preference [M1] and will follow up via email."

    # Send in a brand-new session (sess_2)
    resp = auth_client.post(
        "/api/chat",
        json={
            "session_id": "sess_priya_new_02",
            "message": "Can someone update me on my billing ticket?",
            "use_memory": True,
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "sess_priya_new_02"
    assert len(data["memories_used"]) == 1
    assert "email communications" in data["memories_used"][0]["text"]
    assert "[M1]" in data["reply"]


@pytest.mark.unit
def test_customer_isolation_cross_session_no_leakage(auth_client, arjun_client):
    """
    Verify that customer Arjun cannot access or recall Priya's persistent memories.
    """
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.return_value = "I see no past card records on your account."
    mock_memory = MagicMock(spec=MemoryService)
    app.dependency_overrides[get_llm_client] = lambda: mock_llm
    app.dependency_overrides[get_memory_service] = lambda: mock_memory

    # When querying Arjun's bank, recall returns empty or Arjun-only memories
    def mock_recall(customer_id, query):
        if customer_id == "priya":
            return [MemoryItem(id="mem_p1", text="Priya's Visa card 4242 failed", type="experience")]
        elif customer_id == "arjun":
            return []  # Arjun has no card failure memories
        return []

    mock_memory.recall.side_effect = mock_recall
    mock_memory.recall_kb.return_value = []

    # Arjun asks what card was failing
    resp = arjun_client.post(
        "/api/chat",
        json={"message": "Which of my credit cards had an issue?", "use_memory": True},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["memories_used"]) == 0
    # Verify recall was called with Arjun's customer_id, not Priya's
    assert mock_memory.recall.call_args.kwargs["customer_id"] == "arjun"


@pytest.mark.unit
def test_memory_empty_when_no_relevant_history(auth_client):
    """
    Verify that when Hindsight finds no relevant memories, the agent proceeds honestly
    without hallucinating facts.
    """
    mock_llm = MagicMock(spec=LLMClient)
    mock_memory = MagicMock(spec=MemoryService)
    app.dependency_overrides[get_llm_client] = lambda: mock_llm
    app.dependency_overrides[get_memory_service] = lambda: mock_memory

    mock_memory.recall.return_value = []
    mock_memory.recall_kb.return_value = []
    mock_llm.complete.return_value = "Welcome to PayNest! How can I assist you with your account today?"

    resp = auth_client.post(
        "/api/chat",
        json={"message": "Hello, I am a new subscriber.", "use_memory": True},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["memories_used"]) == 0
    assert data["memory_status"] == "active"
    prompt_used = mock_llm.complete.call_args[1]["messages"][0]["content"]
    assert "No relevant history found" in prompt_used
