# PayNest: AI Customer Support Agent with Persistent Memory
## Complete Project Steps & Build History

### Overview
This document tracks every single action, decision, setup step, and milestone completed across all levels of the project build.

---

### Step 0: Initial Inspection & Git Connection
- **Repository Setup**: Initialized empty Git repository in local project directory `D:\Hackathon\AI Customer Support Agent with Persistent Memory`.
- **Remote Origin**: Configured remote origin: `https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory.git` with primary branch `main`.
- **Environment & Tools Verification**:
  - Operating System: Windows (PowerShell)
  - Python Version: `3.12.3` (satisfies `>= 3.11` requirement)
  - Pip Version: `26.1.1`
  - Git Version: `2.55.0.windows.5`
- **Documentation Setup**: Created `docs/PROJECT_STEPS.md` and `docs/ERRORS_HANDLED.md` for continuous traceability.

---

### Level 1: Service Connections and Environment Setup (Completed)
- [x] Initial inspection completed (app repo confirmed, not Hindsight fork).
- [x] Git remote connected.
- [x] Virtual environment created (`.venv`) and dependencies installed (`requirements.txt`).
- [x] Created `.env.example`, `.env`, and `.gitignore` with strict leak checks (`.env` verified git-ignored).
- [x] Generated secure session secret via `secrets.token_urlsafe(48)`.
- [x] Created verification script `scripts/verify_connections.py`.
- [x] User pasted Hindsight Cloud & Groq API keys into `.env`.
- [x] Executed `scripts/verify_connections.py` — ALL CHECKS PASSED with exit code 0!
- [x] Recorded SDK introspection & method findings in `docs/verified-sdk-notes.md`.
- [x] Verified Hindsight retain, recall, and bank operations on Hindsight Cloud.
- [x] Verified cross-customer isolation (zero memory leakage across customer banks).
- [x] Verified Groq LLM model (`openai/gpt-oss-20b`) connection and response.
- [x] Committed Level 1 changes: `chore: complete level 1 service connections, sdk verification, and environment setup`.

---

### Level 2: Scaffolding, Configuration, Health Checks, and Local Run (Completed)
- [x] Scaffolded folder architecture: `backend/app/api`, `backend/app/services`, `backend/app/models`, `backend/app/db`, `backend/app/prompts`, `backend/app/core`, `frontend/`, `tests/unit`, `tests/integration`.
- [x] Implemented `backend/app/config.py` using `pydantic-settings`:
  - Enforces required secrets (`HINDSIGHT_API_KEY`, `GROQ_API_KEY`, `SESSION_SECRET`).
  - Implements custom `__repr__` and `__str__` masking all API keys and session secrets.
  - Automatically strips trailing slashes from URLs and parses allowed origins.
- [x] Implemented `backend/app/api/health.py`:
  - `GET /api/health` -> shallow 200 liveness probe returning environment status.
  - `GET /api/health/deep` -> deep readiness probe verifying live reachability of Hindsight Cloud and Groq LLM without leaking credentials or stack traces.
- [x] Implemented `backend/app/main.py`:
  - FastAPI application configuration.
  - CORS middleware enabled using configured allowed origins.
  - Mounted API routers and static frontend directory at `/`.
- [x] Created UI shell in `frontend/index.html` and `frontend/styles.css` with responsive layout, chat pane, and persistent memory inspector.
- [x] Created `pytest.ini` with unit and integration markers.
- [x] Created comprehensive test suites:
  - Unit tests in `tests/unit/test_health.py`: secret masking test, missing configuration validation test, shallow health check test, static index serving test.
  - Integration tests in `tests/integration/test_health_deep.py`: live deep health check verifying Hindsight and Groq connectivity.
- [x] Ran test suite: **5/5 tests passed in 3.61s**.
- [x] Verified local server execution via Uvicorn over HTTP (`http://127.0.0.1:8000`), testing `/api/health`, `/docs`, and `/`.

---

### Level 3: Backend LLM Integration (Chat Without Memory) (Completed)
- [x] Implemented `backend/app/core/errors.py`:
  - `LLMUnavailableError` and `LLMAuthenticationError` mapping to HTTP 503.
  - Global `AppException` handler returning standard JSON `{"error": {"code": "...", "message": "..."}}`.
  - Zero leakage of raw stack traces, API keys, or provider bodies.
- [x] Implemented `backend/app/prompts/system.py`:
  - PayNest support assistant rules and honesty guardrails.
  - Strict rule preventing agent from falsely claiming account actions or resolutions.
