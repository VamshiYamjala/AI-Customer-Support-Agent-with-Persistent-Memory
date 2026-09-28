"""
backend/app/db/store.py
SQLite database storage for customers, sessions, messages, tickets, and outcomes.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
import uuid
from typing import Any, Dict, List, Optional
from backend.app.config import get_settings


def get_db_path() -> str:
    """Extracts local filesystem path from DATABASE_URL."""
    settings = get_settings()
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "")
    else:
        path = "data/app.db"

    # Ensure parent directory exists
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


def get_db_connection() -> sqlite3.Connection:
    """Returns a sqlite3 connection with Row factory enabled."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initializes tables and seeds initial demo customers idempotently."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            email_masked TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            title TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            client_message_id TEXT,
            memory_saved_status TEXT DEFAULT 'pending',
            FOREIGN KEY (session_id) REFERENCES sessions (id),
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            UNIQUE (session_id, client_message_id)
        );

        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            status TEXT NOT NULL,
            opened_at TEXT NOT NULL,
            closed_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        );

        CREATE TABLE IF NOT EXISTS outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            outcome TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id)
        );
    """)

    # Seed demo customers
    now = datetime.now(timezone.utc).isoformat()
    demo_customers = [
        ("priya", "Priya Sharma", "p****@example.com", now),
        ("arjun", "Arjun Patel", "a****@example.com", now),
        ("meera", "Meera Rao", "m****@example.com", now),
    ]

    for cid, name, email, dt in demo_customers:
        cursor.execute(
            """
            INSERT OR IGNORE INTO customers (id, display_name, email_masked, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (cid, name, email, dt),
        )

    conn.commit()
    conn.close()


class DatabaseStore:
    """Data access helper for SQLite."""

    def __init__(self):
        init_db()

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id.lower().strip(),))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_customers(self) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers ORDER BY id ASC")
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def create_session(self, customer_id: str, session_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db_connection()
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """
            INSERT OR REPLACE INTO sessions (id, customer_id, created_at, title)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, customer_id, now, title or f"Session {session_id[:8]}"),
        )
        conn.commit()
        conn.close()
        return {"id": session_id, "customer_id": customer_id, "created_at": now, "title": title}

    def get_session(self, session_id: str, customer_id: str) -> Optional[Dict[str, Any]]:
        """Ensures session belongs to customer; returns None otherwise."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM sessions WHERE id = ? AND customer_id = ?",
            (session_id, customer_id),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_sessions(self, customer_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM sessions WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,),
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_message(
        self,
        session_id: str,
        customer_id: str,
        role: str,
        content: str,
        client_message_id: Optional[str] = None,
        memory_saved_status: str = "saved",
    ) -> None:
        conn = get_db_connection()
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """
            INSERT OR IGNORE INTO messages (session_id, customer_id, role, content, created_at, client_message_id, memory_saved_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, customer_id, role, content, now, client_message_id, memory_saved_status),
        )
        conn.commit()
        conn.close()

    def get_session_messages(self, session_id: str, customer_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM messages 
            WHERE session_id = ? AND customer_id = ? 
            ORDER BY id ASC
            """,
            (session_id, customer_id),
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def create_ticket(
        self, customer_id: str, session_id: str, topic: str, status: str = "open", ticket_id: Optional[str] = None
    ) -> Dict[str, Any]:
        conn = get_db_connection()
        cur = conn.cursor()
        tkt_id = ticket_id or f"tkt_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """
            INSERT OR REPLACE INTO tickets (id, customer_id, session_id, topic, status, opened_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (tkt_id, customer_id, session_id, topic, status, now),
        )
        conn.commit()
        conn.close()
        return {
            "id": tkt_id,
            "customer_id": customer_id,
            "session_id": session_id,
            "topic": topic,
            "status": status,
            "opened_at": now,
        }

    def get_ticket(self, ticket_id: str, customer_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM tickets WHERE id = ? AND customer_id = ?",
            (ticket_id, customer_id),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_latest_ticket_for_session(self, session_id: str, customer_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM tickets WHERE session_id = ? AND customer_id = ? ORDER BY opened_at DESC LIMIT 1",
            (session_id, customer_id),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def record_outcome(
        self, ticket_id: str, outcome: str, note: Optional[str] = None
    ) -> Dict[str, Any]:
        conn = get_db_connection()
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """
            INSERT INTO outcomes (ticket_id, outcome, note, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (ticket_id, outcome, note or "", now),
        )
        new_status = "resolved" if outcome == "resolved" else "investigating"
        closed_at = now if outcome == "resolved" else None
        cur.execute(
            """
            UPDATE tickets SET status = ?, closed_at = ? WHERE id = ?
            """,
            (new_status, closed_at, ticket_id),
        )
        conn.commit()
        conn.close()
        return {"ticket_id": ticket_id, "outcome": outcome, "note": note, "created_at": now}

    def get_outcomes_for_ticket(self, ticket_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM outcomes WHERE ticket_id = ? ORDER BY id ASC", (ticket_id,))
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_customer_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """Returns customer's sessions with their messages, tickets, and outcomes."""
        sessions = self.list_sessions(customer_id)
        result = []
        for s in sessions:
            sid = s["id"]
            msgs = self.get_session_messages(sid, customer_id)
            ticket = self.get_latest_ticket_for_session(sid, customer_id)
            outcomes = self.get_outcomes_for_ticket(ticket["id"]) if ticket else []
            result.append({
                "session": s,
                "messages": msgs,
                "ticket": ticket,
                "outcomes": outcomes,
            })
        return result


_store_instance: Optional[DatabaseStore] = None


def get_store() -> DatabaseStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = DatabaseStore()
    return _store_instance
