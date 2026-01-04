#!/usr/bin/env python3
"""
Comprehensive Selenium Tests for Refactored GPTGram System
Tests moderator agents, enhanced chain builder, and complete system integration
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
WAIT_TIMEOUT = 10

class TestRefactoredSystem:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def setup(self):
        """Setup Chrome driver"""
        print("🔧 Setting up Chrome WebDriver...")
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, WAIT_TIMEOUT)
        print("✅ WebDriver ready")
        
    def teardown(self):
        """Cleanup"""
        if self.driver:
            self.driver.quit()
            
    def log_test(self, name, passed, details=""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        self.test_results.append({
            "name": name,
            "passed": passed,
            "details": details
        })
        
    def login(self):
        """Login to the application"""
        try:
            self.driver.get(f"{FRONTEND_URL}/login")
            time.sleep(2)
            
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.send_keys("demo")
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys("demo123")
            
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in')]")
            login_button.click()
            
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False
            
    def test_moderator_agent_api(self):
        """Test moderator agent backend APIs"""
        try:
            # Create moderator node
            create_response = requests.post(f"{BACKEND_URL}/api/moderator/create", json={
                "node_id": "test_mod_1",
                "name": "Test Moderator",
                "position": {"x": 100, "y": 100},
                "prompt_template": "Align @Source output to @Target input",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"}
            })
            self.log_test("Moderator Create API", create_response.status_code == 200)
            
            # Check compatibility
            compat_response = requests.post(f"{BACKEND_URL}/api/moderator/check-compatibility", json={
                "source_output": {"text": "test"},
                "target_input_schema": {"required": ["content"], "properties": {"content": {"type": "string"}}}
            })
            self.log_test("Compatibility Check API", compat_response.status_code == 200)
            
            # Execute moderator
            exec_response = requests.post(f"{BACKEND_URL}/api/moderator/execute", json={
                "node_id": "test_mod_1",
                "user_input": "Test input",
                "upstream_outputs": {"Source": {"text": "test"}}
            })
            self.log_test("Moderator Execute API", exec_response.status_code == 200)
            
            return True
        except Exception as e:
            self.log_test("Moderator Agent APIs", False, str(e))
            return False
            
    def test_enhanced_chain_builder(self):
        """Test enhanced chain builder with moderator"""
        try:
            self.driver.get(f"{FRONTEND_URL}/chains")
            time.sleep(3)
            
            # Check for React Flow canvas
            canvas = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "react-flow"))
            )
            self.log_test("React Flow Canvas Present", canvas is not None)
            
            # Check for agent library
            library = self.driver.find_elements(By.XPATH, "//h2[contains(text(), 'Agent Library')]")
            self.log_test("Agent Library Present", len(library) > 0)
            
            # Check for Add Moderator button
            moderator_btn = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Add Moderator Agent')]")
            self.log_test("Add Moderator Button", len(moderator_btn) > 0)
            
            # Check for wallet balance
            wallet = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Wallet:')]")
            self.log_test("Wallet Balance Display", len(wallet) > 0)
            
            return True
        except Exception as e:
            self.log_test("Enhanced Chain Builder", False, str(e))
            return False
            
    def test_dashboard_real_data(self):
        """Test dashboard shows real backend data"""
        try:
            self.driver.get(f"{FRONTEND_URL}/")
            time.sleep(3)
            
            # Check for real metrics
            metrics = self.driver.find_elements(By.CLASS_NAME, "text-2xl")
            self.log_test("Dashboard Metrics Present", len(metrics) > 0)
            
            # Verify wallet API call
            wallet_response = requests.get(f"{BACKEND_URL}/api/wallet/balance")
            self.log_test("Wallet API Working", wallet_response.status_code == 200)
            
            # Verify analytics API
            analytics_response = requests.get(f"{BACKEND_URL}/api/analytics/data")
            self.log_test("Analytics API Working", analytics_response.status_code == 200)
            
            return True
        except Exception as e:
            self.log_test("Dashboard Real Data", False, str(e))
            return False
            
    def test_agent_creation_flow(self):
        """Test agent creation and verification"""
        try:
            self.driver.get(f"{FRONTEND_URL}/agents")
            time.sleep(3)
            
            # Check for create button
            create_btn = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Create')]")
            self.log_test("Agent Create Button", len(create_btn) > 0)
            
            # Check for agent cards
            agent_cards = self.driver.find_elements(By.CLASS_NAME, "cursor-pointer")
            self.log_test("Agent Cards Display", len(agent_cards) > 0)
            
            # Check for verification badges
            badges = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'L')]")
            self.log_test("Verification Badges", len(badges) > 0)
            
            return True
        except Exception as e:
            self.log_test("Agent Creation Flow", False, str(e))
            return False
            
    def test_stripe_integration(self):
        """Test Stripe payment integration"""
        try:
            # Test checkout session creation
            checkout_response = requests.post(
                f"{BACKEND_URL}/api/wallet/create-checkout-session",
                json={"amount": 1000}
            )
            self.log_test("Stripe Checkout API", checkout_response.status_code == 200)
            
            if checkout_response.status_code == 200:
                data = checkout_response.json()
                self.log_test("Checkout URL Generated", 'url' in data)
            
            return True
        except Exception as e:
            self.log_test("Stripe Integration", False, str(e))
            return False
            
    def test_live_metrics_dashboard(self):
        """Test live metrics and WebSocket updates"""
        try:
            self.driver.get(f"{FRONTEND_URL}/analytics")
            time.sleep(3)
            
            # Check for charts
            charts = self.driver.find_elements(By.CLASS_NAME, "recharts-wrapper")
            self.log_test("Analytics Charts Present", len(charts) > 0)
            
            # Check for transform method distribution
            transform_section = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Transform')]")
            self.log_test("Transform Methods Section", len(transform_section) > 0)
            
            # Check for real-time indicators
            activity = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Activity')]")
            self.log_test("Activity Feed", len(activity) > 0)
            
            return True
        except Exception as e:
            self.log_test("Live Metrics Dashboard", False, str(e))
            return False
            
    def test_chain_execution(self):
        """Test chain execution with moderator"""
        try:
            # Test execution API
            exec_request = {
                "chain_id": "test-chain",
                "nodes": [
                    {"id": "node1", "type": "agent", "agent_id": "summarizer"},
                    {"id": "mod1", "type": "moderator"},
                    {"id": "node2", "type": "agent", "agent_id": "sentiment"}
                ],
                "edges": [
                    {"source": "node1", "target": "mod1"},
                    {"source": "mod1", "target": "node2"}
                ]
            }
            
            response = requests.post(f"{BACKEND_URL}/api/chain/execute", json=exec_request)
            self.log_test("Chain Execution API", response.status_code == 200)
            
            return True
        except Exception as e:
            self.log_test("Chain Execution", False, str(e))
            return False
            
    def test_ui_navigation(self):
        """Test all UI navigation links work"""
        try:
            pages = [
                ('/', 'Dashboard'),
                ('/wallet', 'Wallet'),
                ('/agents', 'Agent'),
                ('/chains', 'Chain'),
                ('/runs', 'Run'),
                ('/analytics', 'Analytics')
            ]
            
            working = 0
            for path, keyword in pages:
                self.driver.get(f"{FRONTEND_URL}{path}")
                time.sleep(1)
                
                # Check page loaded
                if keyword.lower() in self.driver.page_source.lower():
                    working += 1
            
            self.log_test("UI Navigation", working >= 5, f"{working}/6 pages working")
            
            return working >= 5
        except Exception as e:
            self.log_test("UI Navigation", False, str(e))
            return False
            
    def test_moderator_duplication(self):
        """Test moderator node duplication"""
        try:
            # Test duplicate API
            response = requests.post(f"{BACKEND_URL}/api/moderator/duplicate/test_mod_1", 
                                    json={"x": 200, "y": 200})
            
            if response.status_code == 404:
                # Create first
                requests.post(f"{BACKEND_URL}/api/moderator/create", json={
                    "node_id": "test_mod_1",
                    "name": "Test",
                    "position": {"x": 100, "y": 100},
                    "prompt_template": "Test",
                    "input_schema": {},
                    "output_schema": {}
                })
                response = requests.post(f"{BACKEND_URL}/api/moderator/duplicate/test_mod_1",
                                        json={"x": 200, "y": 200})
            
            self.log_test("Moderator Duplication", response.status_code == 200)
            
            return response.status_code == 200
        except Exception as e:
            self.log_test("Moderator Duplication", False, str(e))
            return False
            
    def test_token_resolution(self):
        """Test @agent.field token resolution"""
        try:
            # Test token resolution API
            response = requests.post(f"{BACKEND_URL}/api/chain/resolve-atokens", json={
                "template": {"text": "@Summarizer.summary"},
                "outputs_map": {"Summarizer": {"summary": "Test text"}}
            })
            
            self.log_test("Token Resolution API", response.status_code == 200)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Tokens Resolved", data.get('resolved_payload', {}).get('text') == "Test text")
            
            return True
        except Exception as e:
            self.log_test("Token Resolution", False, str(e))
            return False
            
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🚀 REFACTORED SYSTEM COMPREHENSIVE TESTS")
        print("="*60 + "\n")
        
        self.setup()
        
        # Login first
        if not self.login():
            print("❌ Login failed - aborting tests")
            self.teardown()
            return
            
        print("\n📋 TEST 1: Moderator Agent APIs")
        self.test_moderator_agent_api()
        
        print("\n📋 TEST 2: Enhanced Chain Builder")
        self.test_enhanced_chain_builder()
        
        print("\n📋 TEST 3: Dashboard Real Data")
        self.test_dashboard_real_data()
        
        print("\n📋 TEST 4: Agent Creation Flow")
        self.test_agent_creation_flow()
        
        print("\n📋 TEST 5: Stripe Integration")
        self.test_stripe_integration()
        
        print("\n📋 TEST 6: Live Metrics Dashboard")
        self.test_live_metrics_dashboard()
        
        print("\n📋 TEST 7: Chain Execution")
        self.test_chain_execution()
        
        print("\n📋 TEST 8: UI Navigation")
        self.test_ui_navigation()
        
        print("\n📋 TEST 9: Moderator Duplication")
        self.test_moderator_duplication()
        
        print("\n📋 TEST 10: Token Resolution")
        self.test_token_resolution()
        
        # Print results
        self.print_results()
        self.teardown()
        
    def print_results(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        print(f"\n✅ PASSED: {self.passed_tests}/{self.total_tests} tests")
        print(f"❌ FAILED: {self.total_tests - self.passed_tests}/{self.total_tests} tests")
        print(f"📈 SUCCESS RATE: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 EXCELLENT! All refactored system tests passed!")
        elif self.passed_tests / self.total_tests >= 0.8:
            print("\n✅ Good! Most tests passed.")
        else:
            print("\n⚠️ Warning: Several tests failed. Review the details above.")
            
        print("\n" + "="*60)

if __name__ == "__main__":
    tester = TestRefactoredSystem()
    tester.run_all_tests()
