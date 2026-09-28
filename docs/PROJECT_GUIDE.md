# AI Customer Support Agent with Persistent Memory — Complete Technical Documentation and Antigravity Implementation Guide

**Event:** HackwithHyderabad 3.0 · **Required technology:** Hindsight by Vectorize · **Submission deadline:** September 29, 2026
**Document written:** September 28, 2026 · **Status of the project:** In Development

---

## 0. START HERE (read this first)
**What this document is.** A build manual that you hand to Google Antigravity together with the master prompt at the very end (Part 8). Antigravity builds the app one level at a time and stops to ask you whenever it needs a human action.
**What you must do first: start at LEVEL 1.** Level 1 creates accounts, gets API keys, connects Hindsight and the LLM, and proves each connection works. **No feature code is written until every Level 1 check passes.**
**Execution Schedule:** The plan is an emergency MVP: a chat UI, Hindsight-backed memory, a memory inspector panel, a "memory ON/OFF" comparison, and cross-customer isolation. Everything else is cut.

### 0.3 Verified Hindsight facts this design depends on
1. **Three operations:** `retain` (store), `recall` (search), `reflect` (reason over memories).
2. **Retain does not store raw text.** An LLM extracts facts, entities and times; those are stored.
3. **Memory banks are isolated stores** ("no cross-bank leakage"). One bank = one "brain" for one user/agent/project.
4. **Tags** scope visibility in recall. Default `tags_match="any"` also returns untagged memories — a leakage trap. Use `any_strict` / `all_strict`.
5. **`document_id`** makes retain idempotent (same id -> old version replaced). Omit it and every call creates duplicates.
6. **Consolidation into "observations" happens in the background** after retain, so observations lag behind raw facts.
7. **Python client:** `from hindsight_client import Hindsight`; `Hindsight(base_url=..., api_key=..., timeout=...)`; `.retain(bank_id, content, context, timestamp, document_id, metadata, retain_async)`; `.recall(bank_id, query, types, max_tokens, budget, ...)` returns an object with `.results`; `.reflect(bank_id, query, budget, context)` returns `.text`; `.create_bank(bank_id, name, mission, disposition)`; `.list_memories(...)`; `.get_version()`; `.close()`.

---

## PART 1 — PROJECT OVERVIEW
### 1.1 The problem
Support chatbots forget. A customer whose payment failed on Monday returns on Thursday and must re-explain everything: which card, which error, what was already tried. Agents repeat failed fixes, ignore known preferences (e.g., "email me, don't call"), and can't see patterns.

### 1.2 Product in one sentence
A web support assistant for a fictional online business, **"PayNest"** (a subscription/payments app), that keeps a **separate Hindsight memory bank per customer** and uses recalled facts to give faster, personalised, honest support in later sessions.

### 1.3 Target users and use cases
- Customer: Describe a problem once; not repeat themselves in later sessions.
- Support agent (judge role-plays): See what the AI remembered and why it answered as it did.
- Business: Fewer repeat contacts, faster resolution.

---

## PART 2 — COMPLETE TECHNOLOGY STACK
- Memory: Hindsight Cloud (`https://api.hindsight.vectorize.io`)
- Memory client: `hindsight-client` Python SDK
- LLM Provider: Groq API
- LLM Model: `openai/gpt-oss-20b` (or active Groq model)
- Backend: Python 3.12 + FastAPI + Uvicorn
- App Database: SQLite (for session tokens, message audit, tickets)
- Frontend: Vanilla HTML5 / CSS3 / JavaScript (no build step, served by FastAPI)
- Testing: pytest + httpx

---

## PART 7 — PROJECT FOLDER STRUCTURE
```
paynest-support-agent/
├── README.md
├── requirements.txt
├── pytest.ini
├── .env.example
├── .env (git-ignored)
├── .gitignore
├── backend/
│   ├── __init__.py
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── api/
│       ├── services/
│       ├── prompts/
│       ├── models/
│       ├── db/
│       └── core/
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── scripts/
│   ├── verify_connections.py
│   ├── seed_demo.py
│   ├── demo_scenario.py
│   └── eval_memory.py
├── tests/
│   ├── unit/
│   └── integration/
├── data/
└── docs/
    ├── PROJECT_GUIDE.md
    ├── PROJECT_STEPS.md
    ├── ERRORS_HANDLED.md
    ├── PROGRESS.md
    └── verified-sdk-notes.md
```
