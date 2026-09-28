"""
scripts/seed_demo.py
Demo data seeding script for PayNest Support Assistant.
Populates:
1. Shared Hindsight Knowledge Base bank ('support-kb') with 5 verified support policies.
2. Isolated customer memory bank ('cs-priya') with Priya's past card failure history.
3. SQLite local store (sessions, messages, tickets, outcomes) for Priya, Arjun, and Meera.

Usage:
  python scripts/seed_demo.py              # Seeds Hindsight Cloud and SQLite
  python scripts/seed_demo.py --local-only # Seeds SQLite only (preserves Hindsight credits)
"""

import argparse
from datetime import datetime, timedelta, timezone
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Reconfigure stdout for UTF-8 in Windows environments
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.config import get_settings
from backend.app.db.store import DatabaseStore, get_store
from backend.app.services.memory import MemoryService, get_memory_service

# 5 Verified PayNest Support Knowledge Base Articles
KB_ARTICLES = [
    {
        "id": "kb-k1-card-update",
        "title": "K1: Subscription Payment Failures & Card Updates",
        "content": (
            "Policy K1: Customers experiencing recurring payment failures on subscription renewal "
            "frequently have an expired card or outdated billing zip code on file. Instruct customer to navigate to "
            "Settings > Billing Methods to update their card details before retrying checkout."
        ),
        "tags": ["kb", "billing", "cards"],
    },
    {
        "id": "kb-k2-sms-2fa",
        "title": "K2: Two-Factor Authentication (2FA) SMS Delays",
        "content": (
            "Policy K2: One-time passwords (2FA) via SMS can take up to 2 minutes during peak carrier hours. "
            "Customers should not request repeated codes within 120 seconds to prevent a temporary 15-minute account lockout."
        ),
        "tags": ["kb", "auth", "2fa"],
    },
    {
        "id": "kb-k3-refund-policy",
        "title": "K3: Refund Review and Limitations",
        "content": (
            "Policy K3: AI assistants and frontline support agents cannot issue refunds or reverse credit card charges directly. "
            "All refund requests require review by our human billing specialist team. Approved refunds settle within 3-5 business days."
        ),
        "tags": ["kb", "refunds", "policy"],
    },
    {
        "id": "kb-k4-plan-changes",
        "title": "K4: Subscription Plan Changes & Proration",
        "content": (
            "Policy K4: When changing or upgrading subscription tiers, changes apply immediately and the unused balance "
            "from the current billing cycle is automatically credited to the next invoice."
        ),
        "tags": ["kb", "subscriptions", "proration"],
    },
    {
        "id": "kb-k5-duplicate-charges",
        "title": "K5: Duplicate Pending Charges",
        "content": (
            "Policy K5: Duplicate charges shown as pending on a banking statement are typically unconfirmed authorization holds "
            "that the bank drops within 48-72 hours. If both charges post as settled, escalate to Tier 2 support with invoice IDs."
        ),
        "tags": ["kb", "billing", "duplicate-charges"],
    },
]


def seed_sqlite(store: DatabaseStore) -> None:
    """Seeds SQLite with historical sessions, messages, tickets, and outcomes for demo personas."""
    print("🌱 Seeding SQLite database records...")
    now = datetime.now(timezone.utc)
    three_days_ago = (now - timedelta(days=3)).isoformat()
    two_days_ago = (now - timedelta(days=2)).isoformat()
    one_day_ago = (now - timedelta(days=1)).isoformat()

    # --- Persona 1: Priya Sharma (The Returning Customer with Recurring Card Issue) ---
    p_session_id = "sess_priya_01"
    store.create_session(
        customer_id="priya",
        session_id=p_session_id,
        title="Pro Renewal Payment Failure (Visa 4242)",
    )
    store.save_message(
        session_id=p_session_id,
        customer_id="priya",
        role="user",
        content="Hi, my payment for the PayNest Pro renewal keeps failing. I'm using my Visa ending in 4242.",
        client_message_id="priya_msg_01",
        memory_saved_status="retained",
    )
    store.save_message(
        session_id=p_session_id,
        customer_id="priya",
        role="assistant",
        content=(
            "Hello Priya! I see you are encountering an error renewing your PayNest Pro plan with Visa card ending in 4242 [M1]. "
            "Renewal failures often occur when billing addresses or card expirations are outdated [K1]. "
            "Please go to Settings > Billing Methods to update your card details and try again."
        ),
        client_message_id="priya_msg_02",
        memory_saved_status="retained",
    )
    p_ticket = store.create_ticket(
        customer_id="priya",
        session_id=p_session_id,
        topic="Pro Renewal Payment Failure (Visa 4242)",
        status="investigating",
        ticket_id="tkt_priya_4242",
    )
    store.record_outcome(
        ticket_id=p_ticket["id"],
        outcome="not_resolved",
        note="Customer tried updating billing address but transaction still failed at gateway.",
    )
    print("  ✓ Priya Sharma: Session sess_priya_01, ticket tkt_priya_4242, and 'not_resolved' outcome seeded.")

    # --- Persona 2: Arjun Patel (Corporate Billing & Tax Invoices) ---
    a_session_id = "sess_arjun_01"
    store.create_session(
        customer_id="arjun",
        session_id=a_session_id,
        title="Annual GST Tax Invoice Request",
    )
    store.save_message(
        session_id=a_session_id,
        customer_id="arjun",
        role="user",
        content="Could you send the consolidated GST tax invoice for our enterprise team for FY 2025-26?",
        client_message_id="arjun_msg_01",
        memory_saved_status="retained",
    )
    store.save_message(
        session_id=a_session_id,
        customer_id="arjun",
        role="assistant",
        content="Hello Arjun! You can download all consolidated tax invoices directly under Billing > Invoices > Tax Statements.",
        client_message_id="arjun_msg_02",
        memory_saved_status="retained",
    )
    a_ticket = store.create_ticket(
        customer_id="arjun",
        session_id=a_session_id,
        topic="Annual GST Tax Invoice Request",
        status="resolved",
        ticket_id="tkt_arjun_gst",
    )
    store.record_outcome(
        ticket_id=a_ticket["id"],
        outcome="resolved",
        note="Customer downloaded invoices successfully from Billing portal.",
    )
    print("  ✓ Arjun Patel: Session sess_arjun_01, ticket tkt_arjun_gst, and 'resolved' outcome seeded.")

    # --- Persona 3: Meera Rao (Clean Slate New User) ---
    m_session_id = "sess_meera_01"
    store.create_session(
        customer_id="meera",
        session_id=m_session_id,
        title="Team Workspace Seat Pricing",
    )
    store.save_message(
        session_id=m_session_id,
        customer_id="meera",
        role="user",
        content="Hi, what is the cost of adding 5 additional seats to our workspace?",
        client_message_id="meera_msg_01",
        memory_saved_status="retained",
    )
    store.save_message(
        session_id=m_session_id,
        customer_id="meera",
        role="assistant",
        content="Hello Meera! Additional workspace seats are $12 per user/month, prorated immediately against your current billing cycle [K4].",
        client_message_id="meera_msg_02",
        memory_saved_status="retained",
    )
    m_ticket = store.create_ticket(
        customer_id="meera",
        session_id=m_session_id,
        topic="Team Workspace Seat Pricing",
        status="open",
        ticket_id="tkt_meera_seats",
    )
    print("  ✓ Meera Rao: Session sess_meera_01 and ticket tkt_meera_seats seeded.")


