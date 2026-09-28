# LinkedIn Post — PayNest Support Assistant (HackwithHyderabad)

This document contains two ready-to-publish versions of the LinkedIn announcement: a **Standard Long Version** (ideal for engagement and technical storytelling) and a **Short Version** (ideal for mobile readers), along with recommended post settings and format guidelines.

---

## 1. Primary LinkedIn Post (Long Technical Storytelling Version)

Most customer support bots suffer from instant amnesia. 

You spend 10 minutes explaining that your renewal failed, wait on hold, and the next day you have to re-explain the exact same error, card details, and past attempts from scratch.

For **HackwithHyderabad**, I built and deployed **PayNest Support Agent** — an AI customer support assistant powered by persistent memory that actually remembers customer interactions, troubleshooting history, and preferences across separate sessions.

### How it works under the hood:
- **Persistent Memory Bank Isolation**: Using **Hindsight Cloud**, each customer has a dedicated, isolated memory bank (`cs-<customer_id>`). Customer A's memories can never leak into Customer B's context.
- **Fast Groq LLM Inference**: Powered by `openai/gpt-oss-20b` via Groq Cloud, generating grounded responses with sub-second latency.
- **Dual-Context Retrieval**: Merges customer-specific experiences with a shared company policy knowledge base (`support-kb`).
- **Strict Honesty Guardrails**: If a customer asks to "process a refund immediately" or "cancel my subscription", the agent never hallucinates that it has executed financial actions it lacks authorization to perform.
- **Memory ON vs. OFF Switch**: Judges and users can toggle persistent memory in real time to see the exact difference in response grounding.

### A Real Engineering Learning:
Deploying this to production on Render surfaced an interesting concurrency edge case: the Hindsight SDK client's internal `aiohttp` session was initially bound to a worker thread event loop. Under concurrent FastAPI requests in AnyIO worker pools, subsequent requests encountered closed loops. Refactoring `MemoryService` to dynamically manage thread-safe client instantiation resolved the issue, backed by 63 automated tests and 25 live production verification checks.

Try the live application and let me know your thoughts:
- 🌐 **Live Demo**: https://paynest-support-agent.onrender.com/
- 💻 **GitHub Repository**: https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory

Would love your feedback on how we can make AI memory in support systems more context-aware and secure!

#HackwithHyderabad #GenerativeAI #FastAPI #Groq #Hindsight #Python #MachineLearning #FullStack #TechCommunity #BuildingInPublic

---

## 2. Short LinkedIn Caption (Concise Mobile Version)

Ever get tired of repeating your support issue to an AI bot every single time you start a new chat?

For **HackwithHyderabad**, I built **PayNest Support Agent** — a context-aware AI assistant with persistent memory across sessions.

Built with **FastAPI**, **Groq LLM**, **Hindsight Cloud**, and **SQLite**, it features:
- Customer-specific isolated memory banks (`cs-<customer_id>`)
- Live Memory ON vs. OFF side-by-side comparison
- Grounded citations from company policies (`[K1]`) and customer history (`[M1]`)
- Automated guardrails against unauthorized action claims

Check out the live project and code:
- 🌐 Live App: https://paynest-support-agent.onrender.com/
- 💻 GitHub: https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory

Feedback and suggestions are welcome!

#HackwithHyderabad #AI #FastAPI #Groq #Hindsight #WebDevelopment #Python

---

## 3. Recommended Format & Image Specifications

- **Post Format**: Image + Text Post.
- **Image**: Attach the generated project banner located at `assets/social/linkedin_project_graphic.jpg`.
- **Dimensions**: Landscape 1200 × 627 px (16:9 ratio), optimized for desktop and mobile LinkedIn feeds.
- **Placement**: Add the text in the post body, attach the graphic, and ensure the live link previews render cleanly.
