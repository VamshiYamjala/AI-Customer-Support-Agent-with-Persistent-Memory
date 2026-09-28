# Video Recording, Editing & QC Guide

A practical, beginner-friendly guide to recording, voicing, and editing the 4-minute demonstration video for **HackwithHyderabad**.

---

## 1. Title & Ending Card Specifications

### Title Card (Scene 1: 0:00–0:05)
- **Background**: Dark slate navy (`#0f172a`) with subtle glowing accent.
- **Top Badge**: `HackwithHyderabad 2026 Submission`
- **Main Title**: `PayNest Support Agent` (Bold, White, ~64pt)
- **Subtitle**: `Context-Aware AI Assistant with Persistent Memory` (Cyan, ~32pt)
- **Footer**: `Built by Vamshi Yamjala • FastAPI • Groq • Hindsight • SQLite`

### Ending Card (Scene 9: 4:20–4:40)
- **Background**: Dark slate navy (`#0f172a`).
- **Headline**: `Try PayNest Support Live`
- **Live Demo Link**: `https://paynest-support-agent.onrender.com/`
- **GitHub Repository**: `github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory`
- **Closing Note**: `Thank you, HackwithHyderabad Judges & Community!`

---

## 2. Voiceover-Only Script (Continuous Read)

Use this clean script if you prefer recording your voice track first or speaking along with the screen recording:

> *"Hello judges and fellow builders! I’m Vamshi Yamjala, and this is PayNest Support Agent — a context-aware AI customer support assistant built for HackwithHyderabad that solves one of the biggest pain points in modern conversational AI: support bot amnesia.*
>
> *Traditional customer support bots treat every single interaction as a blank slate. If your payment renewal failed yesterday, you spent 10 minutes explaining it, and you return today, the bot starts with 'Hello, how can I help you?' as if you've never met. PayNest changes this. By integrating Hindsight Cloud's persistent memory with Groq's high-speed LLM inference, PayNest remembers past customer issues, troubleshooting steps, and customer preferences across completely separate sessions, while keeping every customer's data strictly isolated.*
>
> *Here is our architecture: On the frontend, a clean, responsive interface connects to a production FastAPI backend. Each customer session is securely authenticated using signed URL-safe tokens with itsdangerous. When a customer sends a message, our Agent Service queries two sources: first, an isolated customer memory bank in Hindsight Cloud, and second, a shared company knowledge base. The context is passed to Groq Cloud running openai/gpt-oss-20b for ultra-fast, sub-second generation, backed by automated honesty guardrails.*
>
> *Let's see company knowledge grounding in action with Meera, a new customer. On the right panel, our company knowledge base has 5 verified PayNest policies. When Meera asks about 2FA SMS delays, watch how quickly Groq responds with sub-second latency. The response is strictly grounded in Policy K2 — explaining that carrier delays can take up to 2 minutes during peak hours, and advising not to request multiple codes within 120 seconds to prevent security lockout.*
>
> *Now let's demonstrate real persistent memory across separate sessions. We switch to Priya Sharma. I'll tell the agent: 'Please note that I always prefer getting support follow-ups via email rather than SMS.' The agent acknowledges this and retains the fact in Priya's isolated Hindsight bank. Now, let's click 'New Session'. The session is reset, generating a brand new session token. When Priya asks in this fresh session: 'How should your team contact me regarding my open tickets?', the agent instantly queries Priya's persistent memory bank and accurately recalls that Priya prefers email follow-ups!*
>
> *To prove the power of persistent memory, we built a built-in comparison engine. When Priya says: 'It's happening again with my subscription payment', look at the difference: With Memory OFF, the bot has no clue what 'it' refers to, asking generic questions like 'What is your error message and which plan?'. But with Memory ON, the agent recognizes Priya's recurring Visa renewal failure from yesterday, references her card ending in 4242, and immediately guides her to update her billing details under Settings > Billing Methods without asking her to repeat herself. That’s a 100% reduction in customer repetition.*
>
> *A critical requirement for enterprise AI is customer isolation. In multi-tenant systems, Customer A must never see Customer B's data. Watch what happens when we switch to Arjun Patel, whose bank is cs-arjun. When Arjun asks: 'Which credit card did I have an issue with?', the agent does NOT leak Priya's Visa 4242. Instead, it accurately searches only Arjun's isolated memory bank, confirming he has no credit card issues on record, and relates strictly to his business tax invoices.*
>
> *We also built automated honesty guardrails. When a user asks the agent to immediately process a refund or cancel an account, our post-generation guardrail prevents the AI from falsely claiming it executed the transaction. The agent clearly cites Policy K3, clarifying that refunds require human specialist review. Furthermore, our application is deployed on Render and backed by 63 automated tests locally and 25 comprehensive live production verification checks, including automated graceful fallback if external APIs ever degrade.*
>
> *PayNest Support Agent demonstrates how combining persistent memory with modern LLM inference transforms AI customer support from a frustrating loop into a genuinely helpful, context-aware experience. The project is completely open source on GitHub, and the live application is deployed on Render for you to test right now. Thank you to the HackwithHyderabad team and judges!"*