def seed_hindsight(memory: MemoryService) -> None:
    """Seeds Hindsight Cloud knowledge base bank and Priya's historical memory bank."""
    print("🧠 Seeding Hindsight Cloud memory banks...")

    # 1. Seed Shared Knowledge Base ('support-kb')
    print("  → Populating 'support-kb' bank...")
    try:
        memory.client.create_bank(
            bank_id=memory.shared_kb_bank,
            name="PayNest Support Knowledge Base",
            mission="Store verified support guidelines, refund policies, and troubleshooting instructions for PayNest assistants.",
        )
    except Exception:
        # Bank may already exist
        pass

    now_iso = datetime.now(timezone.utc).isoformat()
    for article in KB_ARTICLES:
        try:
            memory.client.retain(
                bank_id=memory.shared_kb_bank,
                content=article["content"],
                context="PayNest Official Support Guidelines",
                timestamp=now_iso,
                document_id=article["id"],
                metadata={"title": article["title"]},
                tags=article["tags"],
                retain_async=False,
            )
            print(f"    ✓ Stored {article['id']}: {article['title']}")
        except Exception as e:
            print(f"    ⚠ Could not retain {article['id']}: {e}")

    # 2. Seed Priya's Historical Memory in 'cs-priya'
    print("  → Populating 'cs-priya' bank...")
    priya_bank = memory.bank_id_for("priya")
    memory.ensure_bank("priya")

    priya_history_turn = (
        "Customer (Priya Sharma): My payment for the PayNest Pro renewal keeps failing. "
        "I am using my Visa card ending in 4242.\n"
        "Agent suggested: Update card details in Settings > Billing Methods or verify the billing zip code.\n"
        "Customer update: Tried updating billing details on Visa ending 4242, but payment still fails with gateway decline."
    )

    try:
        memory.client.retain(
            bank_id=priya_bank,
            content=priya_history_turn,
            context="Past support session regarding subscription renewal failure",
            timestamp=(datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
            document_id="sess_priya_01-t1",
            metadata={"session_id": "sess_priya_01", "turn": "1", "ticket_id": "tkt_priya_4242"},
            tags=["customer:priya", "ticket:tkt_priya_4242", "billing"],
            retain_async=False,
        )
        print("    ✓ Stored Priya's past card failure history in cs-priya (document_id: sess_priya_01-t1)")
    except Exception as e:
        print(f"    ⚠ Could not retain Priya history: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed PayNest demo scenarios and knowledge base.")
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Seed SQLite database only without calling Hindsight Cloud (preserves credits).",
    )
    args = parser.parse_args()

    store = get_store()
    seed_sqlite(store)

    if args.local_only:
        print("ℹ --local-only specified. Skipped Hindsight Cloud memory seeding.")
    else:
        settings = get_settings()
        if not settings.HINDSIGHT_API_KEY:
            print("⚠ HINDSIGHT_API_KEY is not configured. Skipped Hindsight Cloud seeding.")
        else:
            memory = get_memory_service()
            seed_hindsight(memory)

    print("\n✅ PayNest demo data seeding completed successfully.")


if __name__ == "__main__":
    main()
