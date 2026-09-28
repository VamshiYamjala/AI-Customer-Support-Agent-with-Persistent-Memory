# Video Storyboard — PayNest Support Assistant

This storyboard maps each scene to visual layouts, UI states, on-screen text, and audio cues for the 4-minute demonstration video.

---

```
+-----------------------------------------------------------------------------+
| Scene 1 (0:00 - 0:20) | Title Card & Live Service Landing                   |
+-----------------------------------------------------------------------------+
| VISUAL LAYOUT:                                                              |
| [Centered Title Card]                                                       |
|   💳 PayNest Support Agent                                                 |
|   Persistent Memory • Context-Aware Customer Support                        |
|   Developer: Vamshi Yamjala | Event: HackwithHyderabad                      |
|                                                                             |
| DISSOLVE TO: Live Web UI at https://paynest-support-agent.onrender.com/     |
| Top Bar: Brand, Customer Picker, Memory Toggle, Session ID                  |
| Left: Chat Window | Right: Hindsight Memory Inspector                       |
| AUDIO CUE: Gentle tech BGM fades in (-26 dB). Voiceover: Clean introduction.|
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| Scene 2 (0:20 - 0:50) | The Problem (Bot Amnesia) vs. The Solution          |
+-----------------------------------------------------------------------------+
| VISUAL LAYOUT:                                                              |
| Split Screen Graphic or Focus Callout:                                      |
|   LEFT: Standard Chatbots (Blank state, repetitive questions)               |
|   RIGHT: PayNest (Persistent context, past tickets, instant recognition)    |
| FOCUS: Right panel of PayNest UI showing "Hindsight Memory Inspector".      |
| AUDIO CUE: Narration explains customer frustration and persistent memory.   |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| Scene 3 (0:50 - 1:20) | Technical Architecture Diagram                      |
+-----------------------------------------------------------------------------+
| VISUAL LAYOUT:                                                              |
| Full-Screen Flowchart:                                                      |
|   [Client UI] ---> [FastAPI / Uvicorn Backend]                              |
|                          |                   |                              |
|             [Hindsight Cloud Banks]    [Groq Cloud LLM]                     |
|             - cs-priya (Isolated)      - gpt-oss-20b                        |
|             - cs-arjun (Isolated)      - sub-second latency                 |
|             - support-kb (Shared)                                           |
|                          |                                                  |
|                  [SQLite Audit DB]                                          |
| AUDIO CUE: Upbeat explanation of multi-tenant isolation and Groq inference. |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| Scene 4 (1:20 - 2:00) | Live Support Chat & Company KB Grounding            |
+-----------------------------------------------------------------------------+
| VISUAL LAYOUT:                                                              |
| Customer: Meera Rao (New Customer)                                         |
| Inspector Tab: Company KB (5 Verified Policies)                             |
| Chat Prompt: "Why is my 2FA SMS code taking so long to arrive?"             |
| Chat Output: Fast response citing [K2] carrier delays and 120s limit.       |
| Callout Box: Highlight inline citation pill [K2].                           |
| AUDIO CUE: Focus on policy adherence and anti-hallucination.                |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| Scene 5 (2:00 - 2:45) | Persistent Memory Across Separate Sessions          |
+-----------------------------------------------------------------------------+
| VISUAL LAYOUT:                                                              |
| 1. Switch Customer to Priya Sharma.                                         |
| 2. Input: "Please note I prefer support follow-ups via email."              |
| 3. Click "+ New Session" button (header clears, new session ID created).   |
| 4. Fresh Prompt: "How should your team contact me for open tickets?"        |
| 5. Agent recalls email preference! Inspector shows recalled memory item.    |
| AUDIO CUE: Emphasize the session reset and seamless cross-session recall.   |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| Scene 6 (2:45 - 3:20) | Live Memory ON vs. OFF Comparison Engine            |
+-----------------------------------------------------------------------------+
| VISUAL LAYOUT:                                                              |
| Click banner button: "Compare: Memory ON vs OFF".                           |
| Modal / Card comparison renders side-by-side:                               |
|   - LEFT (Memory OFF): Generic question asking which plan and error.        |
|   - RIGHT (Memory ON): Immediately identifies Visa 4242 & renewal failure.  |
| Metric Badge: "100% Repetition Reduction".                                  |
| AUDIO CUE: Direct contrast of customer experience.                          |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| Scene 7 (3:20 - 3:50) | Customer Isolation Verification                     |
+-----------------------------------------------------------------------------+
| VISUAL LAYOUT:                                                              |
| 1. Switch Customer to Arjun Patel (cs-arjun).                               |
| 2. Click "Demo: Arjun Isolation".                                           |
| 3. Prompt: "Which credit card did I have an issue with?"                    |
| 4. Agent states Arjun has no credit card history; his records relate only   |
|    to business tax invoices. Zero leakage from Priya's cs-priya bank.       |
| AUDIO CUE: Stress data privacy and multi-tenant security guarantees.        |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| Scene 8 (3:50 - 4:20) | Honesty Guardrails & Reliability Testing            |
+-----------------------------------------------------------------------------+
| VISUAL LAYOUT:                                                              |
| 1. Input: "Process a full refund to my card right now and cancel account."   |
| 2. Agent refuses unauthorized action and quotes Policy K3.                  |
| 3. Click resolution outcome button: "✓ That worked".                        |
| 4. Brief flash of terminal showing "63 passed" and Render health status.    |
| AUDIO CUE: Highlight engineering rigor, unit tests, and production health.  |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| Scene 9 (4:20 - 4:40) | Closing, GitHub, and Live Demo Links                |
+-----------------------------------------------------------------------------+
| VISUAL LAYOUT:                                                              |
| Full-Screen Outro Slide:                                                    |
|   PayNest Support Assistant                                                 |
|   Live Demo: https://paynest-support-agent.onrender.com/                    |
|   GitHub: https://github.com/VamshiYamjala/AI-Customer-Support-Agent...     |
|   Developer: Vamshi Yamjala                                                 |
|   HackwithHyderabad 2026                                                    |
| AUDIO CUE: Warm thank-you to judges and community. BGM swells and fades out.|
+-----------------------------------------------------------------------------+
```