---

## 3. Screen Recording Checklist

- [ ] **Resolution**: 1920 × 1080 (Full HD).
- [ ] **Browser Window**: Fullscreen (`F11`) or maximize browser without visible bookmarks bar.
- [ ] **Zoom Level**: Zoom browser to **115% or 125%** (`Ctrl + Plus`) so text, inspector cards, and badges are crisp on 1080p video.
- [ ] **Cursor**: Keep mouse movements steady and purposeful. Avoid rapid circles or erratic dragging.
- [ ] **Audio Levels**:
  - Voiceover peak levels: `-6 dB to -3 dB`.
  - Background music (optional): `-26 dB to -30 dB` (must not compete with voice).
- [ ] **Notifications**: Turn on "Do Not Disturb" on Windows to prevent popups or chime sounds during recording.

---

## 4. Beginner Recording & Editing Workflow

If you are new to video recording, this 3-step workflow is free and fast:

### Step 1: Record Screen & Voice (using OBS Studio or Loom)
1. Download **OBS Studio** (Free, Open Source) or use **Loom / Clipchamp** (built into Windows 11).
2. Set Source: **Display Capture** or **Window Capture (Chrome)**.
3. Audio Input: Select your microphone. Run a 10-second mic test to check levels.
4. Record the walkthrough following the scene-by-scene script.

### Step 2: Edit & Trim (using Clipchamp / CapCut)
1. Import your recorded video into **Microsoft Clipchamp** (free on Windows) or **CapCut**.
2. Cut out any long pauses or misspoken lines.
3. Add a simple fade-in at the beginning and fade-out at the end.
4. Add the Title Card at 0:00 and Ending Card at the end.
5. (Optional) Enable auto-generated captions for accessibility.

### Step 3: Export & Upload
1. Export as **1080p MP4**.
2. Upload to **YouTube** as **Unlisted** (or **Public**), or upload to **Loom** or **Google Drive** (ensure permissions are set to "Anyone with the link can view").
3. Copy the video link into your hackathon submission form.

---

## 5. Quality Control Checklist

- [ ] **Video Duration**: Between **3 minutes 00 seconds and 5 minutes 00 seconds**.
- [ ] **Audio Clarity**: Voice is audible without clipping, heavy background hiss, or echo.
- [ ] **Text Readability**: Code, chat messages, and memory inspector cards are legible on a mobile screen.
- [ ] **Accurate Terminology**: Correctly mentions FastAPI, Groq `openai/gpt-oss-20b`, Hindsight Cloud, and SQLite.
- [ ] **Privacy**: No secrets, `.env` files, or raw API keys appear on screen.
- [ ] **Working Links**: Live Render URL and GitHub URL are visible and verified working.
