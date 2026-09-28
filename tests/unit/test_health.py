"""
tests/unit/test_health.py
Unit tests for configuration validation, secret masking, and health endpoints.
"""

import pytest
from pydantic import ValidationError
from starlette.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import app


@pytest.mark.unit
def test_settings_masks_secrets_in_repr():
    """Verify that Settings.__repr__ never reveals raw secrets."""
    hindsight_secret = "hs_super_secret_key_12345"
    groq_secret = "gsk_super_secret_llm_key_67890"
    session_secret = "session_token_secret_abcdefghijk"

    s = Settings(
        HINDSIGHT_API_KEY=hindsight_secret,
        GROQ_API_KEY=groq_secret,
        SESSION_SECRET=session_secret,
        _env_file=None,
    )
    repr_str = repr(s)

    # Ensure full secrets are not exposed
    assert hindsight_secret not in repr_str
    assert groq_secret not in repr_str
    assert session_secret not in repr_str

    # Ensure masking pattern is present
    assert "********2345" in repr_str
    assert "********7890" in repr_str
    assert "********hijk" in repr_str


@pytest.mark.unit
def test_missing_required_env_var_raises():
    """Verify that missing required settings raise ValidationError listing missing fields."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,
        )
    errors = exc_info.value.errors()
    missing_fields = {e["loc"][0] for e in errors if e["type"] == "missing"}
    assert "HINDSIGHT_API_KEY" in missing_fields or "GROQ_API_KEY" in missing_fields


@pytest.mark.unit
def test_shallow_health_endpoint():
    """Verify GET /api/health returns 200 and the expected contract."""
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "env" in data
    assert data["hindsight"] == "unchecked"
    assert data["llm"] == "unchecked"


@pytest.mark.unit
def test_static_index_page_served():
    """Verify root / serves the frontend index.html."""
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "PayNest" in response.text


@pytest.mark.unit
def test_static_assets_served():
    """Verify static styles.css and app.js are served with 200 OK under / and /static."""
    client = TestClient(app)
    # Root paths
    css_resp = client.get("/styles.css")
    assert css_resp.status_code == 200
    assert "text/css" in css_resp.headers.get("content-type", "")

    js_resp = client.get("/app.js")
    assert js_resp.status_code == 200
    assert "javascript" in js_resp.headers.get("content-type", "")

    # /static/ prefixed paths
    static_css_resp = client.get("/static/styles.css")
    assert static_css_resp.status_code == 200
    assert "text/css" in static_css_resp.headers.get("content-type", "")

    static_js_resp = client.get("/static/app.js")
    assert static_js_resp.status_code == 200
    assert "javascript" in static_js_resp.headers.get("content-type", "")


@pytest.mark.unit
def test_settings_sanitizes_credentials_and_urls():
    """Verify that Settings strips whitespace, quotes, and Bearer prefixes from secrets and URLs."""
    s = Settings(
        HINDSIGHT_BASE_URL="  \"https://api.hindsight.test/\"  ",
        HINDSIGHT_API_KEY="  \"Bearer hs_token_with_quotes_and_prefix\"  ",
        GROQ_API_KEY=" 'gsk_token_with_single_quotes' ",
        SESSION_SECRET="  session_secret_with_spaces  ",
        _env_file=None,
    )
    assert s.HINDSIGHT_BASE_URL == "https://api.hindsight.test"
    assert s.HINDSIGHT_API_KEY == "hs_token_with_quotes_and_prefix"
    assert s.GROQ_API_KEY == "gsk_token_with_single_quotes"
    assert s.SESSION_SECRET == "session_secret_with_spaces"


