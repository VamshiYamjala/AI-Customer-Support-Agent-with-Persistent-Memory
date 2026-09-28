"""
tests/unit/test_rocketride_hydradb.py
Unit tests verifying RocketRide AI Pipeline service and HydraDB GraphRAG service.
"""

from unittest.mock import MagicMock, patch
import pytest

from backend.app.services.hydradb import HydraDBService
from backend.app.services.rocketride import RocketRideService


def test_rocketride_disabled_by_default():
    rr = RocketRideService(enabled=False)
    assert not rr.is_healthy()
    assert rr.execute_pipeline({"message": "test"}) is None


def test_rocketride_load_pipeline():
    rr = RocketRideService(pipeline_path="pipelines/support_agent.pipe")
    pipeline = rr.load_pipeline_definition()
    assert pipeline is not None
    assert pipeline["name"] == "paynest_support_agent_pipeline"
    assert "nodes" in pipeline
    assert "edges" in pipeline


def test_rocketride_execute_online():
    rr = RocketRideService(enabled=True, server_url="http://mock-rocketride:8080")
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"outputs": {"reply": "Handled by RocketRide pipeline."}}
        mock_post.return_value = mock_resp

        result = rr.execute_pipeline({"message": "hello"})
        assert result is not None
        assert result["reply"] == "Handled by RocketRide pipeline."


def test_hydradb_disabled_by_default():
    db = HydraDBService(enabled=False)
    assert not db.is_healthy()
    assert db.execute_cypher("MATCH (n) RETURN n") == []
    assert db.recall_graph_context("priya") == []


def test_hydradb_headers():
    db = HydraDBService(token="test-token", namespace="custom-ns")
    headers = db.headers
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["X-Graph-Namespace"] == "custom-ns"


def test_hydradb_query_and_recall():
    db = HydraDBService(enabled=True, token="token123", namespace="test-ns")
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"session": "sess_abc123", "topic": "Card Renewal", "outcome": "resolved"}
            ]
        }
        mock_post.return_value = mock_resp

        insights = db.recall_graph_context("priya")
        assert len(insights) == 1
        assert "[G1]" in insights[0]
        assert "Card Renewal" in insights[0]
        assert "resolved" in insights[0]
