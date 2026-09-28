"""
backend/app/services/identity.py
Customer authentication and session identity service using itsdangerous signed tokens.
Enforces that customer identity is computed strictly server-side.
"""

from typing import Optional
from fastapi import Header, HTTPException, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from backend.app.config import get_settings
from backend.app.db.store import get_store


def get_serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    return URLSafeTimedSerializer(secret_key=settings.SESSION_SECRET, salt="paynest-auth")


def create_token(customer_id: str) -> str:
    """Generates a cryptographically signed token for a customer."""
    serializer = get_serializer()
    return serializer.dumps({"customer_id": customer_id.lower().strip()})


def verify_token(token: str, max_age: int = 43200) -> str:
    """
    Verifies token signature and expiration (default 12 hours = 43,200 seconds).
    Returns verified customer_id.
    """
    serializer = get_serializer()
    try:
        data = serializer.loads(token, max_age=max_age)
        customer_id = data.get("customer_id")
        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
            )
        return str(customer_id)
    except SignatureExpired as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please log in again.",
        ) from e
    except BadSignature as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or tampered session token.",
        ) from e


def get_current_customer(authorization: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency extracting and validating the authenticated customer from Authorization header.
    Rejects any request without a valid Bearer token.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Please log in.",
        )

    parts = authorization.strip().split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'.",
        )

    token = parts[1]
    customer_id = verify_token(token)

    # Verify customer exists in database
    store = get_store()
    customer = store.get_customer(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Customer '{customer_id}' does not exist.",
        )

    return customer_id
