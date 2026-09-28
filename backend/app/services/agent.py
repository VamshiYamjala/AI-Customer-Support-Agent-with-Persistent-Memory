"""
backend/app/services/agent.py
Core Support Agent orchestration service for PayNest.
Executes the full agent turn loop:
1. Validates identity and session ownership.
2. Builds search query from current turn and recent context.
3. Recalls memories from customer bank and shared KB bank.
4. Renders prompt with strict rules, citations, and conversation history.
5. Invokes LLM with exponential retry.
6. Runs post-check honesty guardrails (strips unsupported action claims & validates citations).
7. Persists turn to SQLite and queues background memory retention.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from fastapi import Depends

from backend.app.core.errors import MemoryUnavailableError
from backend.app.db.store import DatabaseStore, get_store
from backend.app.models.schemas import ChatResponse, MemoryItem
from backend.app.prompts.system import render_system_prompt
from backend.app.services.llm import LLMClient, get_llm_client
from backend.app.services.memory import MemoryService, get_memory_service
from backend.app.services.rocketride import RocketRideService, get_rocketride_service
from backend.app.services.hydradb import HydraDBService, get_hydradb_service
from backend.app.services.sanitize import sanitize_for_memory

# Regex detecting unauthorized action claims by the agent
UNAUTHORIZED_ACTION_PATTERNS = [
    re.compile(r"(?i)\b(?:I(?:'ve| have)? (?:refunded|processed (?:your|the) refund|cancelled your subscription|reset your password|fixed your (?:account|charge|card)))\b"),
    re.compile(r"(?i)\b(?:your (?:refund|payment) has been (?:issued|processed|completed|fixed) by me)\b"),
    re.compile(r"(?i)\b(?:I (?:went ahead and )?(?:credited|waived|adjusted) your (?:account|bill|invoice))\b"),
]

SAFE_ACTION_REPLACEMENT = (
    "I do not have direct access to process transactions, modify billing, or issue refunds directly. "
    "However, I have documented this details and can submit a priority ticket to our human billing team for you."
)

# Matches Hindsight memory ([M1]), Knowledge Base ([K1]), and HydraDB graph ([G1]) citations
CITATION_PATTERN = re.compile(r"\[(M\d+|K\d+|G\d+)\]")


def build_recall_query(message: str, recent_messages: List[Dict[str, Any]]) -> str:
    """
    Builds a concise semantic recall query from the new message and recent context.
    Keeps length strictly within 40 words to remain well within Hindsight limits.
    """
    cleaned = message.strip()
    if not recent_messages:
        return cleaned[:200]

    # Extract user keywords from previous turn if relevant
    prev_user_msgs = [m["content"] for m in recent_messages if m.get("role") == "user"]
    if prev_user_msgs:
        last_msg = prev_user_msgs[-1][:100]
        query = f"{cleaned} (context: {last_msg})"
    else:
        query = cleaned

    words = query.split()
    if len(words) > 35:
        query = " ".join(words[:35])
    return query


def post_check_honesty(reply: str, allowed_citations: Set[str]) -> str:
    """
    Guards against hallucinated capabilities and invalid citations:
    1. Replaces false action claims (e.g. 'I refunded your card') with honest support boundaries.
    2. Strips any memory/KB citations [M#] or [K#] that were not part of the injected context.
    """
    checked_reply = reply

    # 1. Action claim guardrail
    for pattern in UNAUTHORIZED_ACTION_PATTERNS:
        if pattern.search(checked_reply):
            checked_reply = pattern.sub(SAFE_ACTION_REPLACEMENT, checked_reply)

    # 2. Citation validity check
    def validate_citation(match: re.Match) -> str:
        cite = match.group(1)
        if cite in allowed_citations:
            return match.group(0)
        # Strip invalid citation tag
        return ""

    checked_reply = CITATION_PATTERN.sub(validate_citation, checked_reply)
    # Clean up any leftover double spaces
    checked_reply = re.sub(r" +", " ", checked_reply).strip()

    return checked_reply


class AgentService:
    """Orchestrates the PayNest support decision loop with Hindsight, RocketRide, and HydraDB."""

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        memory: Optional[MemoryService] = None,
        store: Optional[DatabaseStore] = None,
        rocketride: Optional[RocketRideService] = None,
        hydradb: Optional[HydraDBService] = None,
    ):
        self.llm = llm or get_llm_client()
        self.memory = memory or get_memory_service()
        self.store = store or get_store()
        self.rocketride = rocketride or get_rocketride_service()
        self.hydradb = hydradb or get_hydradb_service()

    def process_turn(
        self,
        customer_id: str,
        session_id: str,
        message: str,
        use_memory: bool = True,
        client_message_id: Optional[str] = None,
    ) -> Tuple[ChatResponse, Optional[dict]]:
        """
        Executes a single conversational support turn.
        Returns (ChatResponse, background_retain_payload).
        """
        # Step 1: Ensure session exists in SQLite store for auditing and continuity
        session = self.store.get_session(session_id, customer_id)
        if not session:
            self.store.create_session(customer_id=customer_id, session_id=session_id)

        # Step 2: Ensure an associated support ticket exists for this session
        ticket = self.store.get_latest_ticket_for_session(session_id, customer_id)
        if not ticket:
            ticket = self.store.create_ticket(
                customer_id=customer_id,
                session_id=session_id,
                topic="Billing & Payments Support",
            )

        # Step 3: Retrieve recent conversation turns to provide prompt history & recall context
        recent_history = self.store.get_session_messages(session_id, customer_id)
        turn_no = (len(recent_history) // 2) + 1

        recalled_memories: Optional[List[MemoryItem]] = None
        kb_memories: Optional[List[MemoryItem]] = None
        graph_context: List[str] = []
        memory_status = "off"
        banner: Optional[str] = None
        allowed_citations: Set[str] = set()

        # Step 4: Multi-modal memory recall from Hindsight & HydraDB GraphRAG
        if use_memory:
            query = build_recall_query(message, recent_history)
            try:
                # Retrieve isolated customer-specific history and shared company policies from Hindsight
                recalled_memories = self.memory.recall(customer_id=customer_id, query=query)
                kb_memories = self.memory.recall_kb(query=query)
                memory_status = "active"

                # Populate allowed citation identifiers ([M1], [K1])
                for idx in range(1, len(recalled_memories) + 1):
                    allowed_citations.add(f"M{idx}")
                for idx in range(1, len(kb_memories or []) + 1):
                    allowed_citations.add(f"K{idx}")

            except MemoryUnavailableError:
                # Graceful degradation if Hindsight service is unreachable or rate-limited
                memory_status = "unavailable"
                banner = "Memory temporarily unavailable — answering without history."
                recalled_memories = None
                kb_memories = None

            # Retrieve GraphRAG context from HydraDB
            try:
                graph_context = self.hydradb.recall_graph_context(customer_id=customer_id)
                for idx in range(1, len(graph_context) + 1):
                    allowed_citations.add(f"G{idx}")
            except Exception:
                graph_context = []

        # Step 5: Render dynamic system prompt with verified memories, KB, and HydraDB graph relations
        system_prompt = render_system_prompt(
            memories=recalled_memories,
            kb_memories=kb_memories,
            graph_context=graph_context,
        )

        # Step 6: Assemble dialogue payload including bounded sliding window of past messages
        messages = [{"role": "system", "content": system_prompt}]
        for turn in recent_history[-6:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": message})

        # Step 7: Inference execution (RocketRide AI Pipeline Engine or Native Groq fallback)
        pipeline_engine = "native"
        raw_reply: Optional[str] = None

        if self.rocketride.enabled and self.rocketride.is_healthy():
            rr_output = self.rocketride.execute_pipeline({
                "customer_id": customer_id,
                "session_id": session_id,
                "message": message,
                "use_memory": use_memory,
                "system_prompt": system_prompt,
            })
            if rr_output and "reply" in rr_output:
                raw_reply = str(rr_output["reply"])
                pipeline_engine = "rocketride"

        if raw_reply is None:
            raw_reply = self.llm.complete(messages=messages, max_tokens=700, temperature=0.2)
            pipeline_engine = "native"

        # Post-check honesty guardrails
        final_reply = post_check_honesty(raw_reply, allowed_citations)

        # Persist turn in SQLite
        self.store.save_message(
            session_id=session_id,
            customer_id=customer_id,
            role="user",
            content=message,
            client_message_id=client_message_id,
            memory_saved_status="retained" if (use_memory and memory_status == "active") else "skipped",
        )
        self.store.save_message(
            session_id=session_id,
            customer_id=customer_id,
            role="assistant",
            content=final_reply,
            memory_saved_status="retained" if (use_memory and memory_status == "active") else "skipped",
        )

        # Record entity-relationship turn in HydraDB graph
        if ticket:
            try:
                self.hydradb.record_turn(
                    customer_id=customer_id,
                    session_id=session_id,
                    topic=ticket["topic"],
                )
            except Exception:
                pass

        retain_payload = None
        if use_memory and memory_status == "active":
            retain_payload = {
                "customer_id": customer_id,
                "session_id": session_id,
                "turn_no": turn_no,
                "user_text": message,
                "agent_text": final_reply,
                "ticket_id": ticket["id"] if ticket else None,
            }

        all_used_memories: List[MemoryItem] = []
        if recalled_memories:
            all_used_memories.extend(recalled_memories)
        if kb_memories:
            all_used_memories.extend(kb_memories)

        response = ChatResponse(
            reply=final_reply,
            session_id=session_id,
            memories_used=all_used_memories,
            memory_status=memory_status,
            banner=banner,
            pipeline_engine=pipeline_engine,
            graph_context=graph_context,
        )

        return response, retain_payload


def get_agent_service(
    llm: LLMClient = Depends(get_llm_client),
    memory: MemoryService = Depends(get_memory_service),
    store: DatabaseStore = Depends(get_store),
    rocketride: RocketRideService = Depends(get_rocketride_service),
    hydradb: HydraDBService = Depends(get_hydradb_service),
) -> AgentService:
    return AgentService(
        llm=None if hasattr(llm, "dependency") else llm,
        memory=None if hasattr(memory, "dependency") else memory,
        store=None if hasattr(store, "dependency") else store,
        rocketride=None if hasattr(rocketride, "dependency") else rocketride,
        hydradb=None if hasattr(hydradb, "dependency") else hydradb,
    )

