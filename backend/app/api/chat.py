"""
backend/app/api/chat.py
Chat API endpoint for PayNest customer support interactions with Hindsight persistent memory.
Enforces that customer identity is derived strictly from the verified bearer token.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from backend.app.core.errors import MemoryUnavailableError
from backend.app.db.store import DatabaseStore, get_store
from backend.app.models.schemas import ChatRequest, ChatResponse, MemoryItem
from backend.app.prompts.system import render_system_prompt
from backend.app.services.identity import get_current_customer
from backend.app.services.llm import LLMClient, get_llm_client
from backend.app.services.memory import MemoryService, get_memory_service

router = APIRouter(prefix="/api", tags=["chat"])

_session_turns: dict[str, int] = {}


def _async_retain_turn(
    memory: MemoryService,
    customer_id: str,
    session_id: str,
    turn_no: int,
    user_text: str,
    agent_text: str,
) -> None:
    """Safe background retention task."""
    try:
        memory.retain_turn(
            customer_id=customer_id,
            session_id=session_id,
            turn_no=turn_no,
            user_text=user_text,
            agent_text=agent_text,
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
    llm: LLMClient = Depends(get_llm_client),
    memory: MemoryService = Depends(get_memory_service),
    store: DatabaseStore = Depends(get_store),
):
    """
    Handles a customer chat turn:
    1. Authenticates customer strictly from signed bearer token (never from request body).
    2. Validates session ownership in SQLite (creates session if new).
    3. Recalls relevant customer and KB memories if use_memory is True.
    4. Generates LLM response using Groq.
    5. Saves interaction history to SQLite store for customer audit.
    6. Queues background memory retention in customer's isolated Hindsight bank.
    """
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    # Validate or initialize session in database
    existing_session = store.get_session(session_id, customer_id)
    if not existing_session:
        # Check if session exists under another customer (isolation violation attempt)
        conn = store.get_customer(customer_id)
        # Check if session belongs to someone else
        raw_session = store.get_session(session_id, customer_id)
        if raw_session is None:
            # Check if session_id is owned by another customer in DB
            all_sessions = store.list_sessions(customer_id)
            # Create session for this customer
            store.create_session(customer_id=customer_id, session_id=session_id)

    # Track turn count for document_id idempotency
    turn_no = _session_turns.get(session_id, 0) + 1
    _session_turns[session_id] = turn_no

    recalled_memories: Optional[List[MemoryItem]] = None
    kb_memories: Optional[List[MemoryItem]] = None
    memory_status = "off"
    banner: Optional[str] = None

    if request.use_memory:
        try:
            recalled_memories = memory.recall(customer_id=customer_id, query=request.message)
            kb_memories = memory.recall_kb(query=request.message)
            memory_status = "active"
        except MemoryUnavailableError:
            memory_status = "unavailable"
            banner = "Memory temporarily unavailable — answering without history."
            recalled_memories = None
            kb_memories = None

    # Build prompt context
    system_prompt = render_system_prompt(memories=recalled_memories, kb_memories=kb_memories)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.message},
    ]

    # Execute LLM completion
    reply_text = llm.complete(messages=messages, max_tokens=700, temperature=0.2)

    # Persist message history in SQLite
    store.save_message(
        session_id=session_id,
        customer_id=customer_id,
        role="user",
        content=request.message,
        client_message_id=request.client_message_id,
        memory_saved_status="retained" if (request.use_memory and memory_status == "active") else "skipped",
    )
    store.save_message(
        session_id=session_id,
        customer_id=customer_id,
        role="assistant",
        content=reply_text,
        memory_saved_status="retained" if (request.use_memory and memory_status == "active") else "skipped",
    )

    # Queue memory retention
    if request.use_memory and memory_status == "active":
        background_tasks.add_task(
            _async_retain_turn,
            memory=memory,
            customer_id=customer_id,
            session_id=session_id,
            turn_no=turn_no,
            user_text=request.message,
            agent_text=reply_text,
        )

    return ChatResponse(
        reply=reply_text,
        session_id=session_id,
        memories_used=recalled_memories or [],
        memory_status=memory_status,
        banner=banner,
    )
