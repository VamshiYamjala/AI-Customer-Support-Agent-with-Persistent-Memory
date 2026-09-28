"""
tests/integration/test_chat_live.py
Integration test verifying live chat completion via Groq LLM.
"""

import pytest
from starlette.testclient import TestClient
from backend.app.main import app


@pytest.mark.integration
def test_live_chat_completion():
    """Verify live POST /api/chat returns real response from configured Groq model."""
    client = TestClient(app)
    response = client.post(
        "/api/chat",
        json={
            "message": "Hi, I have a quick question about PayNest support.",
            "use_memory": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 0
    assert data["memory_status"] == "off"
