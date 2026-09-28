# Production QA & Reliability Bug Report: PayNest Support Assistant

**Application:** PayNest Support — AI Customer Support Agent with Persistent Memory  
**Target URL:** `https://paynest-support-agent.onrender.com/`  
**GitHub Repository:** `https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory`  
**Git Branch:** `main`  
**Report Date:** 2026-09-28  
**QA Lead:** Senior QA Engineer, Full-Stack Developer & Production Reliability Engineer  

---

## 1. Executive Summary

A comprehensive end-to-end audit was conducted against both the live production deployment (`https://paynest-support-agent.onrender.com/`) and the local testbed. 

### Key Findings:
- **Baseline Test Suite:** **61/61 automated tests passing** locally across 11 test modules.
- **Live Deployment Availability:** The web service is reachable, serving HTML, CSS, JavaScript, and health check endpoints.
- **Authentication & Security Isolation:** Strict token-based authentication (`/api/login`), customer isolation (cross-customer session access rejected with 404), and tamper detection are verified working on production.
- **LLM Grounding & Guardrails:** Groq LLM replies are successfully generated in production, adhering to honesty guardrails (no unauthorized refund claims or crypto loans).
- **Core Production Issues Identified:**
  1. `RuntimeError: Event loop is closed` / AnyIO worker thread contention in `MemoryService.client`: A singleton Hindsight client shared across asynchronous worker threads causes persistent memory recall to fail on multi-turn web requests, triggering graceful degradation to memory unavailable.
  2. `/api/health/deep` returns HTTP 503 (`hindsight: down`) on live deployment due to thread event-loop closure during SDK client teardown and lack of credential string trimming.
  3. Static asset routing lacks `/static` mount alias (`/static/styles.css` returns 404 while `/styles.css` returns 200).

---

## 2. Test Execution Matrix (25 Live Deployed Scenarios)

| Test ID | Category | Test Scenario | Target Env | Status | Observed Details |
|:---|:---|:---|:---|:---:|:---|
| **A1** | Availability | Frontend loads `index.html` | Deployed | **PASS** | Status 200, contains full PayNest DOM |
| **A2** | Availability | Static CSS loads correctly (`/styles.css`) | Deployed | **PASS** | Status 200, 22,016 bytes |
| **A3** | Availability | Static JS loads correctly (`/app.js`) | Deployed | **PASS** | Status 200, 26,413 bytes |
| **A4** | Availability | Health liveness probe (`/api/health`) | Deployed | **PASS** | Status 200, `{"status":"ok","env":"production"}` |
| **A5** | Availability | Deep health check (`/api/health/deep`) | Deployed | **FAIL** | Status 503, `{"status":"degraded","hindsight":"down","llm":"ok"}` |
| **E1** | Authentication | Demo customers listed (`/api/customers`) | Deployed | **PASS** | Status 200, returns Priya, Arjun, Meera |
| **E2** | Authentication | Valid customer login (`/api/login`) | Deployed | **PASS** | Status 200, returns signed URL-safe bearer token |
| **E3** | Authentication | Unknown customer login | Deployed | **PASS** | Status 404, `"Customer 'unknown_hacker' not found"` |
| **E4** | Authorization | Unauthenticated request rejected | Deployed | **PASS** | Status 401 Unauthorized |
| **E5** | Authorization | Tampered session token rejected | Deployed | **PASS** | Status 401 Unauthorized |
| **E6** | Isolation | Cross-customer session access | Deployed | **PASS** | Status 404, `"Session not found or belongs to another customer."` |
| **G1** | Sessions | Create session (`POST /api/sessions`) | Deployed | **PASS** | Status 201 Created, returns session ID |
| **G2** | History | Customer history (`/api/customer/history`) | Deployed | **PASS** | Status 200 OK, returns 16 historical interaction records |
| **G3** | Outcomes | Outcome recorded (`/api/outcome`) | Deployed | **PASS** | Status 200 OK, `{"status":"recorded"}` |
| **B1** | AI Chat | Basic chat response (Memory OFF) | Deployed | **PASS** | Status 200 OK, answers refund policy accurately via Groq |
| **C1** | Grounding | Policy query grounded in PayNest KB | Deployed | **PASS** | Status 200 OK, correctly details 2FA 2-minute carrier window |
| **C2** | Grounding | Ungrounded inquiry (crypto loan) | Deployed | **PASS** | Status 200 OK, politely declines without policy hallucination |
| **F1** | Honesty | Refund promise guardrail | Deployed | **PASS** | Status 200 OK, does not promise immediate charge reversal |
| **F2** | Sanitization | Credit card number handling | Deployed | **PASS** | Status 200 OK, handled securely without crashes |
| **H1** | Validation | Empty message string | Deployed | **PASS** | Status 422 Unprocessable Entity |
| **H2** | Validation | Whitespace-only message | Deployed | **PASS** | Status 422 Unprocessable Entity |
| **H3** | Validation | Oversized message (>2000 chars) | Deployed | **PASS** | Status 422 Unprocessable Entity |
| **H4** | Validation | Exact boundary message (2000 chars) | Deployed | **PASS** | Status 200 OK, accepted and answered |
| **H5** | Validation | Unicode and emoji handling | Deployed | **PASS** | Status 200 OK, unicode handled properly |
| **D1** | Memory | Chat with persistent memory enabled | Deployed | **FAIL** | Status 200, but degraded with `memory_status: "unavailable"` |

