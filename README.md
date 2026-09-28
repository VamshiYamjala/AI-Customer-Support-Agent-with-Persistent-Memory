# AI Customer Support Agent with Persistent Memory (PayNest Support Assistant)

An intelligent, context-aware customer support assistant built for **HackwithHyderabad 3.0**, powered by **Hindsight by Vectorize** and **Groq LLMs**.

## Overview
Traditional support bots suffer from session amnesia: customers must re-explain recurring payment errors, previously tried troubleshooting steps, and communication preferences each time they return. 

This project solves customer support amnesia by assigning each customer a dedicated, isolated persistent memory bank in Hindsight. The assistant remembers prior issues, what was tried, confirmed resolutions, and preferences across sessions while strictly isolating customer data.

## Persistent Memory Architecture (Hindsight)
- **Isolated Per-Customer Memory Banks**:
  - Each customer receives their own dedicated memory bank in Hindsight (e.g. `cs-priya`, `cs-arjun`).
  - Cross-customer memory leakage is structurally impossible: queries are scoped strictly to the authenticated customer bank.
  - Defense-in-depth: Queries enforce `tags=["customer:{customer_id}"]` with `tags_match="all_strict"`.
- **Company Knowledge Base Bank**:
  - Shared knowledge is maintained in a separate company bank (`support-kb`).
  - Contains verified known troubleshooting resolutions with no customer personal data.
- **Complete Memory Lifecycle**:
  1. **Capture**: Conversation turns and customer-confirmed outcomes are formatted into structured transcripts.
  2. **Sanitize**: Credit card numbers are masked to `****-****-****-XXXX`, and CVVs, OTPs, and passwords are fully redacted before retention.
  3. **Retain**: Written to Hindsight using idempotent `document_id=f"{session_id}-t{turn_no}"` to prevent duplicate facts.
  4. **Consolidate**: Hindsight automatically links entities, updates temporal beliefs, and produces consolidated observations in the background.
  5. **Recall**: Multi-modal retrieval (semantic, keyword, graph, temporal) retrieves relevant facts within a token budget.
  6. **Use**: Recalled facts are injected into system prompts as quoted `<memories>` data with citation tags (`[M1]`, `[M2]`).
- **Resilient Fallback**:
  - If the external memory service is temporarily unreachable, the assistant does not crash. It provides support with a clean warning banner: *"Memory temporarily unavailable — answering without history."*

## Tech Stack
- **Persistent Memory**: [Hindsight Cloud](https://api.hindsight.vectorize.io) via `hindsight-client` Python SDK
- **LLM Provider**: [Groq](https://console.groq.com) (`openai/gpt-oss-20b`)
- **Backend API**: Python 3.12, FastAPI, Uvicorn, Pydantic Settings
- **Local Storage**: SQLite (session tokens, message audit, tickets)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (no build step, served directly by FastAPI)

## Quick Start (Local Run)
1. **Activate Virtual Environment**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
2. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your keys:
   ```dotenv
   HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
   HINDSIGHT_API_KEY=your_hindsight_key
   GROQ_API_KEY=your_groq_key
   GROQ_MODEL=openai/gpt-oss-20b
   ```
3. **Run the Application**:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```
4. **Access the App**:
   - Web App UI: [http://localhost:8000](http://localhost:8000)
   - Interactive OpenAPI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)
   - Deep Health Check: [http://localhost:8000/api/health/deep](http://localhost:8000/api/health/deep)

## API Endpoints
- `GET /api/health` — Shallow liveness probe.
- `GET /api/health/deep` — Live connectivity check to Hindsight Cloud and Groq LLM.
- `POST /api/chat` — Chat with the support assistant with persistent memory:
  ```bash
  # Memory ON (default)
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"customer_id": "priya", "message": "My card failed at checkout again", "use_memory": true}'

  # Memory OFF
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"customer_id": "priya", "message": "My card failed at checkout again", "use_memory": false}'
  ```

## Running Tests
```powershell
# Run unit tests (mocked, no network calls, fast)
pytest -m unit

# Run live integration tests (connects to live services)
pytest -m integration

# Run full test suite
pytest -q
```
