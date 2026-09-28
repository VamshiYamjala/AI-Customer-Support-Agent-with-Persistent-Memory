"""
scripts/capture_screenshots.py
Automated end-to-end browser testing script using Playwright.
Takes full-page screenshots of every core feature on localhost:8000:
1. Initial landing & dashboard
2. Live conversational chat turn
3. Priya Sharma Session 2 persistent memory recall ([M1], [K1] citations)
4. Side-by-side comparison (Memory ON vs OFF)
5. Arjun Patel tenant memory isolation (zero cross-customer leakage)
6. Inspector tabs: Graph Relations (HydraDB) & Company KB
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = r"C:\Users\gocha\.gemini\antigravity\brain\2f3400f5-8b4e-4457-988d-5b618e929742"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def run():
    print(f"Starting Playwright browser to test http://localhost:8000...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Step 1: Initial Landing
        print("Navigating to http://localhost:8000...")
        page.goto("http://localhost:8000")
        page.wait_for_selector(".app-header")
        time.sleep(1)
        shot1 = os.path.join(ARTIFACTS_DIR, "screenshot_01_landing.png")
        page.screenshot(path=shot1)
        print(f"Captured: {shot1}")

        # Step 2: Send 'hi' message
        print("Sending message 'hi'...")
        page.fill("#chat-input", "hi")
        page.click("#send-btn")
        # Wait for assistant response
        page.wait_for_selector(".message.assistant", timeout=15000)
        time.sleep(2)
        shot2 = os.path.join(ARTIFACTS_DIR, "screenshot_02_live_chat_hi.png")
        page.screenshot(path=shot2)
        print(f"Captured: {shot2}")

        # Step 3: Run Priya Session 2 Demo
        print("Running Priya Session 2 Demo button...")
        page.click("#demo-btn-priya-s2")
        time.sleep(4)
        shot3 = os.path.join(ARTIFACTS_DIR, "screenshot_03_priya_session2.png")
        page.screenshot(path=shot3)
        print(f"Captured: {shot3}")

        # Step 4: Run Compare ON vs OFF
        print("Running Compare ON vs OFF Demo button...")
        page.click("#demo-btn-compare")
        page.wait_for_selector(".comparison-card", timeout=20000)
        time.sleep(3)
        shot4 = os.path.join(ARTIFACTS_DIR, "screenshot_04_comparison_on_vs_off.png")
        page.screenshot(path=shot4)
        print(f"Captured: {shot4}")

        # Step 5: Switch to Arjun Patel & Isolation Check
        print("Switching to Arjun Patel...")
        page.select_option("#customer-select", "arjun")
        time.sleep(2)
        page.click("#demo-btn-arjun")
        time.sleep(4)
        shot5 = os.path.join(ARTIFACTS_DIR, "screenshot_05_arjun_isolation.png")
        page.screenshot(path=shot5)
        print(f"Captured: {shot5}")

        # Step 6: Test Inspector Tabs
        print("Testing Inspector Graph Relations Tab...")
        page.click("button[data-tab='graph']")
        time.sleep(1)
        shot6 = os.path.join(ARTIFACTS_DIR, "screenshot_06_inspector_graph.png")
        page.screenshot(path=shot6)
        print(f"Captured: {shot6}")

        print("Testing Inspector Company KB Tab...")
        page.click("button[data-tab='kb']")
        time.sleep(1)
        shot7 = os.path.join(ARTIFACTS_DIR, "screenshot_07_inspector_kb.png")
        page.screenshot(path=shot7)
        print(f"Captured: {shot7}")

        browser.close()
        print("All screenshots successfully captured!")

if __name__ == "__main__":
    run()
