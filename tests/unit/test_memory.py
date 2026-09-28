"""
tests/unit/test_memory.py
Unit tests for MemoryService: bank isolation, retention, sanitization, recall, and error handling.
"""

from unittest.mock import MagicMock, patch
import pytest

from backend.app.core.errors import MemoryUnavailableError
from backend.app.models.schemas import MemoryItem
from backend.app.services.memory import MemoryService
from backend.app.services.sanitize import sanitize_for_memory


@pytest.fixture
def mock_hindsight_service():
    """Returns a MemoryService instance with a mocked Hindsight client."""
    with patch("backend.app.services.memory.Hindsight") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        service = MemoryService(
            base_url="https://api.hindsight.test",
            api_key="test_key",
            bank_prefix="cs-",
            shared_kb_bank="support-kb",
        )
        service.client = mock_client
        yield service, mock_client


@pytest.mark.unit
def test_bank_id_for(mock_hindsight_service):
    """Verify bank ID computation and validation."""
    service, _ = mock_hindsight_service

    assert service.bank_id_for("priya") == "cs-priya"
    assert service.bank_id_for("Arjun-1") == "cs-arjun-1"

    with pytest.raises(ValueError):
        service.bank_id_for("a")  # too short (< 3 chars)

    with pytest.raises(ValueError):
        service.bank_id_for("invalid_customer!")  # invalid characters


@pytest.mark.unit
def test_ensure_bank_idempotent(mock_hindsight_service):
    """Verify ensure_bank creates bank and caches result."""
    service, mock_client = mock_hindsight_service

    service.ensure_bank("priya")
    assert mock_client.create_bank.call_count == 1

    # Second call should use cache
    service.ensure_bank("priya")
    assert mock_client.create_bank.call_count == 1


@pytest.mark.unit
def test_retain_turn_sanitization_and_params(mock_hindsight_service):
    """Verify retain_turn redacts card details/passwords and sends strict customer tags."""
    service, mock_client = mock_hindsight_service

    user_msg = "My Visa 4111 2222 3333 4444 failed with cvv 123. password: secretpassword"
    agent_msg = "Please verify your billing address."

    service.retain_turn(
        customer_id="priya",
        session_id="sess_123",
        turn_no=1,
        user_text=user_msg,
        agent_text=agent_msg,
        ticket_id="T-45",
    )

    mock_client.retain.assert_called_once()
    kwargs = mock_client.retain.call_args.kwargs

    assert kwargs["bank_id"] == "cs-priya"
    assert kwargs["document_id"] == "sess_123-t1"
    assert "customer:priya" in kwargs["tags"]
    assert "ticket:T-45" in kwargs["tags"]

    # Verify sensitive data is redacted in content
    retained_content = kwargs["content"]
    assert "4111 2222 3333 4444" not in retained_content
    assert "****-****-****-4444" in retained_content
    assert "123" not in retained_content
    assert "[CVV_REDACTED]" in retained_content
    assert "secretpassword" not in retained_content


@pytest.mark.unit
def test_recall_maps_to_memory_items(mock_hindsight_service):
    """Verify recall maps SDK results to MemoryItem with all_strict customer tag scoping."""
    service, mock_client = mock_hindsight_service

    mock_r1 = MagicMock()
    mock_r1.id = "mem_001"
    mock_r1.text = "Customer preferred email communication."
    mock_r1.type = "world"
    mock_r1.occurred_start = "2026-09-28T10:00:00Z"
    mock_r1.tags = ["customer:priya"]

    mock_resp = MagicMock()
    mock_resp.results = [mock_r1]
    mock_client.recall.return_value = mock_resp

    items = service.recall(customer_id="priya", query="preferred channel")

    assert len(items) == 1
    assert isinstance(items[0], MemoryItem)
    assert items[0].id == "mem_001"
    assert items[0].text == "Customer preferred email communication."
    assert items[0].type == "world"

    # Verify query parameters
    call_kwargs = mock_client.recall.call_args.kwargs
    assert call_kwargs["bank_id"] == "cs-priya"
    assert call_kwargs["tags"] == ["customer:priya"]
    assert call_kwargs["tags_match"] == "all_strict"


@pytest.mark.unit
def test_recall_handles_memory_unavailable(mock_hindsight_service):
    """Verify Hindsight client error raises clean MemoryUnavailableError."""
    service, mock_client = mock_hindsight_service
    mock_client.recall.side_effect = Exception("Hindsight service timeout")

    with pytest.raises(MemoryUnavailableError):
        service.recall(customer_id="priya", query="anything")


@pytest.mark.unit
def test_customer_isolation_unit(mock_hindsight_service):
    """Verify separate customer IDs route to strictly separated banks."""
    service, mock_client = mock_hindsight_service

    service.recall(customer_id="priya", query="issues")
    assert mock_client.recall.call_args.kwargs["bank_id"] == "cs-priya"
    assert mock_client.recall.call_args.kwargs["tags"] == ["customer:priya"]

    service.recall(customer_id="arjun", query="issues")
    assert mock_client.recall.call_args.kwargs["bank_id"] == "cs-arjun"
    assert mock_client.recall.call_args.kwargs["tags"] == ["customer:arjun"]
