"""
backend/app/api/chat.py
Chat API endpoint for PayNest customer support interactions.
"""

import uuid
from fastapi import APIRouter, Depends, status
from backend.app.models.schemas import ChatRequest, ChatResponse
from backend.app.prompts.system import render_system_prompt
from backend.app.services.llm import LLMClient, get_llm_client

router = APIRouter(prefix="/api", tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message to the PayNest support assistant",
)
def chat_turn(
    request: ChatRequest,
    llm: LLMClient = Depends(get_llm_client),
):
    """
    Handles a customer chat turn.
    In Level 3, memory is OFF by default and runs directly through the base LLM prompt.
    """
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"

    # Build prompt context
    system_prompt = render_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.message},
    ]

    # Execute LLM completion (exceptions handled by global AppException handler)
    reply_text = llm.complete(messages=messages, max_tokens=700, temperature=0.2)

    return ChatResponse(
        reply=reply_text,
        session_id=session_id,
        memories_used=[],
        memory_status="off",
        banner=None,
    )
