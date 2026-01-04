#!/usr/bin/env python3
"""
Production-grade Playwright test suite for GPTGram
No hanging, proper timeouts, real assertions
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import requests

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeout

# Configuration
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 8000  # 8 seconds
MAX_TIMEOUT = 20000  # 20 seconds
LONG_TIMEOUT = 90000  # 90 seconds for chain execution

# Test credentials
TEST_USER = "demo"
TEST_PASSWORD = "demo123"

class GPTGramTester:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.passed = 0
        self.failed = 0
        self.failures = []
        
    async def setup(self, headless=True):
        """Initialize browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=['--no-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.context.set_default_timeout(DEFAULT_TIMEOUT)
        self.page = await self.context.new_page()
        
        # Log console messages
        self.page.on("console", lambda msg: print(f"[Browser] {msg.text}"))
        
    async def teardown(self):
        """Clean up browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def capture_screenshot(self, name: str):
        """Save screenshot on failure"""
        try:
            path = f"test-failures/{name}_{datetime.now():%Y%m%d_%H%M%S}.png"
            Path("test-failures").mkdir(exist_ok=True)
            await self.page.screenshot(path=path, full_page=True)
            print(f"📸 Screenshot saved: {path}")
        except:
            pass
    
    async def test_assert(self, condition: bool, test_name: str, error_msg=""):
        """Assert with proper tracking"""
        if condition:
            self.passed += 1
            print(f"✅ {test_name}")
            return True
        else:
            self.failed += 1
            self.failures.append(f"{test_name}: {error_msg}")
            print(f"❌ {test_name}: {error_msg}")
            await self.capture_screenshot(test_name.replace(" ", "_"))
            return False
    
    async def wait_and_click(self, selector: str, timeout=DEFAULT_TIMEOUT):
        """Wait for element and click"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.click(selector, timeout=timeout)
            return True
        except PlaywrightTimeout:
            return False
    
    async def wait_and_fill(self, selector: str, value: str, timeout=DEFAULT_TIMEOUT):
        """Wait for element and fill"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.fill(selector, value, timeout=timeout)
            return True
        except PlaywrightTimeout:
            return False
    
    # === TESTS ===
    
    async def test_login(self):
        """Test login flow"""
        print("\n📋 TEST: Login")
        
        await self.page.goto(FRONTEND_URL, wait_until="networkidle", timeout=MAX_TIMEOUT)
        
        # Fill login form
        filled = await self.wait_and_fill('[data-test-id="login-username-input"]', TEST_USER, 5000)
        if not filled:
            filled = await self.wait_and_fill('input[type="text"]', TEST_USER, 5000)
        
        await self.test_assert(filled, "Username input filled", "Could not find username field")
        
        filled = await self.wait_and_fill('[data-test-id="login-password-input"]', TEST_PASSWORD, 5000)
        if not filled:
            filled = await self.wait_and_fill('input[type="password"]', TEST_PASSWORD, 5000)
        
        await self.test_assert(filled, "Password input filled", "Could not find password field")
        
        # Click login
        clicked = await self.wait_and_click('[data-test-id="login-submit-button"]', 5000)
        if not clicked:
            clicked = await self.wait_and_click('button[type="submit"]', 5000)
        
        await self.test_assert(clicked, "Login button clicked", "Could not click login")
        
        # Wait for redirect
        try:
            await self.page.wait_for_url(
                lambda url: "dashboard" in url or "agents" in url,
                timeout=10000
            )
            await self.test_assert(True, "Login successful")
        except PlaywrightTimeout:
            await self.test_assert(False, "Login redirect", "No redirect after login")
    
    async def test_agents(self):
        """Test agent library"""
        print("\n📋 TEST: Agent Library")
        
        await self.page.goto(f"{FRONTEND_URL}/agents", wait_until="networkidle", timeout=MAX_TIMEOUT)
        
        # Check for agents
        agents = await self.page.query_selector_all('.cursor-pointer')
        await self.test_assert(len(agents) > 0, f"Found {len(agents)} agents", "No agents displayed")
        
        # Test create agent
        create_clicked = await self.wait_and_click('button:has-text("Create")', 3000)
        if not create_clicked:
            await self.page.goto(f"{FRONTEND_URL}/agents/create")
        
        await self.page.wait_for_timeout(2000)
        
        # Fill form
        timestamp = datetime.now().strftime("%H%M%S")
        await self.wait_and_fill('input[name="name"]', f"Test_{timestamp}", 5000)
        await self.wait_and_fill('*[name="description"]', "Test agent", 5000)
        
        # Find textareas for schemas
        textareas = await self.page.query_selector_all('textarea')
        if len(textareas) >= 2:
            await textareas[0].fill('{"type":"object","properties":{"text":{"type":"string"}}}')
            await textareas[1].fill('{"type":"object","properties":{"result":{"type":"string"}}}')
            await self.test_assert(True, "Schemas filled")
        
        # Save
        save_clicked = await self.wait_and_click('button:has-text("Save")', 5000)
        if not save_clicked:
            save_clicked = await self.wait_and_click('button:has-text("Create")', 5000)
        
        await self.test_assert(save_clicked, "Save button clicked", "Could not save agent")
        
        # Verify via API
        await self.page.wait_for_timeout(3000)
        response = requests.get(f"{BACKEND_URL}/api/agents/", timeout=5)
        
        if response.status_code == 200:
            agents = response.json()
            created = any(f"Test_{timestamp}" in agent.get("name", "") for agent in agents)
            await self.test_assert(created, "Agent created in backend", "Agent not found after creation")
    
    async def test_chain_builder(self):
        """Test chain builder"""
        print("\n📋 TEST: Chain Builder")
        
        await self.page.goto(f"{FRONTEND_URL}/chains", wait_until="networkidle", timeout=MAX_TIMEOUT)
        
        # Check for React Flow
        flow = await self.page.query_selector('.react-flow')
        await self.test_assert(flow is not None, "React Flow loaded", "Chain builder not found")
        
        # Add input node
        input_clicked = await self.wait_and_click('button:has-text("Input")', 5000)
        await self.test_assert(input_clicked, "Input node added", "Could not add input")
        
        # Add agents
        agents = await self.page.query_selector_all('.cursor-pointer')
        if len(agents) >= 2:
            await agents[0].click()
            await self.page.wait_for_timeout(1000)
            await agents[1].click()
            await self.test_assert(True, "Agents added to flow")
        
        # Check nodes exist
        nodes = await self.page.query_selector_all('.react-flow__node')
        await self.test_assert(len(nodes) >= 2, f"Found {len(nodes)} nodes", "Not enough nodes")
        
        # Add moderator
        mod_clicked = await self.wait_and_click('button:has-text("Moderator")', 3000)
        await self.test_assert(mod_clicked, "Moderator added", "Could not add moderator")
        
        # Execute chain
        run_clicked = await self.wait_and_click('button:has-text("Run")', 5000)
        if not run_clicked:
            run_clicked = await self.wait_and_click('button:has-text("Execute")', 5000)
        
        if run_clicked:
            await self.page.wait_for_timeout(5000)
            
            # Check for result
            success = await self.page.query_selector('*:has-text("success")')
            complete = await self.page.query_selector('*:has-text("complete")')
            
            await self.test_assert(
                success is not None or complete is not None,
                "Chain executed",
                "No execution result"
            )
    
    async def test_moderator_api(self):
        """Test moderator transformations"""
        print("\n📋 TEST: Moderator API")
        
        # Test Summarizer->Sentiment
        data = {
            "upstream_agent_id": "summarizer",
            "downstream_agent_id": "sentiment",
            "upstream_output": {
                "summary": "AI is amazing",
                "sentences": ["S1", "S2"],
                "key_points": ["Innovation"]
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/moderator/moderate-payload",
            json=data,
            timeout=10
        )
        
        await self.test_assert(
            response.status_code == 200,
            "Summarizer→Sentiment moderation",
            f"Status {response.status_code}"
        )
        
        if response.status_code == 200:
            payload = response.json().get("payload", {})
            await self.test_assert(
                "text" in payload or "content" in payload,
                "Payload has text field",
                f"Missing field in {payload}"
            )
        
        # Test Sentiment->Translator
        data2 = {
            "upstream_agent_id": "sentiment",
            "downstream_agent_id": "translator",
            "upstream_output": {
                "sentiment": "positive",
                "score": 0.95
            },
            "user_input": "es"
        }
        
        response2 = requests.post(
            f"{BACKEND_URL}/api/moderator/moderate-payload",
            json=data2,
            timeout=10
        )
        
        await self.test_assert(
            response2.status_code == 200,
            "Sentiment→Translator moderation",
            f"Status {response2.status_code}"
        )
        
        if response2.status_code == 200:
            payload2 = response2.json().get("payload", {})
            await self.test_assert(
                "target_language" in payload2,
                "Language field set",
                f"Missing language in {payload2}"
            )
    
    async def test_runs(self):
        """Test run history"""
        print("\n📋 TEST: Run History")
        
        await self.page.goto(f"{FRONTEND_URL}/runs", wait_until="networkidle", timeout=MAX_TIMEOUT)
        
        # Check for runs
        runs = await self.page.query_selector_all('div[class*="border"][class*="rounded"]')
        
        # Check backend
        response = requests.get(f"{BACKEND_URL}/api/runs/", timeout=5)
        backend_runs = response.json() if response.status_code == 200 else []
        
        await self.test_assert(
            len(runs) > 0 or len(backend_runs) > 0,
            f"UI: {len(runs)} runs, Backend: {len(backend_runs)} runs",
            "No runs found"
        )
    
    async def test_dashboard(self):
        """Test dashboard"""
        print("\n📋 TEST: Dashboard")
        
        await self.page.goto(f"{FRONTEND_URL}/dashboard", wait_until="networkidle", timeout=MAX_TIMEOUT)
        
        # Check metrics
        metrics = await self.page.query_selector_all('*[class*="text-2xl"], *[class*="text-3xl"]')
        await self.test_assert(
            len(metrics) > 0,
            f"Found {len(metrics)} metric cards",
            "No metrics displayed"
        )
        
        # Check activity
        activity = await self.page.query_selector_all('*:has-text("ago")')
        await self.test_assert(
            len(activity) > 0,
            f"Found {len(activity)} activity items",
            "No activity feed"
        )
    
    async def test_wallet(self):
        """Test wallet page"""
        print("\n📋 TEST: Wallet")
        
        await self.page.goto(f"{FRONTEND_URL}/wallet", wait_until="networkidle", timeout=MAX_TIMEOUT)
        
        # Check balance
        balance = await self.page.query_selector('*:has-text("Balance")')
        await self.test_assert(balance is not None, "Balance displayed", "No balance shown")
        
        # Check top-up
        topup = await self.page.query_selector('button:has-text("Top"), button:has-text("Add")')
        await self.test_assert(topup is not None, "Top-up button found", "No top-up button")
    
    async def run_all(self):
        """Run all tests"""
        print("="*70)
        print("🚀 GPTGRAM PLAYWRIGHT TEST SUITE")
        print("="*70)
        
        # Check backend
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code != 200:
                print("❌ Backend not healthy")
                return False
        except:
            print("❌ Backend not responding")
            return False
        
        print("✅ Backend is healthy")
        
        # Setup browser
        await self.setup(headless=False)  # Set True for CI
        
        try:
            # Run tests
            await self.test_login()
            await self.test_agents()
            await self.test_chain_builder()
            await self.test_moderator_api()
            await self.test_runs()
            await self.test_dashboard()
            await self.test_wallet()
            
        finally:
            await self.teardown()
        
        # Print results
        print("\n" + "="*70)
        print("📊 TEST RESULTS")
        print("="*70)
        
        total = self.passed + self.failed
        if total > 0:
            rate = (self.passed / total) * 100
            print(f"\n✅ PASSED: {self.passed}/{total}")
            print(f"❌ FAILED: {self.failed}/{total}")
            print(f"📈 SUCCESS: {rate:.1f}%")
            
            if self.failures:
                print("\n⚠️ Failures:")
                for f in self.failures:
                    print(f"  - {f}")
        
        print("="*70)
        return self.failed == 0

# Run tests
async def main():
    tester = GPTGramTester()
    success = await tester.run_all()
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