**Live Deployed Results:** 23 Passed, 2 Failed.

---

## 3. Prioritized Bug Report

### ISSUE-01: Thread Event-Loop Contention in `MemoryService.client` (Hindsight SDK)
- **Issue ID:** `ISSUE-01`
- **Title:** Singleton Hindsight SDK client is bound to closed AnyIO worker thread event loop, causing `RuntimeError: Event loop is closed` on subsequent memory operations.
- **Severity:** **High**
- **Affected Feature:** Persistent Memory Recall & Retention (`MemoryService.recall`, `MemoryService.retain_turn`, `MemoryService.ensure_bank`).
- **Reproduction Steps:**
  1. Send a request to `/api/chat` with `use_memory: true`.
  2. Let worker thread complete and close its event loop.
  3. Send a second request to `/api/chat` with `use_memory: true`.
- **Expected Behavior:** `MemoryService` recalls customer memories from Hindsight Cloud and returns `memory_status: "active"`.
- **Actual Observed Behavior:** The underlying `aiohttp.ClientSession` raises `RuntimeError: Event loop is closed`. `AgentService` catches `MemoryUnavailableError` and degrades to `memory_status: "unavailable"` with banner: *"Memory temporarily unavailable — answering without history."*
- **Environment:** Deployed production & Multi-threaded server runtimes.
- **Evidence:** Reproduction in concurrent worker threads triggered:
  ```
  RuntimeError: Event loop is closed
  Unclosed client session: <aiohttp.client.ClientSession>
  ```
- **Root Cause:** In `backend/app/services/memory.py`, `self.client = Hindsight(...)` is initialized once during service startup. `hindsight_client` uses `_run_async` with `aiohttp`. An `aiohttp.ClientSession` cannot be shared across different event loops or closed threads.
- **Proposed Fix:** Refactor `MemoryService.client` into a dynamic property that generates a client instance bound to the caller thread's active event loop, while supporting explicit mocking for unit tests.
- **Fix Implemented:** Replaced static `self.client` in `MemoryService` (`backend/app/services/memory.py`) with a dynamic property that generates a thread-safe client instance per request and supports `_explicit_client` assignment for unit test mocking.
- **Verification:** Added `test_memory_service_client_property_thread_safe` in `tests/unit/test_reliability.py`. Verified multi-threaded concurrent execution succeeds without `RuntimeError: Event loop is closed`.
- **Status:** **Fixed (Verified Locally; Requires Live Redeploy)**

---

### ISSUE-02: Deep Health Check Failure on Live Service (`/api/health/deep`)
- **Issue ID:** `ISSUE-02`
- **Title:** `GET /api/health/deep` returns 503 `status: degraded, hindsight: down` due to client teardown loop conflict and unhandled credential formatting.
- **Severity:** **High**
- **Affected Feature:** Production Health & Liveness Probing (`backend/app/api/health.py`).
- **Reproduction Steps:**
  1. Send `GET https://paynest-support-agent.onrender.com/api/health/deep`.
- **Expected Behavior:** Returns HTTP 200 OK `{"status":"ok","hindsight":"ok","llm":"ok"}`.
- **Actual Observed Behavior:** Returns HTTP 503 `{"status":"degraded","hindsight":"down","llm":"ok"}`.
- **Environment:** Deployed production (`https://paynest-support-agent.onrender.com/api/health/deep`).
- **Evidence:** `HTTP 503: {"status":"degraded","hindsight":"down","llm":"ok"}`.
- **Root Cause:**
  1. `client.close()` inside worker thread triggers `RuntimeError: Task got Future attached to a different loop`.
  2. `deep_health_check` catches `Exception` with zero server logging, obscuring errors.
  3. Pydantic settings do not sanitize accidental surrounding quotes (`"..."`) or `Bearer ` prefixes from pasted environment variables.
