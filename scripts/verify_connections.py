#!/usr/bin/env python3
"""
scripts/verify_connections.py
Level 1 verification script for PayNest.
Verifies Hindsight Cloud and Groq LLM connections, introspects SDK, and runs an isolation smoke test.
Never logs or prints secret keys in full (at most masks all but the last 4 chars).
"""

import inspect
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure stdout uses UTF-8 to handle unicode symbols smoothly on Windows
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def mask_key(k: str) -> str:
    if not k:
        return "<EMPTY>"
    if len(k) <= 6:
        return "***"
    return f"...{k[-4:]}"


def main():
    print("=" * 60)
    print("  AI Customer Support Agent with Persistent Memory")
    print("  Level 1 - Service Connection Verification")
    print("=" * 60)

    # 1. Load .env
    env_path = Path(".env")
    if not env_path.exists():
        print("[FAIL] .env file not found in current directory!")
        sys.exit(1)

    load_dotenv(dotenv_path=env_path)

    required_vars = [
        "HINDSIGHT_BASE_URL",
        "HINDSIGHT_API_KEY",
        "HINDSIGHT_BANK_PREFIX",
        "HINDSIGHT_SHARED_KB_BANK",
        "GROQ_API_KEY",
        "GROQ_MODEL",
        "SESSION_SECRET",
    ]

    missing = []
    unfilled = []
    for var in required_vars:
        val = os.getenv(var)
        if val is None or val.strip() == "":
            missing.append(var)
        elif "PASTE_" in val or "your-" in val:
            unfilled.append(var)

    if missing or unfilled:
        print("[FAIL] Environment configuration incomplete:")
        if missing:
            print(f"  Missing variable(s): {', '.join(missing)}")
        if unfilled:
            print(f"  Variables still containing template placeholders: {', '.join(unfilled)}")
            print("  Please edit your .env file and paste your actual API keys.")
        sys.exit(1)

    base_url = os.getenv("HINDSIGHT_BASE_URL").rstrip("/")
    hindsight_key = os.getenv("HINDSIGHT_API_KEY").strip()
    groq_key = os.getenv("GROQ_API_KEY").strip()
    groq_model = os.getenv("GROQ_MODEL").strip()

    print(f"[OK] .env loaded successfully.")
    print(f"     Hindsight Base URL : {base_url}")
    print(f"     Hindsight API Key  : {mask_key(hindsight_key)}")
    print(f"     Groq API Key       : {mask_key(groq_key)}")
    print(f"     Groq Model         : {groq_model}")

    # 2. Introspect Hindsight SDK
    print("\n--- 2. SDK Introspection ---")
    try:
        from hindsight_client import Hindsight
    except ImportError as e:
        print(f"[FAIL] Could not import hindsight_client: {e}")
        print("       Ensure dependencies are installed in .venv.")
        sys.exit(1)

    sig_retain = inspect.signature(Hindsight.retain)
    sig_recall = inspect.signature(Hindsight.recall)

    has_tags_retain = "tags" in sig_retain.parameters
    has_tags_recall = "tags" in sig_recall.parameters

    print(f"Hindsight.retain signature: {sig_retain}")
    print(f"Hindsight.recall signature: {sig_recall}")
    print(f"Tags parameter in retain: {has_tags_retain}")
    print(f"Tags parameter in recall: {has_tags_recall}")

    # Save to docs/verified-sdk-notes.md
    sdk_notes_path = Path("docs/verified-sdk-notes.md")
    sdk_notes_content = f"""# Verified SDK Notes

- Date: 2026-09-28
- Hindsight Python Client: `hindsight-client`
- `Hindsight.retain` signature: `{sig_retain}`
- `Hindsight.recall` signature: `{sig_recall}`
- `tags` parameter present in `retain()`: `{has_tags_retain}`
- `tags` parameter present in `recall()`: `{has_tags_recall}`
"""
    sdk_notes_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sdk_notes_path, "w", encoding="utf-8") as f:
        f.write(sdk_notes_content)
    print(f"[OK] SDK notes recorded in {sdk_notes_path}")

    # 3. Connect to Hindsight Client & get version
    print("\n--- 3. Hindsight Cloud Connection ---")
    try:
        client = Hindsight(base_url=base_url, api_key=hindsight_key, timeout=30.0)
        version_info = client.get_version()
        print(f"[OK] Hindsight reachable! api_version: {version_info}")
    except Exception as e:
        print(f"[FAIL] Hindsight connection error: {e}")
        print("       Check HINDSIGHT_BASE_URL and HINDSIGHT_API_KEY in .env.")
        sys.exit(1)

    all_passed = True
    check_results = {}

    # 4. Bank Creation test & Auto-create behavior test
    print("\n--- 4. Memory Bank Test ---")
    test_bank_id = "cs-connection-test"
    try:
        res = client.create_bank(
            bank_id=test_bank_id,
            name="Connection test",
            mission="Test bank for connection verification only.",
        )
        print(f"[OK] Bank '{test_bank_id}' created successfully: {res}")
        check_results["Bank Creation"] = "PASS"
    except Exception as e:
        err_msg = str(e)
        if "already exists" in err_msg.lower() or "conflict" in err_msg.lower():
            print(f"[OK] Bank '{test_bank_id}' already exists (safe to proceed).")
            check_results["Bank Creation"] = "PASS"
        else:
            print(f"[FAIL] Error during create_bank: {err_msg}")
            check_results["Bank Creation"] = f"FAIL ({err_msg})"
            all_passed = False

    # 5. Retain test
    print("\n--- 5. Retain Operation Test ---")
    retain_passed = False
    try:
        retain_res = client.retain(
            bank_id=test_bank_id,
            content="The test user likes blue widgets.",
            context="connection test",
            document_id="verify-001",
            retain_async=False,
        )
        print(f"[OK] retain succeeded: {retain_res}")
        check_results["Hindsight Retain"] = "PASS"
        retain_passed = True
    except Exception as e:
        print(f"[FAIL] Retain operation failed: {e}")
        check_results["Hindsight Retain"] = f"FAIL ({e})"
        all_passed = False

    # 6. Recall test
    print("\n--- 6. Recall Operation Test ---")
    try:
        recall_res = client.recall(
            bank_id=test_bank_id,
            query="What does the test user like?",
        )
        results = getattr(recall_res, "results", [])
        if not results and retain_passed:
            print(f"[FAIL] Recall returned 0 results for '{test_bank_id}'.")
            check_results["Hindsight Recall"] = "FAIL (0 results)"
            all_passed = False
        else:
            first_text = results[0].text if results and hasattr(results[0], "text") else (results[0] if results else "None")
            print(f"[OK] recall response received ({len(results)} items). Snippet: {first_text}")
            check_results["Hindsight Recall"] = "PASS"
    except Exception as e:
        print(f"[FAIL] Recall operation failed: {e}")
        check_results["Hindsight Recall"] = f"FAIL ({e})"
        all_passed = False

    # 7. Groq connection & chat test
    print("\n--- 7. Groq LLM Test ---")
    try:
        from groq import Groq

        groq_client = Groq(api_key=groq_key)
        models_resp = groq_client.models.list()
        model_ids = [m.id for m in models_resp.data]
        print(f"[OK] Groq reachable! {len(model_ids)} models available.")
        print(f"     Active models: {model_ids}")

        target_model = groq_model if groq_model in model_ids else "openai/gpt-oss-20b"
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "user", "content": "Reply with only the word OK"}
            ],
            model=target_model,
            max_tokens=60,
            temperature=0.0,
        )
        reply = chat_completion.choices[0].message.content.strip()
        print(f"[OK] LLM response received using '{target_model}': '{reply}'")
        check_results["Groq LLM Connection & Reply"] = f"PASS ('{reply}')"
    except Exception as e:
        print(f"[FAIL] Groq LLM check failed: {e}")
        check_results["Groq LLM Connection & Reply"] = f"FAIL ({e})"
        all_passed = False

    # 8. Cross-Customer Isolation Smoke Test
    print("\n--- 8. Cross-Customer Isolation Smoke Test ---")
    bank_a = "cs-conn-iso-a"
    bank_b = "cs-conn-iso-b"
    unique_secret = "The secret passphrase is purple-unicorn-7789."

    try:
        for b in [bank_a, bank_b]:
            try:
                client.create_bank(bank_id=b, name=b, mission="Isolation test bank.")
            except Exception:
                pass

        if retain_passed:
            client.retain(
                bank_id=bank_a,
                content=unique_secret,
                context="isolation test",
                document_id="iso-001",
                retain_async=False,
            )
            print(f"[OK] Retained isolated secret into bank '{bank_a}'")

            res_b = client.recall(bank_id=bank_b, query="What is the secret passphrase?")
            results_b = getattr(res_b, "results", [])
            leaks = [r for r in results_b if "purple-unicorn" in getattr(r, "text", str(r))]

            if len(leaks) > 0:
                print(f"[FAIL] Isolation breach! Bank '{bank_b}' leaked secret from '{bank_a}'!")
                check_results["Cross-Customer Isolation"] = "FAIL (Isolation breach)"
                all_passed = False
            else:
                print(f"[OK] Isolation test passed! Bank '{bank_b}' returned 0 leaked results.")
                check_results["Cross-Customer Isolation"] = "PASS"
        else:
            print("[SKIP] Skipping retention isolation check until retain permissions/credits are active.")
            check_results["Cross-Customer Isolation"] = "BLOCKED (Retain 402)"
    except Exception as e:
        print(f"[FAIL] Isolation test encountered an error: {e}")
        check_results["Cross-Customer Isolation"] = f"FAIL ({e})"
        all_passed = False

    finally:
        try:
            client.close()
        except Exception:
            pass

    # 9. Summary & Completion
    print("\n" + "=" * 60)
    print("  VERIFICATION SCORECARD")
    print("=" * 60)
    for check_name, status in check_results.items():
        print(f"  - {check_name:<30}: {status}")
    print("=" * 60)

    if not all_passed:
        print("\n[!] Level 1 gate incomplete. Address the failing checks above.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] ALL LEVEL 1 GATE CHECKS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
