"""
tests/integration/test_health_deep.py
Integration test for GET /api/health/deep with real Hindsight and Groq connections.
"""

import pytest
from starlette.testclient import TestClient
from backend.app.main import app


@pytest.mark.integration
def test_deep_health_live():
    """Verify GET /api/health/deep connects to real services and returns 200 ok."""
    client = TestClient(app)
    response = client.get("/api/health/deep")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["hindsight"] == "ok"
    assert data["llm"] == "ok"
