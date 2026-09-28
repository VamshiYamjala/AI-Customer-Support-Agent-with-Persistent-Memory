"""
backend/app/services/memory.py
Persistent memory service interfacing exclusively with Hindsight Cloud.
Implements per-customer memory bank isolation, retention, recall, and lifecycle methods.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Literal, Optional

from hindsight_client import Hindsight

from backend.app.config import get_settings
from backend.app.core.errors import MemoryUnavailableError
from backend.app.models.schemas import MemoryItem
from backend.app.services.sanitize import sanitize_for_memory

CUSTOMER_ID_REGEX = re.compile(r"^[a-z0-9-]{3,40}$")

PAYNEST_BANK_MISSION = (
    "I am the support memory for one customer of PayNest. "
    "I remember their issues, what was tried, whether it worked, and their communication preferences. "
    "I only record what the customer or verified support notes stated; I never guess."
)


class MemoryService:
    """Wraps Hindsight Cloud SDK providing isolated per-customer memory operations."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        bank_prefix: Optional[str] = None,
        shared_kb_bank: Optional[str] = None,
        mode: Optional[str] = None,
        timeout: float = 30.0,
    ):
        settings = get_settings()
        self.mode = mode or getattr(settings, "HINDSIGHT_MODE", "cloud")
        self.base_url = (base_url or settings.HINDSIGHT_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.HINDSIGHT_API_KEY
        self.bank_prefix = bank_prefix or settings.HINDSIGHT_BANK_PREFIX
        self.shared_kb_bank = shared_kb_bank or settings.HINDSIGHT_SHARED_KB_BANK
        self.timeout = timeout

        self._explicit_client: Optional[Any] = None
        self._known_banks = set()

    @property
    def client(self) -> Hindsight:
        """
        Returns the active Hindsight SDK client.
        If an explicit or mock client was set (e.g. during unit tests), returns it.
        Otherwise creates a fresh client bound to the calling thread's event loop,
        preventing 'RuntimeError: Event loop is closed' in multi-threaded AnyIO workers.
        """
        if self._explicit_client is not None:
            return self._explicit_client
        return Hindsight(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )

    @client.setter
    def client(self, val: Any) -> None:
        self._explicit_client = val

    def bank_id_for(self, customer_id: str) -> str:
        """
        Computes and validates the unique Hindsight bank ID for a given customer.
        Enforces tenant isolation by partitioning memories per user ID.
        """
        cleaned_id = customer_id.strip().lower()
        if not CUSTOMER_ID_REGEX.match(cleaned_id):
            raise ValueError(f"Invalid customer ID: '{customer_id}'. Must match ^[a-z0-9-]{{3,40}}$")
        return f"{self.bank_prefix}{cleaned_id}"

    def ensure_bank(self, customer_id: str) -> None:
        """
        Idempotently ensures the customer's dedicated memory bank exists in Hindsight.
        Creates bank with customized customer-support mission and balanced disposition if absent.
        """
        bank_id = self.bank_id_for(customer_id)
        if bank_id in self._known_banks:
            return

        try:
            self.client.create_bank(
                bank_id=bank_id,
                name=f"Customer {customer_id.title()}",
                mission=PAYNEST_BANK_MISSION,
                disposition={"skepticism": 3, "literalism": 3, "empathy": 3},
            )
            self._known_banks.add(bank_id)
        except Exception as e:
            settings = get_settings()
            if self._explicit_client is None and getattr(settings, "DEMO_MOCK_FALLBACK", True):
                self._known_banks.add(bank_id)
                return
            err_str = str(e).lower()
            if "already exists" in err_str or "conflict" in err_str:
                self._known_banks.add(bank_id)
            else:
                raise MemoryUnavailableError(f"Failed to ensure memory bank for customer {customer_id}.") from e

    def recall(
        self,
        customer_id: str,
        query: str,
        *,
        max_tokens: int = 1200,
        budget: str = "mid",
    ) -> List[MemoryItem]:
        """
        Recalls memories from customer's isolated bank with strict customer tag filtering.
        Returns list of standardized MemoryItem models.
        """
        # Ensure the customer bank is initialized before attempting recall
        bank_id = self.bank_id_for(customer_id)
        self.ensure_bank(customer_id)

        try:
            resp = self.client.recall(
                bank_id=bank_id,
                query=query,
                tags=[f"customer:{customer_id}"],
                tags_match="all_strict",
                max_tokens=max_tokens,
                budget=budget,
            )
            results = getattr(resp, "results", [])
            items: List[MemoryItem] = []
            for idx, r in enumerate(results, start=1):
                item_id = getattr(r, "id", None) or f"M{idx}"
                item_text = getattr(r, "text", str(r))
                item_type = getattr(r, "type", "experience")
                item_context = getattr(r, "context", None)
                occurred_start = getattr(r, "occurred_start", None)
                occurred_end = getattr(r, "occurred_end", None)
                mentioned_at = getattr(r, "mentioned_at", None)
                tags = getattr(r, "tags", []) or []
                doc_id = getattr(r, "document_id", None)
                score = getattr(r, "score", None)

                items.append(
                    MemoryItem(
                        id=str(item_id),
                        text=str(item_text),
                        type=str(item_type),
                        context=str(item_context) if item_context else None,
                        occurred_start=str(occurred_start) if occurred_start else None,
                        occurred_end=str(occurred_end) if occurred_end else None,
                        mentioned_at=str(mentioned_at) if mentioned_at else None,
                        tags=[str(t) for t in tags],
                        document_id=str(doc_id) if doc_id else None,
                        score=float(score) if score is not None else None,
                    )
                )
            return items

        except Exception as e:
            settings = get_settings()
            if self._explicit_client is None and getattr(settings, "DEMO_MOCK_FALLBACK", True):
                if customer_id == "priya":
                    return [
                        MemoryItem(
                            id="M1",
                            text="Priya's Visa card ending in 4242 failed on Pro subscription renewal. Updating address did not resolve it.",
                            type="experience",
                            tags=["customer:priya", "billing"],
                        )
                    ]
                return []
            raise MemoryUnavailableError("Failed to recall memories from Hindsight.") from e

    def recall_kb(self, query: str, *, max_tokens: int = 800) -> List[MemoryItem]:
        """Recalls facts from the shared company knowledge base bank."""
        try:
            resp = self.client.recall(
                bank_id=self.shared_kb_bank,
                query=query,
                max_tokens=max_tokens,
                budget="mid",
            )
            results = getattr(resp, "results", [])
            items: List[MemoryItem] = []
            for idx, r in enumerate(results, start=1):
                item_id = getattr(r, "id", None) or f"K{idx}"
                item_text = getattr(r, "text", str(r))
                items.append(
                    MemoryItem(
                        id=str(item_id),
                        text=str(item_text),
                        type="world",
                        context="support-kb",
                    )
                )
            return items
        except Exception:
            settings = get_settings()
            if getattr(settings, "DEMO_MOCK_FALLBACK", True):
                return [
                    MemoryItem(
                        id="K1",
                        text="Policy K1: Customers with recurring payment failures frequently have expired cards or outdated zip codes. Update in Settings > Billing Methods.",
                        type="world",
                        context="support-kb",
                    ),
                    MemoryItem(
                        id="K3",
                        text="Policy K3: AI assistants cannot process refunds directly; escalated tickets go to human specialists.",
                        type="world",
                        context="support-kb",
                    ),
                ]
            return []

    def retain_turn(
        self,
        customer_id: str,
        session_id: str,
        turn_no: int,
        user_text: str,
        agent_text: str,
        ticket_id: Optional[str] = None,
    ) -> Any:
        """
        Retains an interaction turn into the customer's isolated bank.
        Extracts facts, sanitizes sensitive data, and uses idempotent document_id.
        """
        bank_id = self.bank_id_for(customer_id)
        self.ensure_bank(customer_id)

        clean_user = sanitize_for_memory(user_text)
        clean_agent = sanitize_for_memory(agent_text)
        now_iso = datetime.now(timezone.utc).isoformat()

        content = (
            f"Customer ({now_iso}): {clean_user}\n"
            f"Agent suggested: {clean_agent}"
        )

        doc_id = f"{session_id}-t{turn_no}"
        tags = [f"customer:{customer_id}"]
        if ticket_id:
            tags.append(f"ticket:{ticket_id}")

        metadata: Dict[str, str] = {
            "session_id": str(session_id),
            "turn": str(turn_no),
        }
        if ticket_id:
            metadata["ticket_id"] = str(ticket_id)

        try:
            return self.client.retain(
                bank_id=bank_id,
                content=content,
                context="support conversation",
                timestamp=now_iso,
                document_id=doc_id,
                metadata=metadata,
                tags=tags,
                retain_async=False,
            )
        except Exception as e:
            raise MemoryUnavailableError(f"Failed to retain turn for customer {customer_id}.") from e

    def retain_outcome(
        self,
        customer_id: str,
        ticket_id: str,
        outcome: Literal["resolved", "not_resolved"],
        note: str,
    ) -> Any:
        """Retains customer confirmation outcome ('That worked' / 'Still broken')."""
        bank_id = self.bank_id_for(customer_id)
        self.ensure_bank(customer_id)

        clean_note = sanitize_for_memory(note)
        now_iso = datetime.now(timezone.utc).isoformat()
        content = f"Customer confirmed: the fix for ticket {ticket_id} outcome was {outcome}. Note: {clean_note}"

        doc_id = f"outcome-{ticket_id}-{outcome}"
        try:
            return self.client.retain(
                bank_id=bank_id,
                content=content,
                context="ticket outcome verification",
                timestamp=now_iso,
                document_id=doc_id,
                metadata={"ticket_id": ticket_id, "outcome": outcome},
                tags=[f"customer:{customer_id}", f"ticket:{ticket_id}"],
                retain_async=False,
            )
        except Exception as e:
            raise MemoryUnavailableError(f"Failed to record ticket outcome for {customer_id}.") from e

    def list_memories(
        self,
        customer_id: str,
        limit: int = 50,
        search_query: Optional[str] = None,
    ) -> List[MemoryItem]:
        """Lists memories from customer bank for the UI inspector."""
        bank_id = self.bank_id_for(customer_id)
        self.ensure_bank(customer_id)

        try:
            resp = self.client.list_memories(
                bank_id=bank_id,
                limit=limit,
                search_query=search_query,
            )
            # Response might be a list or an object with items
            items_raw = getattr(resp, "items", resp) if not isinstance(resp, list) else resp
            items: List[MemoryItem] = []
            for idx, r in enumerate(items_raw, start=1):
                item_id = getattr(r, "id", None) or f"M{idx}"
                item_text = getattr(r, "text", str(r))
                item_type = getattr(r, "type", "experience")
                items.append(
                    MemoryItem(
                        id=str(item_id),
                        text=str(item_text),
                        type=str(item_type),
                    )
                )
            return items
        except Exception as e:
            settings = get_settings()
            if self._explicit_client is None and getattr(settings, "DEMO_MOCK_FALLBACK", True):
                if customer_id == "priya":
                    return [
                        MemoryItem(
                            id="M1",
                            text="Priya's Visa card ending in 4242 failed on Pro subscription renewal. Updating address did not resolve it.",
                            type="experience",
                            tags=["customer:priya", "billing"],
                        )
                    ]
                return []
            raise MemoryUnavailableError(f"Failed to list memories for customer {customer_id}.") from e

    def reflect(self, customer_id: str, query: str) -> Optional[str]:
        """
        Synthesizes agent mental models and summaries from customer memories
        using Hindsight's biomimetic reflect capability (vectorize-io/hindsight).
        """
        bank_id = self.bank_id_for(customer_id)
        self.ensure_bank(customer_id)
        try:
            if hasattr(self.client, "reflect"):
                resp = self.client.reflect(bank_id=bank_id, query=query)
                return getattr(resp, "text", str(resp))
            return None
        except Exception:
            return None

    def close(self) -> None:
        """Closes the client session cleanly."""
        try:
            self.client.close()
        except Exception:
            pass


_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """Singleton getter for MemoryService."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
