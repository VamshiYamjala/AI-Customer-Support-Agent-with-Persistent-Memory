"""
backend/app/services/rocketride.py
High-performance AI Pipeline service integrating RocketRide Server (https://github.com/rocketride-org/rocketride-server).
Executes .pipe defined multi-step agent graphs or falls back to native runtime.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import httpx

from backend.app.config import get_settings

logger = logging.getLogger(__name__)


class RocketRideService:
    """
    Client for RocketRide C++ Pipeline Server (https://github.com/rocketride-org/rocketride-server).
    Enables low-latency execution of AI customer support workflows defined in .pipe formats.
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        server_url: Optional[str] = None,
        pipeline_path: Optional[str] = None,
        timeout: float = 5.0,
    ):
        settings = get_settings()
        self.enabled = settings.ROCKETRIDE_ENABLED if enabled is None else enabled
        self.server_url = (server_url or settings.ROCKETRIDE_SERVER_URL).rstrip("/")
        self.pipeline_path = pipeline_path or settings.ROCKETRIDE_PIPELINE_PATH
        self.timeout = timeout
        self._cached_pipeline: Optional[Dict[str, Any]] = None

    def is_healthy(self) -> bool:
        """Checks if RocketRide C++ server instance is reachable."""
        if not self.enabled:
            return False
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.server_url}/health")
                return resp.status_code == 200
        except Exception:
            return False

    def load_pipeline_definition(self) -> Optional[Dict[str, Any]]:
        """Loads and caches the .pipe pipeline definition from disk."""
        if self._cached_pipeline is not None:
            return self._cached_pipeline

        p = Path(self.pipeline_path)
        if not p.is_absolute():
            # Resolve relative to project root
            root = Path(__file__).resolve().parent.parent.parent.parent
            p = root / self.pipeline_path

        if not p.exists():
            logger.warning("RocketRide pipeline file not found at %s", p)
            return None

        try:
            with open(p, "r", encoding="utf-8") as f:
                self._cached_pipeline = json.load(f)
                return self._cached_pipeline
        except Exception as e:
            logger.error("Failed to parse RocketRide pipeline file: %s", e)
            return None

    def execute_pipeline(self, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Executes the agent turn workflow through RocketRide server.
        Returns execution result dictionary or None if unreachable.
        """
        if not self.enabled:
            return None

        pipeline = self.load_pipeline_definition()
        payload = {
            "pipeline": pipeline,
            "inputs": inputs,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.server_url}/api/v1/pipelines/execute",
                    json=payload,
                )
                if resp.status_code == 200:
                    return resp.json().get("outputs")
                logger.warning("RocketRide server execution returned %s: %s", resp.status_code, resp.text)
                return None
        except Exception as e:
            logger.debug("RocketRide server execution offline (%s), using native agent runtime", e)
            return None


_rocketride_instance: Optional[RocketRideService] = None


def get_rocketride_service() -> RocketRideService:
    global _rocketride_instance
    if _rocketride_instance is None:
        _rocketride_instance = RocketRideService()
    return _rocketride_instance
