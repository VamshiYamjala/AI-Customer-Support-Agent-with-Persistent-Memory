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
    customer_id: str = Field(
        default="priya",
        description="Validated customer identifier (default demo: priya).",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier for grouping turns.",
    )
    use_memory: bool = Field(
        default=True,
        description="Flag indicating whether to query persistent memory.",
    )

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or contain only whitespace.")
        return stripped

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not CUSTOMER_ID_REGEX.match(cleaned):
            raise ValueError(f"Invalid customer_id '{v}'. Must match ^[a-z0-9-]{{3,40}}$.")
        return cleaned


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


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
