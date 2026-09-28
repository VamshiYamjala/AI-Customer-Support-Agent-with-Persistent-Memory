"""
backend/app/models/schemas.py
Pydantic request and response schemas for chat, memory, and error responses.
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

CUSTOMER_ID_REGEX = re.compile(r"^[a-z0-9-]{3,40}$")


class MemoryItem(BaseModel):
    id: str = Field(..., description="Unique memory ID or reference tag.")
    text: str = Field(..., description="Extracted memory fact or statement.")
    type: str = Field(default="experience", description="Memory type: world, experience, or observation.")
    context: Optional[str] = Field(default=None, description="Original context of the memory.")
    occurred_start: Optional[str] = Field(default=None, description="When the event occurred.")
    occurred_end: Optional[str] = Field(default=None, description="When the event ended.")
    mentioned_at: Optional[str] = Field(default=None, description="When the memory was first recorded.")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the memory.")
    document_id: Optional[str] = Field(default=None, description="Idempotent document ID.")
    score: Optional[float] = Field(default=None, description="Relevance score.")


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The customer's message text (1-2000 chars).",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier for grouping turns.",
    )
    client_message_id: Optional[str] = Field(
        default=None,
        description="Client-side idempotency identifier.",
    )
    use_memory: bool = Field(
        default=True,
        description="Flag indicating whether to query persistent memory.",
    )
    # Ignored if supplied by client to prevent identity spoofing
    customer_id: Optional[str] = Field(
        default=None,
        description="Ignored. Identity is resolved server-side from bearer token.",
    )

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or contain only whitespace.")
        return stripped


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Assistant reply message.")
    session_id: Optional[str] = Field(default=None, description="Active session ID.")
    memories_used: List[MemoryItem] = Field(
        default_factory=list,
        description="List of memories recalled and used in this turn.",
    )
    memory_status: str = Field(
        default="off",
        description="Memory status: 'active', 'off', or 'unavailable'.",
    )
    banner: Optional[str] = Field(
        default=None,
        description="Informational banner (e.g. when memory is temporarily unavailable).",
    )
    pipeline_engine: Optional[str] = Field(
        default="native",
        description="Execution pipeline engine: 'rocketride' or 'native'.",
    )
    graph_context: List[str] = Field(
        default_factory=list,
        description="GraphRAG entity relations recalled from HydraDB.",
    )


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class OutcomeRequest(BaseModel):
    ticket_id: Optional[str] = Field(default=None, description="Ticket ID, if known.")
    session_id: Optional[str] = Field(default=None, description="Session ID to attach outcome to.")
    outcome: str = Field(..., description="Outcome status: 'resolved' or 'not_resolved'.")
    note: Optional[str] = Field(default="", description="Optional feedback note from customer.")

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in ("resolved", "not_resolved"):
            raise ValueError("Outcome must be either 'resolved' or 'not_resolved'.")
        return cleaned


class OutcomeResponse(BaseModel):
    status: str
    ticket_id: str
    outcome: str
    message: str

