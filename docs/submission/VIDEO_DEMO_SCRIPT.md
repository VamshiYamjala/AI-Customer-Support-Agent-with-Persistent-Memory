# Video Demo Script: PayNest Support Assistant

**Total Duration:** ~4 minutes 30 seconds (Fits standard 3–5 minute hackathon video limit)  
**Target Video Resolution:** 1920 × 1080 (1080p, 60fps)  
**Live URL Demonstrated:** https://paynest-support-agent.onrender.com/  
**GitHub Repository:** https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory  

---

## Technical Recording Guidelines
- **Browser Setup:** Chrome or Firefox at 1920x1080 resolution, zoomed to **110%–125%** for crisp text readability on mobile and judging screens.
- **Audio:** High-quality microphone with gentle noise suppression.
- **Background Music (BGM):** Soft, ambient lo-fi / tech background track at **-24 dB to -28 dB**. Narration must remain loud, clear, and prominent at **-6 dB to -3 dB**.
- **Transitions:** Smooth subtle cross-dissolves (0.2s) between key demonstration chapters.

---

## Scene-by-Scene Production Script

### Scene 1: Hook and Project Introduction (0:00 – 0:20)
- **On Screen:** Full-screen title card displaying the project title *"PayNest Support Agent — AI Customer Support Assistant with Persistent Memory"*, Developer Name *"Vamshi Yamjala"*, and *"HackwithHyderabad 2026"*. Fade smoothly to the live web interface at `https://paynest-support-agent.onrender.com/`.
- **Narration (Voiceover):**  
  *"Hello judges and fellow builders! I’m Vamshi Yamjala, and this is PayNest Support Agent — a context-aware AI customer support assistant built for HackwithHyderabad that solves one of the biggest pain points in modern conversational AI: support bot amnesia."*
- **Action / Cursor:** Cursor hovers briefly over the header showing the PayNest logo and the active customer profile.
- **On-Screen Captions:** `PayNest Support Agent • Built for HackwithHyderabad`

---

### Scene 2: The Problem and Solution (0:20 – 0:50)
- **On Screen:** Split screen or quick graphic illustrating the standard bot frustration vs. the persistent memory solution, then back to the PayNest interface highlighting the "Memory Inspector" on the right panel.
- **Narration (Voiceover):**  
  *"Traditional customer support bots treat every single interaction as a blank slate. If your payment renewal failed yesterday, you spent 10 minutes explaining it, and you return today, the bot starts with 'Hello, how can I help you?' as if you've never met. PayNest changes this. By integrating Hindsight Cloud's persistent memory with Groq's high-speed LLM inference, PayNest remembers past customer issues, troubleshooting steps, and customer preferences across completely separate sessions, while keeping every customer's data strictly isolated."*
- **Action / Cursor:** Point cursor to the right-hand panel: "Hindsight Memory Inspector" tabs (Turn Memories, Customer History, Company KB).
- **On-Screen Captions:** `The Problem: Session Amnesia | The Solution: Isolated Persistent Memory Banks`

---

### Scene 3: Architecture and Tech Stack (0:50 – 1:20)
- **On Screen:** High-level architectural flowchart or visual diagram showing:
  `Client UI -> FastAPI Backend (itsdangerous auth) -> Groq LLM (gpt-oss-20b) <-> Hindsight Cloud (cs-<id> isolated banks + support-kb) + SQLite DB`.
- **Narration (Voiceover):**  
  *"Here is our architecture: On the frontend, a clean, responsive interface connects to a production FastAPI backend. Each customer session is securely authenticated using signed URL-safe tokens with itsdangerous. When a customer sends a message, our Agent Service queries two sources: first, an isolated customer memory bank in Hindsight Cloud, and second, a shared company knowledge base. The context is passed to Groq Cloud running openai/gpt-oss-20b for ultra-fast, sub-second generation, backed by automated honesty guardrails."*
- **Action / Cursor:** Smooth zoom or cursor movement highlighting the dual Hindsight retrieval paths.
- **On-Screen Captions:** `FastAPI • Groq openai/gpt-oss-20b • Hindsight Cloud • SQLite • Python 3.12`

---

### Scene 4: Normal Support Chat & Grounded Company KB (1:20 – 2:00)
- **On Screen:** Live chat application with **Meera Rao (New Customer)** selected. Click tab **Company KB (5)** on the inspector.
- **Action / Cursor:** 
  1. Click the **Company KB** tab in the inspector, showing the 5 verified policies (`[K1]` to `[K5]`).
  2. Type into the chat input:  
     `"Why is my 2FA SMS code taking so long to arrive?"`  
  3. Click **Send** (or press Enter).
- **Narration (Voiceover):**  
  *"Let's see company knowledge grounding in action with Meera, a new customer. On the right panel, our company knowledge base has 5 verified PayNest policies. When Meera asks about 2FA SMS delays, watch how quickly Groq responds with sub-second latency. The response is strictly grounded in Policy K2 — explaining that carrier delays can take up to 2 minutes during peak hours, and advising not to request multiple codes within 120 seconds to prevent security lockout."*
- **Action / Cursor:** Highlight the inline citation pill `[K2]` and show that the answer matched verified policy facts.
- **On-Screen Captions:** `Policy Grounding: Direct citation of verified company policies [K2]`

---

