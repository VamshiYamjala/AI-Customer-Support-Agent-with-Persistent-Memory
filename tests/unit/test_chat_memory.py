"""
tests/unit/test_chat_memory.py
Unit tests verifying chat endpoint integration with MemoryService (ON/OFF toggle, fallback, and background retain).
"""

from unittest.mock import MagicMock
import pytest
from starlette.testclient import TestClient

from backend.app.core.errors import MemoryUnavailableError
from backend.app.main import app
from backend.app.models.schemas import MemoryItem
from backend.app.services.llm import LLMClient, get_llm_client
from backend.app.services.memory import MemoryService, get_memory_service


@pytest.fixture
def mock_deps():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.complete.return_value = "Hello! I remember your Visa card was declined previously [M1]."

    mock_memory = MagicMock(spec=MemoryService)
    app.dependency_overrides[get_llm_client] = lambda: mock_llm
    app.dependency_overrides[get_memory_service] = lambda: mock_memory

    yield mock_llm, mock_memory
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_deps):
    with TestClient(app) as c:
        yield c


@pytest.mark.unit
def test_chat_memory_on_recalls_and_injects(client, mock_deps):
    """Verify memory ON recalls memories and returns them in response."""
    mock_llm, mock_memory = mock_deps

    mock_memory.recall.return_value = [
        MemoryItem(id="mem_01", text="Visa ending 4242 failed at checkout", type="experience")
    ]
    mock_memory.recall_kb.return_value = []

    response = client.post(
        "/api/chat",
        json={
            "message": "It is happening again.",
            "customer_id": "priya",
            "use_memory": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["memory_status"] == "active"
    assert len(data["memories_used"]) == 1
    assert data["memories_used"][0]["id"] == "mem_01"
    assert "Visa ending 4242" in data["memories_used"][0]["text"]

    # Verify LLM was called with prompt containing recalled memory
    prompt_used = mock_llm.complete.call_args.kwargs["messages"][0]["content"]
    assert "CUSTOMER HISTORY" in prompt_used
    assert "Visa ending 4242" in prompt_used


@pytest.mark.unit
def test_chat_memory_off_skips_recall(client, mock_deps):
    """Verify memory OFF does not call memory.recall and returns memory_status='off'."""
    mock_llm, mock_memory = mock_deps

    response = client.post(
        "/api/chat",
        json={
            "message": "Hi, how do I reset my card?",
            "customer_id": "priya",
            "use_memory": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["memory_status"] == "off"
    assert len(data["memories_used"]) == 0
    mock_memory.recall.assert_not_called()

    # Prompt does not contain memories block
    prompt_used = mock_llm.complete.call_args.kwargs["messages"][0]["content"]
    assert "<memories>" not in prompt_used


@pytest.mark.unit
def test_chat_memory_unavailable_graceful_fallback(client, mock_deps):
    """Verify Hindsight outage does not crash chat; replies with warning banner."""
    mock_llm, mock_memory = mock_deps
    mock_memory.recall.side_effect = MemoryUnavailableError()

    response = client.post(
        "/api/chat",
        json={
            "message": "I need help with my account.",
            "customer_id": "priya",
            "use_memory": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["memory_status"] == "unavailable"
    assert data["banner"] is not None
    assert "Memory temporarily unavailable" in data["banner"]
    assert len(data["memories_used"]) == 0
