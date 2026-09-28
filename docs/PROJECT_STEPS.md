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
- [x] Committed Level 4 changes: `feat: implement level 4 hindsight memory service, lifecycle, and customer isolation` and pushed to GitHub `main`.

---

### Level 5: Customer Identity and Strict Isolation (Completed)
- [x] Implemented `backend/app/db/store.py`:
  - SQLite database tables: `customers`, `sessions`, `messages`, `tickets`, `outcomes`.
  - Idempotent seeding on startup for 3 demo customers: `priya` (Priya Sharma), `arjun` (Arjun Patel), and `meera` (Meera Rao).
  - Session and message access methods with strict `WHERE customer_id = ?` query isolation.
- [x] Implemented `backend/app/services/identity.py`:
  - Signed URL-safe timed tokens via `itsdangerous.URLSafeTimedSerializer(SESSION_SECRET)`.
  - 12-hour expiration window; rejects expired or tampered signatures with HTTP 401.
  - `get_current_customer` FastAPI dependency: decodes token from `Authorization: Bearer <token>` and verifies existence against SQLite.
- [x] Implemented authentication endpoints in `backend/app/api/auth.py`:
  - `POST /api/login` -> issues signed bearer token for demo customers.
  - `GET /api/me` -> returns authenticated customer profile.
  - `GET /api/customers` -> provides customer list for frontend selector.
- [x] Implemented session management in `backend/app/api/sessions.py`:
  - `POST /api/sessions` -> creates customer-owned session.
  - `GET /api/sessions` -> returns only the authenticated customer's sessions.
  - `GET /api/sessions/{session_id}/messages` -> returns message history; raises HTTP 404 if accessed by any other customer.
- [x] Updated `backend/app/api/chat.py`:
  - Enforced `customer_id` derived exclusively from verified bearer token (any client-supplied `customer_id` or `bank_id` in request body is rejected/ignored).
  - Persists chat turns and assistant replies directly to SQLite messages table for audit.
- [x] Updated Frontend (`frontend/index.html`, `frontend/app.js`, `frontend/styles.css`):
  - Added customer selector in header allowing seamless switching between Priya, Arjun, and Meera.
  - Automatic demo login and storage of bearer token in `sessionStorage`.
  - Passes `Authorization: Bearer <token>` on all API requests.
- [x] Comprehensive test suites:
  - `tests/unit/test_identity.py` (4 tests): token creation/verification, signature tampering (401), token expiry (401), missing/malformed auth header (401).
  - `tests/unit/test_isolation.py` (3 tests): SQLite cross-customer access rejected with 404, request body identity spoofing ignored, MemoryService bank and tag isolation.
  - Full test suite: **30/30 tests passing in 5.46s**.
- [x] Verified live HTTP execution: customer switching, token generation, session creation, chat, and cross-customer isolation enforcement.

---

### Level 6: Core Support Agent, Honesty Guardrails, Demo Seeding, and Outcomes (Completed)
- [x] Implemented `backend/app/services/agent.py`:
  - `AgentService.process_turn(...)`: Full orchestration pipeline integrating FastAPI bearer customer identity, SQLite session/ticket persistence, context-aware semantic query generation, Hindsight customer and KB recall, Groq LLM completion, post-check honesty guardrails, and asynchronous background retention.
  - `build_recall_query(...)`: Combines current message with recent conversation context, respecting a strict 35-word limit for optimal Hindsight search precision.
  - `post_check_honesty(...)`:
    - Regex detection of unauthorized action claims (e.g., "I have refunded", "I fixed your account", "I cancelled your subscription") and drops safe honest boundaries directing customer to human billing teams.
    - Citation validation: Strips hallucinated citation tags (e.g. `[M99]`, `[K5]`) while preserving verified recalled references (`[M1]`, `[K1]`).
- [x] Implemented Ticket & Outcome Storage (`backend/app/db/store.py`):
  - Added methods `create_ticket`, `get_ticket`, `get_latest_ticket_for_session`, `record_outcome`, `get_outcomes_for_ticket`, and `get_customer_history`.
  - Fully idempotent operations using `INSERT OR REPLACE INTO sessions` and `INSERT OR IGNORE INTO messages`.