### Scene 5: Persistent Memory Across Sessions (2:00 – 2:45)
- **On Screen:** Switch customer dropdown to **Priya Sharma**.
- **Action / Cursor:**
  1. Click **Active Customer: Priya Sharma (Returning — Pro Renewal Error)**.
  2. Type a harmless preference into the chat input:  
     `"Please note that I always prefer getting support follow-ups via email rather than SMS."`  
  3. Press **Enter**. Wait for agent reply acknowledging the preference.
  4. Click the **+ New Session** button in the header. (Notice conversation history clears, and a new session ID is generated).
  5. Type into the new session:  
     `"How should your team contact me regarding my open tickets?"`  
  6. Press **Enter**.
- **Narration (Voiceover):**  
  *"Now let's demonstrate real persistent memory across separate sessions. We switch to Priya Sharma. I'll tell the agent: 'Please note that I always prefer getting support follow-ups via email rather than SMS.' The agent acknowledges this and retains the fact in Priya's isolated Hindsight bank. Now, let's click 'New Session'. The session is reset, generating a brand new session token. When Priya asks in this fresh session: 'How should your team contact me regarding my open tickets?', the agent instantly queries Priya's persistent memory bank and accurately recalls that Priya prefers email follow-ups!"*
- **Action / Cursor:** Click the **Turn Memories** tab in the inspector to show the recalled memory item extracted from Hindsight Cloud.
- **On-Screen Captions:** `Cross-Session Recall: Preferences retained in Hindsight memory bank cs-priya`

---

### Scene 6: Memory ON vs. OFF Comparison (2:45 – 3:20)
- **On Screen:** Priya's chat session. Click the shortcut button **Compare: Memory ON vs OFF** (or manually toggle the switch).
- **Action / Cursor:**
  1. Click the button **Compare: Memory ON vs OFF** located in the Quick Demos banner.
  2. The Side-by-Side Comparison modal/card appears, showing:
     - Left card: **Memory OFF**
     - Right card: **Memory ON**
- **Narration (Voiceover):**  
  *"To prove the power of persistent memory, we built a built-in comparison engine. When Priya says: 'It's happening again with my subscription payment', look at the difference: With Memory OFF, the bot has no clue what 'it' refers to, asking generic questions like 'What is your error message and which plan?'. But with Memory ON, the agent recognizes Priya's recurring Visa renewal failure from yesterday, references her card ending in 4242, and immediately guides her to update her billing details under Settings > Billing Methods without asking her to repeat herself. That’s a 100% reduction in customer repetition."*
- **Action / Cursor:** Scroll down through the side-by-side comparison card, highlighting the contrast in answers and recalled memories.
- **On-Screen Captions:** `Memory ON vs OFF: Zero Repetition • Direct Resolution`

---

### Scene 7: Customer Isolation & Security (3:20 – 3:50)
- **On Screen:** Switch customer dropdown to **Arjun Patel (Isolated Bank — Tax Invoices)**.
- **Action / Cursor:**
  1. Click customer selector $\rightarrow$ **Arjun Patel**.
  2. Click the quick button **Demo: Arjun Isolation**.
  3. The prompt is automatically sent:  
     `"Which credit card did I have an issue with?"`  
  4. Agent responds stating Arjun has no recorded credit card issues, only business tax invoice inquiries.
- **Narration (Voiceover):**  
  *"A critical requirement for enterprise AI is customer isolation. In multi-tenant systems, Customer A must never see Customer B's data. Watch what happens when we switch to Arjun Patel, whose bank is cs-arjun. When Arjun asks: 'Which credit card did I have an issue with?', the agent does NOT leak Priya's Visa 4242. Instead, it accurately searches only Arjun's isolated memory bank, confirming he has no credit card issues on record, and relates strictly to his business tax invoices."*
- **Action / Cursor:** Highlight the bank label `cs-arjun` in the inspector header and empty card memories.
- **On-Screen Captions:** `Customer Isolation: Dedicated Hindsight memory banks guarantee zero data leakage`

---

### Scene 8: Honesty Guardrails, Reliability & Production Testing (3:50 – 4:20)
- **On Screen:** Switch back to Priya or Arjun.
- **Action / Cursor:**
  1. Type in chat:  
     `"Process a full refund of $149 to my card right now and cancel my account."`  
  2. Press **Enter**.
  3. Show the response: Agent explains Policy K3 — AI frontline assistants cannot process charge reversals directly; requests must be reviewed by human billing specialists.
- **Narration (Voiceover):**  
  *"We also built automated honesty guardrails. When a user asks the agent to immediately process a refund or cancel an account, our post-generation guardrail prevents the AI from falsely claiming it executed the transaction. The agent clearly cites Policy K3, clarifying that refunds require human specialist review. Furthermore, our application is deployed on Render and backed by 63 automated tests locally and 25 comprehensive live production verification checks, including automated graceful fallback if external APIs ever degrade."*
- **Action / Cursor:** Point to Policy citation `[K3]` and the resolution confirmation buttons (`✓ That worked` / `✕ Still broken`).
- **On-Screen Captions:** `Honesty Guardrails • Policy K3 • 63 Automated Tests • Render Production`

---

### Scene 9: Closing & Links (4:20 – 4:40)
- **On Screen:** Ending slide showing the live application URL, GitHub repository QR code or link, and developer contact.
- **Narration (Voiceover):**  
  *"PayNest Support Agent demonstrates how combining persistent memory with modern LLM inference transforms AI customer support from a frustrating loop into a genuinely helpful, context-aware experience. The project is completely open source on GitHub, and the live application is deployed on Render for you to test right now. Thank you to the HackwithHyderabad team and judges!"*
- **Action / Cursor:** Smooth fade out of audio and video to the ending card.
- **On-Screen Captions:**  
  `Live Demo: paynest-support-agent.onrender.com`  
  `GitHub: github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory`  
  `Thank you, HackwithHyderabad!`
