# Solving Support Bot Amnesia: Building an AI Customer Support Agent with Persistent Memory

**Author:** Vamshi Yamjala  
**Event:** HackwithHyderabad 2026  
**Live Deployed Application:** [https://paynest-support-agent.onrender.com/](https://paynest-support-agent.onrender.com/)  
**GitHub Repository:** [https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory](https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory)  
**Tech Stack:** Python 3.12, FastAPI, Groq (`openai/gpt-oss-20b`), Hindsight Cloud, SQLite, Vanilla HTML/CSS/JS, Render  

---

## Abstract

Most conversational AI assistants today suffer from **instant amnesia**. When a customer returns to a support portal after experiencing an issue the previous day, the bot starts over with a blank slate: *"Hello, how can I help you today?"* The customer is forced to re-explain their billing error, repeat their card details, and retrace past troubleshooting attempts.

For **HackwithHyderabad 2026**, I engineered **PayNest Support Agent** — an open-source, context-aware AI support assistant featuring isolated persistent memory across customer sessions. By pairing **Groq's ultra-fast LLM inference** with **Hindsight Cloud's isolated memory banks**, PayNest remembers customer interaction history, past resolutions, and communication preferences across separate sessions without compromising multi-tenant data privacy.

This article details the end-to-end architecture, customer isolation mechanisms, honesty guardrails, and key production engineering lessons learned while deploying the application to Render.

---

## The Problem: Why Context Loss Breaks Customer Support

In traditional customer support workflows, customer dissatisfaction is rarely caused by the bot's tone; it is caused by **repetition fatigue**. 

1. **Context Fragmentation**: Typical LLM chat interfaces maintain context only within the active session window. Once the session expires, closes, or restarts, all conversational history evaporates.
2. **Data Leakage Risks in Multi-Tenant AI**: Simply dumping past customer conversations into a global vector database introduces severe cross-customer data leakage risks. Customer A's invoice or credit card issues must never influence Customer B's queries.
3. **Hallucinated Actions**: Standard LLMs frequently over-promise. When a frustrated user demands *"Refund my card immediately"*, off-the-shelf bots often respond with *"I have processed your refund of $49"*, creating severe financial and customer trust liabilities when no actual transaction occurred.

---

## System Architecture

To solve these challenges, PayNest Support was built as a multi-tiered system combining sub-second inference, strict per-customer memory isolation, and automated honesty verification.

```
                              ┌─────────────────────────────────────────┐
                              │            Client Browser               │
                              │  (HTML5 / CSS / JS / Memory Inspector)  │
                              └───────────────────┬─────────────────────┘
                                                  │ HTTP / JSON (Bearer Token)
                                                  ▼
                              ┌─────────────────────────────────────────┐
                              │           FastAPI Backend               │
                              │  - Session Auth (itsdangerous)          │
                              │  - PII Masking & Sanitization           │
                              │  - Orchestrator (AgentService)          │
                              └───────┬──────────────────────┬──────────┘
                                      │                      │
             ┌────────────────────────┴────────┐             │
             ▼                                 ▼             ▼
┌─────────────────────────┐       ┌──────────────────────┐ ┌────────────────┐
│     Hindsight Cloud     │       │      Groq Cloud      │ │ SQLite DB      │
│  - cs-priya (Isolated)  │       │  openai/gpt-oss-20b  │ │ - Sessions     │
│  - cs-arjun (Isolated)  │       │  Sub-second latency  │ │ - Messages     │
│  - support-kb (Shared)  │       │  Grounded generation │ │ - Audit Logs   │
└─────────────────────────┘       └──────────────────────┘ └────────────────┘
```

### 1. The Inference Layer (Groq Cloud)
For customer support, generation latency is critical. We utilize **Groq Cloud** running `openai/gpt-oss-20b`. Groq's LPUs (Language Processing Units) deliver sub-second token generation, enabling real-time conversational responses even after performing multi-source memory retrieval.

### 2. Isolated Persistent Memory (Hindsight Cloud)
Rather than maintaining a monolithic vector store, PayNest integrates with **Hindsight Cloud** to partition memories into dedicated memory banks:
- **Per-Customer Memory Banks (`cs-<customer_id>`)**: Each customer is assigned a unique, isolated bank (e.g., `cs-priya`, `cs-arjun`). When Priya chats, the backend queries strictly within `cs-priya`.
- **Shared Company Knowledge Base (`support-kb`)**: A shared bank containing verified PayNest business rules, subscription upgrade rules, refund review workflows, and 2FA carrier delay policies.
- **Dual-Context Retrieval**: Every user turn queries both the customer's personal bank and the shared policy bank. Relevant facts are retrieved with semantic relevance scores and temporal tags.

### 3. Identity and Session Authorization
The client never passes raw customer IDs in chat payloads. Authentication relies on cryptographically signed URL-safe bearer tokens created with `itsdangerous`. The customer's identity is resolved server-side from the bearer token, preventing customer spoofing or cross-tenant query injection.

---

## Key Features & Live Demonstrations

The deployed application includes interactive demo scenarios designed for evaluators:

### 1. Returning Customer Experience (Priya Sharma)
Priya is a Pro subscriber who encountered a failed renewal payment on her Visa card ending in 4242 yesterday. When Priya returns in a completely fresh session and says:
> *"It's happening again with my subscription payment."*

With persistent memory enabled, the agent immediately recalls her past card failure from bank `cs-priya`, connects it with Policy `[K1]` (outdated billing zip code / expired card), and instructs her to navigate to **Settings > Billing Methods** without asking Priya to re-explain the issue.

### 2. Live Memory ON vs. OFF Comparison
The interface includes a real-time comparison toggle:
- **Memory OFF**: The agent replies with generic, boilerplate questions: *"What error message did you see? Which subscription plan are you on?"*
- **Memory ON**: The agent directly references past ticket details and card ending 4242, achieving a **100% reduction in customer repetition**.

### 3. Guaranteed Customer Isolation (Arjun Patel)
To prove multi-tenant isolation, switching to **Arjun Patel** (`cs-arjun`) and asking:
> *"Which credit card did I have an issue with?"*

The agent searches only `cs-arjun`, confirming that Arjun has no credit card issues on file and that his account history relates solely to business tax invoices. Priya's financial records are completely invisible to Arjun.

### 4. Automated Honesty Guardrails
Frontline support agents cannot reverse credit card charges directly. If a user enters:
> *"Process a full refund to my card right now and cancel my account."*

The agent's output passes through an automated regex and citation guardrail. Any fabricated claims such as *"I have processed your refund"* are automatically intercepted and replaced with clear policy citations (`[K3]`), explaining that refund requests require review by human billing specialists.

---

## Production Reliability: An Asynchronous Concurrency Challenge

During production deployment on Render, an edge case emerged regarding asynchronous Python event loops:

### The Bug
In `backend/app/services/memory.py`, the Hindsight SDK client was initially instantiated as a singleton on service startup. Under the hood, `hindsight_client` wraps an `aiohttp.ClientSession` using synchronous `_run_async` loops. 

FastAPI routes synchronous request handlers through AnyIO worker thread pools. When the first thread completed and closed its local event loop, subsequent chat turns executed in different worker threads encountered:
```text
RuntimeError: Event loop is closed
Unclosed client session: <aiohttp.client.ClientSession>
```
This triggered graceful degradation, returning `memory_status: "unavailable"` on subsequent requests.

### The Solution
We refactored `MemoryService.client` into a dynamic property that instantiates a thread-safe client bound to the active worker thread's event loop, while supporting explicit mock injection for unit testing:

```python
@property
def client(self) -> Hindsight:
    """
    Returns an active Hindsight SDK client.
    Generates a thread-safe client instance bound to the calling thread's event loop,
    preventing 'RuntimeError: Event loop is closed' across AnyIO worker pools.
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
```

Additionally, before-mode Pydantic field validators were introduced to sanitize environment variables by automatically stripping accidental surrounding quotes (`"..."` / `'...'`) and extraneous `Bearer ` prefixes from pasted secrets.

### Verification
Following this fix:
- **63 / 63 automated tests** pass locally across 11 test suites.
- **25 / 25 end-to-end verification scenarios** pass on the live Render deployment, including deep health checks (`/api/health/deep`), customer isolation, and multi-turn memory recall.

---

## Conclusion

By treating customer memory as a first-class, secure, and isolated architectural layer, **PayNest Support Agent** bridges the gap between static LLM reasoning and real-world customer support needs. The combination of **FastAPI**, **Groq LLM**, and **Hindsight Cloud** demonstrates that AI support agents can be both deeply context-aware and enterprise-secure.

### Explore the Project
- 🌐 **Live Web Application**: [https://paynest-support-agent.onrender.com/](https://paynest-support-agent.onrender.com/)
- 💻 **Full Source Code**: [https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory](https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory)
- 📄 **Documentation & QA Reports**: Available in the `/docs` directory of the repository.

*Built with passion by Vamshi Yamjala for HackwithHyderabad 2026.*