- [x] Extended API Endpoints (`backend/app/api/chat.py` & `backend/app/models/schemas.py`):
  - Refactored `POST /api/chat` to delegate orchestration directly to `AgentService`.
  - Added `POST /api/outcome`: Accepts `{session_id, ticket_id, outcome, note}` with validation (`resolved` | `not_resolved`), persists outcome to SQLite, and retains confirmation to Hindsight memory.
  - Added `GET /api/customer/history`: Returns full longitudinal sessions, tickets, messages, and outcomes scoped strictly to authenticated customer.
- [x] Demo Seeding Script (`scripts/seed_demo.py`):
  - Populates shared `support-kb` Hindsight bank with 5 verified PayNest support policies (`kb-k1-card-update`, `kb-k2-sms-2fa`, `kb-k3-refund-policy`, `kb-k4-plan-changes`, `kb-k5-duplicate-charges`).
  - Populates Priya's isolated Hindsight memory bank `cs-priya` with her historical Visa 4242 failure (`sess_priya_01-t1`).
  - Populates SQLite store with realistic demo sessions, tickets, and outcomes for Priya Sharma, Arjun Patel, and Meera Rao.
  - Supports `--local-only` mode for offline / zero-credit testing as well as full Hindsight Cloud live seeding.
- [x] Frontend Interaction Updates (`frontend/app.js` & `frontend/styles.css`):
  - Added resolution outcome feedback buttons ("✓ That worked" / "✕ Still broken") under assistant responses that trigger `POST /api/outcome` and render real-time memory-logged confirmation badges.
  - Inspector panel distinguishes between `[K#]` KB / Company Policy badges (`badge-world`) and `[M#]` Customer Experience badges (`badge-exp`).
  - Inspector "All Memories" tab loads full persistent session history, topics, and recorded outcomes via `GET /api/customer/history`.
- [x] Comprehensive Test Suite:
  - Added `tests/unit/test_agent.py` (9 tests) covering query builder with context, honesty claim replacement, citation validation, outcome recording (`resolved` / `not_resolved` / invalid 422), and customer history endpoint.
  - Full test suite: **39/39 tests passing in 15.78s**.

---

### Level 7: Persistent-Learning Demonstration & Comparison (Completed)
- [x] End-to-End Demo Walkthrough Script (`scripts/demo_scenario.py`):
  - Demonstrates Priya's Session 2 recurring card issue under Memory OFF (stateless discovery) vs. Memory ON (proactive recall of Visa 4242 and previous fix attempt).
  - Demonstrates resolution outcome recording (`resolved` feedback saved to SQLite & Hindsight).
  - Proves cross-customer isolation: Customer Arjun Patel queries about card errors and receives 0 recalled memories of Priya's Visa 4242.
  - Supports `--mock` mode for fast, deterministic, zero-credit evaluation by judges.
- [x] Quantitative & Qualitative Benchmark Suite (`scripts/eval_memory.py`):
  - Standardized evaluation of 4 scenarios:
    1. Returning customer recurring payment failure (`TC-01`).
    2. Cross-session communication channel preference (`TC-02`).
    3. Irrelevant / negative match query (`TC-03`).
    4. System resilience under Hindsight outage fallback (`TC-04`).
  - Measures re-explanation rates (100% reduction for returning customers), context recall precision, honesty adherence, and fallback resilience.
  - Generates comprehensive markdown report: `docs/EVALUATION_REPORT.md`.
- [x] Frontend Demonstration Enhancements (`frontend/index.html`, `frontend/app.js`, `frontend/styles.css`):
  - Added Judge Demo Bar with quick action chips:
    - `[⚡ Priya Session 2]`: Tests instant memory recall of past failure.
    - `[⚖️ Compare ON vs OFF]`: Injects side-by-side comparison card displaying Memory OFF vs Memory ON responses, memory counts, re-explanation status, and judge insight.
    - `[🔒 Arjun Isolation]`: Instant isolation proof without manual dropdown clicks.
- [x] Comprehensive Test Suite (`tests/unit/test_comparison.py`):
  - 4 unit tests verifying prompt divergence between Memory ON and OFF, cross-session memory retrieval in fresh sessions, cross-customer isolation with zero leakage, and empty memory handling on irrelevant queries.
  - Full test suite: **43/43 tests passing in 8.47s**.