- [x] Implemented `backend/app/models/schemas.py`:
  - `ChatRequest`: message length 1-2000 chars, whitespace stripping, rejection of empty messages.
  - `ChatResponse`: structured response containing reply, session_id, memories_used, memory_status ("off"), and optional banner.
- [x] Implemented `backend/app/services/llm.py`:
  - `LLMClient.complete` wrapping Groq `openai/gpt-oss-20b`.
  - Configured 30s timeout, automatic retry on 429 rate limit or 5xx with exponential backoff (1s, 3s).
  - Explicit refusal to retry on 401/403 authentication failures.
- [x] Implemented `backend/app/api/chat.py`:
  - `POST /api/chat` handling customer turns and returning LLM responses.
- [x] Updated `backend/app/main.py`:
  - Registered `chat_router` and global `app_exception_handler`.
- [x] Connected Frontend in `frontend/app.js` and `frontend/styles.css`:
  - Interactive chat with typing indicator, dynamic message bubbles, and error toasts.
  - Memory toggle reflecting active/off status.
- [x] Test Suite:
  - Unit tests in `tests/unit/test_chat.py` (8 tests): valid chat, empty input (422), whitespace input (422), oversized input (422), 429 retry success, 401 no-retry 503, timeout 503, system prompt rules.
  - Integration test in `tests/integration/test_chat_live.py`: live Groq response verified.
  - Full test suite: **14/14 tests passing in 5.56s**.
- [x] Verified live HTTP chat via Uvicorn on `http://127.0.0.1:8000/api/chat`.
- [x] Committed Level 3 changes: `feat: implement level 3 backend llm chat integration, schemas, and frontend controller` and pushed to GitHub `main`.

---

### Level 4: Hindsight Integration and Memory Lifecycle (Completed)
- [x] Implemented `backend/app/services/sanitize.py`:
  - Regex-based PII redaction masking 13–19 digit credit cards to `****-****-****-XXXX`.
  - Redaction of CVVs, one-time passwords (OTPs), and plain-text passwords before storing in memory.
- [x] Implemented `backend/app/services/memory.py`:
  - Sole module in the backend importing `hindsight_client`.
  - `MemoryService.bank_id_for(customer_id)`: validates customer ID and prefixes with `cs-`.
  - `MemoryService.ensure_bank(customer_id)`: creates dedicated bank with verified mission and disposition if not already present.
  - `MemoryService.retain_turn(...)`: formats transcript, redacts PII, tags customer, and uses idempotent `document_id=f"{session_id}-t{turn_no}"`.
  - `MemoryService.retain_outcome(...)`: records customer outcome ("That worked" / "Still broken") on support recommendations.
  - `MemoryService.recall(...)`: queries customer bank with `tags_match="all_strict"` ensuring defense-in-depth isolation.
  - `MemoryService.recall_kb(...)`: queries shared company knowledge bank `support-kb`.
  - `MemoryService.list_memories(...)`: retrieves memory items for the inspector panel.
  - Exception wrapping: safely maps client errors to `MemoryUnavailableError`.
- [x] Updated `backend/app/prompts/system.py`:
  - Renders recalled memories into `<memories>` block with citations `[M1]`, `[M2]` or fallback `CUSTOMER HISTORY: No relevant history found.`.
  - Renders shared knowledge into `<kb>` block with citations `[K1]`.
- [x] Integrated `MemoryService` into `backend/app/api/chat.py`:
  - When `use_memory=True`: queries customer and KB memories, injects into prompt, schedules background turn retention via `BackgroundTasks`.
  - When `use_memory=False`: bypasses recall, runs in standard direct LLM mode.
  - Graceful outage fallback: if Hindsight is unreachable, returns warning banner `"Memory temporarily unavailable — answering without history."` while still providing conversational assistance.
- [x] Updated Frontend (`frontend/app.js` & `frontend/styles.css`):
  - Inspector renders memory cards with type badges (`[world]`, `[experience]`, `[observation]`), memory tags `[M1]`, and text.
  - Real-time status chip reflects `"Memory: Saved ✓"`, `"Memory: OFF"`, or `"Memory: Unavailable"`.
- [x] Test Suite:
  - Unit tests in `tests/unit/test_memory.py` (6 tests): bank ID validation, idempotent creation, PII redaction before retain, recall mapping & tag scoping, outage handling, customer isolation.
  - Unit tests in `tests/unit/test_chat_memory.py` (3 tests): memory ON recall & injection, memory OFF bypass, memory outage graceful fallback banner.
  - Full test suite: **23/23 tests passing in 6.79s**.
- [x] Verified local HTTP server execution with active memory recall and background retention.