- **Proposed Fix:** Add logging to `deep_health_check`, sanitize credential inputs in `Settings`, and safely probe Hindsight connectivity without event loop corruption.
- **Fix Implemented:** Updated `backend/app/api/health.py` with `logger = logging.getLogger(__name__)`, wrapped `client.close()` in safe exception handling, and logged specific failure causes to server logs.
- **Verification:** Verified `test_deep_health_live` in `tests/integration/test_health_deep.py` and `test_shallow_health_endpoint` in `tests/unit/test_health.py` pass cleanly.
- **Status:** **Fixed (Verified Locally; Requires Live Redeploy)**

---

### ISSUE-03: Static File Route Missing `/static` Prefix Mount
- **Issue ID:** `ISSUE-03`
- **Title:** Static assets return 404 when requested via `/static/styles.css` or `/static/js/app.js`.
- **Severity:** **Medium**
- **Affected Feature:** Static File Serving (`backend/app/main.py`).
- **Reproduction Steps:**
  1. Send `GET /static/styles.css` to the live service.
- **Expected Behavior:** Returns HTTP 200 with stylesheet.
- **Actual Observed Behavior:** Returns HTTP 404 Not Found.
- **Environment:** Deployed production & Local.
- **Evidence:** Probing script output:
  ```
  FAILED https://paynest-support-agent.onrender.com/static/css/styles.css: HTTP Error 404: Not Found
  SUCCESS 200 https://paynest-support-agent.onrender.com/styles.css len=22016
  ```
- **Root Cause:** `main.py` only mounts `app.mount("/", StaticFiles(...))`.
- **Proposed Fix:** Add `app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")` alongside the root mount.
- **Fix Implemented:** Added `app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")` in `backend/app/main.py` prior to the root mount.
- **Verification:** Updated `test_static_assets_served` in `tests/unit/test_health.py` to assert both `/styles.css`, `/app.js`, `/static/styles.css`, and `/static/app.js` return HTTP 200 with proper MIME types.
- **Status:** **Fixed (Verified Locally; Requires Live Redeploy)**

---

### ISSUE-04: Credential Trimming & Sanitization in Settings
- **Issue ID:** `ISSUE-04`
- **Title:** `Settings` does not strip surrounding whitespace, single/double quotes, or `Bearer ` prefixes from API keys.
- **Severity:** **Low / Reliability Improvement**
- **Affected Feature:** Configuration Management (`backend/app/config.py`).
- **Reproduction Steps:**
  1. Set `HINDSIGHT_API_KEY='"ey..."'` or `' ey...'` in `.env` or Render Dashboard.
  2. Make an API call to Hindsight.
- **Expected Behavior:** Key is cleaned and accepted by Hindsight Cloud API.
- **Actual Observed Behavior:** Hindsight rejects key with `401 Unauthorized: Invalid API key format`.
- **Environment:** Local and Production.
- **Proposed Fix:** Add `@field_validator("HINDSIGHT_API_KEY", "GROQ_API_KEY", "SESSION_SECRET", mode="before")` to automatically clean credentials.
- **Fix Implemented:** Added before-mode field validators in `backend/app/config.py` for `HINDSIGHT_BASE_URL`, `HINDSIGHT_API_KEY`, `GROQ_API_KEY`, and `SESSION_SECRET` to strip leading/trailing whitespace, quotes, and extraneous `Bearer ` prefixes.
- **Verification:** Added `test_settings_sanitizes_credentials_and_urls` in `tests/unit/test_health.py`. Verified that malformed environment variables with quotes and prefixes parse cleanly.
- **Status:** **Fixed (Verified Locally; Requires Live Redeploy)**

---

## 4. Limitations & Non-Destructive Constraints
- **Production Secrets:** Live production environment variables in the Render dashboard cannot be directly viewed or changed from the local environment. Any required dashboard environment variable adjustments will be documented for user action.
- **Customer Data Safety:** No production SQLite records or Hindsight memory banks were deleted during testing.
- **Deployment Requirement:** Render is configured with `autoDeploy: true` in `render.yaml`. Committing and pushing these fixes to the `main` branch will automatically trigger Render to rebuild and redeploy the service.
