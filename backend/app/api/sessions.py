"""
backend/app/api/sessions.py
Session management endpoints ensuring strict customer isolation.
"""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.db.store import get_store
from backend.app.services.identity import get_current_customer

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="Optional custom session title.")


class SessionResponse(BaseModel):
    id: str
    customer_id: str
    created_at: str
    title: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    session_id: str
    customer_id: str
    role: str
    content: str
    created_at: str
    client_message_id: Optional[str] = None
    memory_saved_status: str


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    req: Optional[CreateSessionRequest] = None,
    customer_id: str = Depends(get_current_customer),
):
    """Creates a new session tied strictly to the authenticated customer."""
    store = get_store()
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    title = req.title if req and req.title else f"Support Session {session_id[:8]}"
    created = store.create_session(customer_id=customer_id, session_id=session_id, title=title)
    return SessionResponse(**created)


@router.get("", response_model=List[SessionResponse])
def list_my_sessions(
    customer_id: str = Depends(get_current_customer),
):
    """Lists all support sessions belonging strictly to the authenticated customer."""
    store = get_store()
    sessions = store.list_sessions(customer_id)
    return [SessionResponse(**s) for s in sessions]


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(
    session_id: str,
    customer_id: str = Depends(get_current_customer),
):
    """
    Retrieves message history for a session.
    Strict isolation: Returns 404 if the session belongs to another customer or does not exist.
    """
    store = get_store()
    session = store.get_session(session_id, customer_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or belongs to another customer.",
        )

    messages = store.get_session_messages(session_id, customer_id)
    return [MessageResponse(**m) for m in messages]
