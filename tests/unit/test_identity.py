"""
tests/unit/test_identity.py
Unit tests for customer identity: token signing, verification, tampering, expiration, and header validation.
"""

import pytest
from fastapi import HTTPException
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.services.identity import create_token, verify_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.unit
def test_token_generation_and_verification():
    """Verify create_token generates a valid token that correctly verifies."""
    token = create_token("priya")
    assert isinstance(token, str)
    assert len(token) > 20

    verified_id = verify_token(token)
    assert verified_id == "priya"


@pytest.mark.unit
def test_token_tampered_fails():
    """Verify that altering even a single character in the token signature fails with 401."""
    token = create_token("priya")
    tampered = token[:-2] + ("xx" if token[-2:] != "xx" else "yy")

    with pytest.raises(HTTPException) as exc_info:
        verify_token(tampered)

    assert exc_info.value.status_code == 401
    assert "Invalid or tampered" in exc_info.value.detail


@pytest.mark.unit
def test_token_expired_fails():
    """Verify that expired tokens fail verification with 401."""
    token = create_token("priya")

    # max_age = -1 forces immediate expiration check failure
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, max_age=-1)

    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


@pytest.mark.unit
def test_api_me_requires_valid_bearer_token(client):
    """Verify GET /api/me rejects missing or malformed Authorization headers."""
    # Missing header
    res_no_auth = client.get("/api/me")
    assert res_no_auth.status_code == 401

    # Malformed header
    res_bad_format = client.get("/api/me", headers={"Authorization": "Basic 12345"})
    assert res_bad_format.status_code == 401

    # Valid token
    token = create_token("priya")
    res_valid = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert res_valid.status_code == 200
    assert res_valid.json()["id"] == "priya"
