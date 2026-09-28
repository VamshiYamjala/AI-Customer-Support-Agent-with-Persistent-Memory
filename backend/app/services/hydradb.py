"""
backend/app/services/hydradb.py
Graph database service integrating HydraDB (https://github.com/hydra-db/hydradb)
for GraphRAG knowledge tracking and entity-relationship context in customer support.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx

from backend.app.config import get_settings

logger = logging.getLogger(__name__)


class HydraDBService:
    """
    Client for HydraDB (https://github.com/hydra-db/hydradb).
    Provides GraphRAG relationship queries using OpenCypher and REST/Bolt endpoints.
    Enables tracking of customer tickets, topics, resolutions, and payment entities.
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        http_url: Optional[str] = None,
        bolt_url: Optional[str] = None,
        token: Optional[str] = None,
        namespace: Optional[str] = None,
        timeout: float = 3.0,
    ):
        settings = get_settings()
        self.enabled = settings.HYDRADB_ENABLED if enabled is None else enabled
        self.http_url = (http_url or settings.HYDRADB_HTTP_URL).rstrip("/")
        self.bolt_url = bolt_url or settings.HYDRADB_BOLT_URL
        self.token = token or settings.HYDRADB_TOKEN
        self.namespace = namespace or settings.HYDRADB_NAMESPACE
        self.timeout = timeout

    @property
    def headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "X-Graph-Namespace": self.namespace,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def is_healthy(self) -> bool:
        """Checks if HydraDB HTTP query service is accessible."""
        if not self.enabled:
            return False
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.http_url}/health", headers=self.headers)
                return resp.status_code in (200, 204)
        except Exception:
            return False

    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Executes an OpenCypher query against HydraDB HTTPS query endpoint.
        Returns tabular record rows or an empty list on fallback.
        """
        if not self.enabled:
            return []

        payload = {
            "query": query,
            "parameters": parameters or {},
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.http_url}/query",
                    json=payload,
                    headers=self.headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("results", [])
                logger.warning("HydraDB query returned %s: %s", resp.status_code, resp.text)
                return []
        except Exception as e:
            logger.debug("HydraDB unavailable (%s), continuing with standard memory fallback", e)
            return []

    def record_turn(
        self,
        customer_id: str,
        session_id: str,
        topic: str,
        entities: Optional[List[str]] = None,
        outcome: Optional[str] = None,
    ) -> bool:
        """
        Idempotently inserts or links nodes in HydraDB graph:
        (:Customer)-[:OPENED_SESSION]->(:Session)-[:CONCERNS]->(:Topic)
        """
        if not self.enabled:
            return False

        cypher = """
        MERGE (c:Customer {id: $customer_id})
        MERGE (s:Session {id: $session_id})
        MERGE (c)-[:OPENED_SESSION]->(s)
        MERGE (t:Topic {name: $topic})
        MERGE (s)-[:CONCERNS]->(t)
        """
        params: Dict[str, Any] = {
            "customer_id": customer_id,
            "session_id": session_id,
            "topic": topic,
        }

        if outcome:
            cypher += """
            MERGE (o:Outcome {status: $outcome})
            MERGE (s)-[:RESOLVED_AS]->(o)
            """
            params["outcome"] = outcome

        self.execute_cypher(cypher, params)
        return True

    def recall_graph_context(self, customer_id: str, topic: Optional[str] = None) -> List[str]:
        """
        Retrieves GraphRAG context for a customer.
        Returns human-readable relation summaries for prompt injection (e.g. [G1], [G2]).
        """
        if not self.enabled:
            return []

        cypher = """
        MATCH (c:Customer {id: $customer_id})-[:OPENED_SESSION]->(s:Session)-[:CONCERNS]->(t:Topic)
        OPTIONAL MATCH (s)-[:RESOLVED_AS]->(o:Outcome)
        RETURN s.id AS session, t.name AS topic, o.status AS outcome
        LIMIT 5
        """
        rows = self.execute_cypher(cypher, {"customer_id": customer_id})
        graph_insights: List[str] = []
        for idx, row in enumerate(rows, 1):
            session_id = row.get("session", "unknown")
            top = row.get("topic", "General Support")
            out = row.get("outcome")
            status_text = f"status: {out}" if out else "in progress"
            graph_insights.append(
                f"[G{idx}] Prior ticket in session {session_id[:8]} concerning '{top}' ({status_text})"
            )
        return graph_insights


_hydradb_instance: Optional[HydraDBService] = None


def get_hydradb_service() -> HydraDBService:
    global _hydradb_instance
    if _hydradb_instance is None:
        _hydradb_instance = HydraDBService()
    return _hydradb_instance
