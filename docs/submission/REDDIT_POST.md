# Reddit Post — PayNest Support Assistant

This document contains 3 title options, a full technical post body, a concise alternative, and recommended subreddits with rules guidance.

---

## 1. Title Options (Choose One)

- **Option A (Technical & Direct)**:  
  *I built an AI customer support agent with persistent cross-session memory using FastAPI, Groq, and Hindsight Cloud [Live Demo + Code]*

- **Option B (Problem-First)**:  
  *Fixing the "support bot amnesia" problem: Here is how I implemented isolated persistent memory across customer sessions for a hackathon*

- **Option C (Show & Tell)**:  
  *Show Reddit: PayNest Support — An AI assistant that remembers past ticket resolutions without leaking data across customers*

---

## 2. Complete Post Body (Recommended for Technical Subreddits)

Hey everyone,

One of the most frustrating parts of AI customer support bots is that they suffer from complete amnesia between sessions. If your subscription renewal fails on Monday, you explain the situation, and then come back on Tuesday, the bot starts over with *"Hello! How can I help you today?"* as if it has never met you before.

For the **HackwithHyderabad** hackathon, I set out to tackle this problem by building **PayNest Support Agent** — an open-source, context-aware AI support assistant that remembers customer history and preferences across separate sessions while enforcing strict isolation between accounts.

- 🌐 **Live Deployed App**: https://paynest-support-agent.onrender.com/
- 💻 **GitHub Repository**: https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory

### System Architecture
1. **Inference Layer**: Groq Cloud running `openai/gpt-oss-20b` for low-latency reasoning and token generation.
2. **Persistent Memory Layer**: **Hindsight Cloud** provides semantic recall and factual retention. Each customer is assigned a strictly isolated memory bank (`cs-<customer_id>`). Customer A's memories cannot be searched or recalled by Customer B.
3. **Company Knowledge Base**: A shared Hindsight bank (`support-kb`) contains verified policies (refund timelines, 2FA carrier delays, invoice rules).
4. **Backend**: FastAPI with Uvicorn on Python 3.12, handling token-based session security (`itsdangerous`) and SQLite persistence for audit trails.
5. **Frontend**: Lightweight vanilla HTML5/CSS/JavaScript with a real-time **Memory Inspector** that shows judges and users what facts were recalled for each response.

### Demos Included in the Live App:
- **Priya (Returning Customer)**: Shows how the agent immediately recognizes a recurring card renewal issue without requiring re-explanation.
- **Memory ON vs. OFF Switch**: A real-time toggle that demonstrates how the prompt and response diverge when persistent memory is disabled versus enabled.
- **Arjun (Customer Isolation)**: Demonstrates that switching to another customer persona strictly isolates memories — Arjun's invoice inquiries never see Priya's subscription data.
- **Honesty Guardrails**: If you prompt the bot with *"Cancel my account and refund my card right now"*, it refuses to claim that it processed the transaction, adhering to frontline agent boundaries.

### Technical Challenge Faced
Deploying to Render surfaced an interesting issue with asynchronous event loops in Python 3.12. The Hindsight SDK client relies on `aiohttp` wrapped in synchronous helper loops. When FastAPI routed concurrent requests to worker threads in AnyIO thread pools, subsequent calls encountered closed loops (`RuntimeError: Event loop is closed`). Refactoring the memory service to manage thread-safe dynamic client instances solved the issue cleanly. We currently have 63 local unit/integration tests and 25 live production tests passing.

I'd appreciate any constructive feedback on the memory isolation architecture, UI/UX, or ways to improve agent grounding!

---

## 3. Short Post Version (For Quick Feedback / Showcases)

Hey devs,

I built an open-source AI support assistant called **PayNest** that solves support bot amnesia by persisting customer history across sessions.

- **Stack**: FastAPI, Groq (`openai/gpt-oss-20b`), Hindsight Cloud memory banks, SQLite, Vanilla JS.
- **Features**: Isolated per-customer memory banks (`cs-<id>`), Memory ON/OFF comparison toggle, live memory inspector, and guardrails against hallucinated actions (e.g., claiming refunds have been issued).

Live Demo: https://paynest-support-agent.onrender.com/  
GitHub Repo: https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory

Would love feedback on the architecture and live demo!

---

## 4. Suggested Subreddits & Community Guidelines

> [!IMPORTANT]
> **Check community self-promotion rules before posting!** Many subreddits require specific tags (e.g. `[Project]`, `[Showcase]`, or `Showoff Saturday`).

| Subreddit | Recommended Title Prefix | Rules to Check |
|:---|:---|:---|
| **r/FastAPI** | `[Project] AI Customer Support Agent with Persistent Memory` | Allows project showcases built on FastAPI. Keep it technical and focus on the backend architecture. |
| **r/Python** | `Showcase Sunday: Built a support agent with persistent memory using FastAPI & Groq` | Check if self-promotion or project showcases are restricted to specific days (e.g., Showcase Sunday / What's Everyone Working On). |
| **r/SideProject** | `Show Reddit: PayNest — AI support agent with persistent memory` | Welcomes live links, project demos, and founder feedback. |
| **r/artificial** or **r/LocalLLaMA** | Discuss memory architecture and Hindsight integration | Focus discussion on agent memory isolation and latency optimization. |
