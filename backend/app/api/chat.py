"""
backend/app/api/chat.py
Chat and outcome API endpoints for PayNest customer support interactions with Hindsight persistent memory.
Enforces that customer identity is derived strictly from the verified bearer token.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from backend.app.core.errors import MemoryUnavailableError
from backend.app.db.store import DatabaseStore, get_store
from backend.app.models.schemas import (
    ChatRequest,
    ChatResponse,
    OutcomeRequest,
    OutcomeResponse,
)
from backend.app.services.agent import AgentService, get_agent_service
from backend.app.services.identity import get_current_customer
from backend.app.services.memory import MemoryService, get_memory_service

router = APIRouter(prefix="/api", tags=["chat"])


def _async_retain_turn(
    memory: MemoryService,
    customer_id: str,
    session_id: str,
    turn_no: int,
    user_text: str,
    agent_text: str,
    ticket_id: Optional[str] = None,
) -> None:
    """Safe background retention task."""
    try:
        memory.retain_turn(
            customer_id=customer_id,
            session_id=session_id,
            turn_no=turn_no,
            user_text=user_text,
            agent_text=agent_text,
            ticket_id=ticket_id,
        )
    except Exception:
        # Retention errors in background are safely caught without breaking client response
        pass


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message to the PayNest support assistant",
)
def chat_turn(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    customer_id: str = Depends(get_current_customer),
    agent: AgentService = Depends(get_agent_service),
    memory: MemoryService = Depends(get_memory_service),
):
    """
    Handles a customer chat turn:
    1. Authenticates customer strictly from signed bearer token (never from request body).
    2. Orchestrates turn via AgentService (recalls history/KB, builds query, invokes LLM, honesty guards).
    3. Persists turn and tickets to SQLite store for customer audit.
    4. Queues background memory retention in customer's isolated Hindsight bank.
    """
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    response, retain_payload = agent.process_turn(
        customer_id=customer_id,
        session_id=session_id,
        message=request.message,
        use_memory=request.use_memory,
        client_message_id=request.client_message_id,
    )

    if retain_payload:
        background_tasks.add_task(
            _async_retain_turn,
            memory=memory,
            customer_id=retain_payload["customer_id"],
            session_id=retain_payload["session_id"],
            turn_no=retain_payload["turn_no"],
            user_text=retain_payload["user_text"],
            agent_text=retain_payload["agent_text"],
            ticket_id=retain_payload.get("ticket_id"),
        )

    return response


@router.post(
    "/outcome",
    response_model=OutcomeResponse,
    status_code=status.HTTP_200_OK,
    summary="Record customer outcome (resolved or not_resolved) on a ticket or session",
)
def record_outcome(
    request: OutcomeRequest,
    customer_id: str = Depends(get_current_customer),
    memory: MemoryService = Depends(get_memory_service),
    store: DatabaseStore = Depends(get_store),
):
    """
    Records customer feedback on recommendations:
    1. Attaches outcome to existing ticket or creates a support ticket for the session.
    2. Persists outcome to SQLite outcomes table.
    3. Retains outcome to Hindsight customer memory bank for longitudinal tracking.
    """
    ticket_id = request.ticket_id
    session_id = request.session_id

    if not ticket_id:
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either ticket_id or session_id must be provided.",
            )
        ticket = store.get_latest_ticket_for_session(session_id, customer_id)
        if not ticket:
            ticket = store.create_ticket(
                customer_id=customer_id,
                session_id=session_id,
                topic="Billing & Payments Support",
            )
        ticket_id = ticket["id"]
    else:
        ticket = store.get_ticket(ticket_id, customer_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found or belongs to another customer.",
            )

    store.record_outcome(ticket_id=ticket_id, outcome=request.outcome, note=request.note)

    try:
        memory.retain_outcome(
            customer_id=customer_id,
            ticket_id=ticket_id,
            outcome=request.outcome,  # type: ignore[arg-type]
            note=request.note or "",
        )
    except Exception:
        pass

    return OutcomeResponse(
        status="recorded",
        ticket_id=ticket_id,
        outcome=request.outcome,
        message=f"Outcome '{request.outcome}' recorded successfully.",
    )


@router.get(
    "/customer/history",
    summary="Get customer session history with messages, tickets, and outcomes",
)
def get_customer_history(
    customer_id: str = Depends(get_current_customer),
    store: DatabaseStore = Depends(get_store),
):
    """Returns sessions, messages, and outcomes scoped strictly to the authenticated customer."""
    return store.get_customer_history(customer_id)
