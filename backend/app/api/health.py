"""
backend/app/api/health.py
Health check endpoints for basic liveness and deep dependency verification.
"""

import logging
from fastapi import APIRouter, Response, status
from backend.app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """
    Shallow health check for container liveness probes.
    Does not make external network calls.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "hindsight": "unchecked",
        "llm": "unchecked",
    }


@router.get("/health/deep")
def deep_health_check(response: Response):
    """
    Deep health check verifying live reachability of Hindsight Cloud and Groq LLM.
    Never exposes internal error bodies, stack traces, or credentials.
    """
    settings = get_settings()

    hindsight_status = "ok"
    llm_status = "ok"

    # Check Hindsight
    try:
        from hindsight_client import Hindsight
        client = Hindsight(
            base_url=settings.HINDSIGHT_BASE_URL,
            api_key=settings.HINDSIGHT_API_KEY,
            timeout=10.0,
        )
        client.get_version()
        try:
            client.close()
        except Exception:
            pass
    except Exception as exc:
        logger.warning("Hindsight deep health check failed: %s", exc)
        hindsight_status = "down"

    # Check Groq LLM
    try:
        from groq import Groq
        groq_client = Groq(api_key=settings.GROQ_API_KEY, timeout=10.0)
        groq_client.models.list()
    except Exception as exc:
        logger.warning("Groq LLM deep health check failed: %s", exc)
        llm_status = "down"

    all_healthy = (hindsight_status == "ok") and (llm_status == "ok")
    overall_status = "ok" if all_healthy else "degraded"

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": overall_status,
        "hindsight": hindsight_status,
        "llm": llm_status,
    }
