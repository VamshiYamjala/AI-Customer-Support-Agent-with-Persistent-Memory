# PayNest: Errors Handled & Troubleshooting Log

This document records every error encountered during development, installation, verification, integration, and deployment, along with the root cause and the resolution applied.

---

| Date / Phase | Error / Symptom | Root Cause | Solution & Mitigation | Status |
|---|---|---|---|---|
| Level 0 / Setup | Local folder not linked to GitHub | Fresh local folder with no `.git` | Ran `git init`, set branch `main`, added remote origin from repository link. | Resolved |
| Level 1 / Setup | `requirements.txt` generated as UTF-16LE | Windows PowerShell redirection `>` defaults to UTF-16LE encoding | Regenerated using `Out-File -Encoding utf8 requirements.txt` for cross-platform compatibility. | Resolved |
| Level 1 / Connection | Hindsight `retain()` returns `402 Payment Required: {"detail":"Insufficient credits. Please add credits to continue."}` | Fresh Hindsight Cloud account has 0 credits allocated or requires claiming free credits / billing activation in the Vectorize dashboard. | User claimed $5.00 free credits in Hindsight Cloud dashboard. Retest verified retain/recall operating successfully. | Resolved |
| Level 1 / Runtime | Windows console `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f44b'` | Windows PowerShell stdout defaults to cp1252 encoding, which crashes when LLMs return emojis. | Set `PYTHONIOENCODING=utf-8` and configure `sys.stdout.reconfigure(encoding="utf-8")` in Python scripts. | Resolved |
| Level 3 / Testing | Unit test mock bypassed when testing LLM timeout | The `get_llm_client` singleton was already cached from previous calls, causing real Groq API to be called instead of mock. | Used FastAPI's idiomatic `app.dependency_overrides[get_llm_client]` fixture in `tests/unit/test_chat.py`. | Resolved |
| Level 6 / Database | `sqlite3.IntegrityError: UNIQUE constraint failed: sessions.id` during repeat demo seeding | `create_session` used `INSERT INTO` without conflict resolution, failing when seeding predefined demo sessions repeatedly. | Updated SQLite operations to `INSERT OR REPLACE INTO sessions` and `INSERT OR IGNORE INTO messages` in `DatabaseStore` for full idempotency. | Resolved |

---
*Note: Any upcoming errors during API verification, package installation, network calls, or runtime execution will be logged here with detailed diagnoses and solutions.*