- [x] Documentation Deliverables:
  - Updated `README.md` with demonstration and benchmark execution instructions.
  - Updated `docs/PROGRESS.md` and `docs/PROJECT_STEPS.md`.

---

### Level 8: Frontend UI and Memory Inspector UX (Completed)
- [x] Modern Design System & Accessible Layout (`frontend/styles.css`):
  - Adopted a clean customer support dashboard theme with Plus Jakarta Sans typography, high-contrast accessible color palette, elevation tokens, and crisp card borders.
  - Fully responsive design: Seamless desktop 2-column layout (`1fr 420px`) and responsive mobile sliding drawer with mobile inspector toggle badge.
- [x] Elevated Chat Experience (`frontend/index.html` & `frontend/app.js`):
  - Customer vs. AI visual hierarchy: User messages render as rich indigo gradient pills; AI messages render as clean white cards with `🤖 PayNest AI` badges.
  - Inline citation formatting: Automatically highlights memory references as colored pills (`[M1]` in purple, `[K1]` in gold).
  - Character counter (`0 / 2000`) and auto-resizing input textarea.
  - Three-dot pulsing typing indicator replacing static text.
- [x] 3-Tab Memory Inspector Panel:
  - **Tab 1 (Turn Memories):** Displays memories recalled for the active turn with tag badges (`[M#]` vs `[K#]`), type badges (`Experience`, `Observation`, `Company Policy`), relevance score, and source bank indicator.
  - **Tab 2 (Customer History):** Fetches longitudinal history from `GET /api/customer/history`, displaying past sessions, tickets, interaction counts, and confirmation badges (`✓ Resolved` / `✕ Still broken`).
  - **Tab 3 (Company KB):** Displays all 5 verified PayNest company policies (`K1` to `K5`) with titles, text, and policy tags.
  - Informative empty and disabled states when memory is toggled OFF or empty.
- [x] Side-by-Side Comparison UI:
  - Clean comparison card rendering Memory OFF (stateless discovery) vs Memory ON (persistent Hindsight recall) side by side on desktop and stacked on mobile.
  - Displays customer friction comparison and judge insights.
- [x] Outcome Feedback Confirmation:
  - Interactive `[✓ That worked]` and `[✕ Still broken]` feedback bar on recommendation turns.
  - Submits to `POST /api/outcome` and smoothly transitions to green/amber confirmation pills without jumping or re-rendering.
- [x] Test Suite & Asset Serving:
  - Added `test_static_assets_served` in `tests/unit/test_health.py` confirming `styles.css` and `app.js` are properly served with 200 OK.
  - Full test suite: **44/44 tests passing**.

---

### Level 9: Comprehensive Testing & Reliability (Completed)
- [x] Comprehensive Reliability & Edge-Case Test Suite (`tests/unit/test_reliability.py`):
  - **17 new unit tests** covering boundary limits (exact 2000 chars, oversized 2001 chars rejected), unicode & emoji safe encoding, malformed JSON bodies, cross-customer ticket tampering (404), cross-customer session isolation (404), token tampering (401), case variations in honesty guardrails, and database idempotency.
- [x] Fault-Tolerance & Resilience Verification:
  - Tested Hindsight Cloud outages: `MemoryUnavailableError` handled gracefully, returning status `unavailable` and user-facing warning banner while continuing conversational assistance.
  - Tested Groq LLM rate-limit backoff: Exponential retry on HTTP 429 and clean 503 error handling on timeouts without secret leakage.
- [x] Security & Defense-in-Depth Audit:
  - Confirmed identity is derived exclusively from server-verified signed bearer tokens.
  - Confirmed separate Hindsight memory banks (`cs-<customer_id>`) with `tags_match="all_strict"` prevent cross-customer data leakage.
  - Confirmed PII masking (PANs to `****-****-****-XXXX`, CVVs and OTPs redacted).
  - Confirmed `.env` and `data/` are strictly excluded from Git.
- [x] Test Suite Execution:
  - Complete test suite: **61/61 tests passing** across 11 test files in 10.25s.
- [x] Comprehensive Reliability Report (`docs/RELIABILITY_REPORT.md`):
  - Documented full test coverage matrix, security isolation table, fault-tolerance mechanisms, known limitations, and reproducible commands.




