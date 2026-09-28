# AI Customer Support Agent with Persistent Memory (PayNest Support Assistant)

An intelligent, context-aware customer support assistant built for **HackwithHyderabad 3.0**, powered by **Hindsight by Vectorize** and **Groq LLMs**.

## Overview
Traditional support bots suffer from session amnesia: customers must re-explain recurring payment errors, previously tried troubleshooting steps, and communication preferences each time they return. 

This project solves customer support amnesia by assigning each customer a dedicated, isolated persistent memory bank in Hindsight. The assistant remembers prior issues, what was tried, confirmed resolutions, and preferences across sessions while strictly isolating customer data.

## Tech Stack
- **Persistent Memory**: [Hindsight Cloud](https://api.hindsight.vectorize.io) via `hindsight-client` Python SDK
- **LLM Provider**: [Groq](https://console.groq.com)
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
   HINDSIGHT_API_KEY=your_key
   GROQ_API_KEY=your_key
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
- `POST /api/chat` — Chat with the support assistant.
  ```bash
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "How do I update my card on PayNest?", "use_memory": false}'
  ```

## Running Tests
```powershell
# Run unit tests
pytest -m unit

# Run live integration tests (uses configured keys)
pytest -m integration

# Run full test suite
pytest -q
```

