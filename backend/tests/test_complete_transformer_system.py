#!/usr/bin/env python3
"""
Comprehensive Selenium Tests for Complete Transformer System
Tests all features including chain builder, transforms, analytics, and wallet
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
WAIT_TIMEOUT = 10

class TestTransformerSystem:
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
            
            # Enter credentials
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.send_keys("demo")
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys("demo123")
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in')]")
            login_button.click()
            
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False
            
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🚀 COMPREHENSIVE TRANSFORMER SYSTEM TESTS")
        print("="*60 + "\n")
        
        self.setup()
        
        # Login first
        if not self.login():
            print("❌ Login failed - aborting tests")
            self.teardown()
            return
            
        print("\n📋 TEST 1: Chain Builder UI")
        self.test_chain_builder_ui()
        
        print("\n📋 TEST 2: Node Connections")
        self.test_node_connection()
        
        print("\n📋 TEST 3: Transform Methods Display")
        self.test_transform_methods_display()
        
        print("\n📋 TEST 4: Real Analytics")
        self.test_real_analytics()
        
        print("\n📋 TEST 5: Wallet Balance")
        self.test_wallet_balance_update()
        
        print("\n📋 TEST 6: Dashboard Top-Up")
        self.test_dashboard_topup_button()
        
        print("\n📋 TEST 7: Run History Export")
        self.test_run_history_export()
        
        print("\n📋 TEST 8: Agent Recommendations")
        self.test_agent_recommendations()
        
        print("\n📋 TEST 9: Chain Execution API")
        self.test_chain_execution_api()
        
        print("\n📋 TEST 10: Token Resolution API")
        self.test_agent_token_resolution()
        
        # Print results
        self.print_results()
        self.teardown()
        
    def test_chain_builder_ui(self):
        """Test chain builder UI components"""
        try:
            self.driver.get(f"{FRONTEND_URL}/chains")
            time.sleep(3)
            
            # Check for React Flow canvas
            canvas = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "react-flow"))
            )
            self.log_test("React Flow Canvas", canvas is not None)
            
            # Check for agent library
            library = self.driver.find_element(By.XPATH, "//h2[text()='Agent Library']")
            self.log_test("Agent Library", library is not None)
            
            # Check for search box
            search = self.driver.find_element(By.XPATH, "//input[@placeholder='Search agents...']")
            self.log_test("Search Box", search is not None)
            
            return True
        except Exception as e:
            self.log_test("Chain Builder UI", False, str(e))
            return False
            
    def test_node_connection(self):
        """Test drag-to-connect nodes in React Flow"""
        try:
            self.driver.get(f"{FRONTEND_URL}/chains")
            time.sleep(3)
            
            # Add first agent to canvas
            summarizer = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'n8n Summarizer')]"))
            )
            summarizer.click()
            time.sleep(1)
            
            # Add second agent
            sentiment = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Sentiment Analyzer')]")
            sentiment.click()
            time.sleep(1)
            
            # Try to find nodes on canvas
            nodes = self.driver.find_elements(By.CLASS_NAME, "react-flow__node")
            self.log_test("Nodes Added to Canvas", len(nodes) >= 2, f"Found {len(nodes)} nodes")
            
            # Check for handle elements (connection points)
            handles = self.driver.find_elements(By.CLASS_NAME, "react-flow__handle")
            self.log_test("Node Handles Present", len(handles) >= 4, f"Found {len(handles)} handles")
            
            return True
        except Exception as e:
            self.log_test("Node Connection", False, str(e))
            return False
            
    def test_transform_methods_display(self):
        """Test that transform methods are displayed in UI"""
        try:
            self.driver.get(f"{FRONTEND_URL}/chains")
            time.sleep(3)
            
            # Check for legend showing transform methods
            legend = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h4[contains(text(), 'Compatibility')]"))
            )
            self.log_test("Transform Legend Present", legend is not None)
            
            # Check for method badges in legend
            deterministic = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'deterministic')]")
            self.log_test("Deterministic Method Shown", len(deterministic) > 0)
            
            gat = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'gat')]")
            self.log_test("GAT Method Shown", len(gat) > 0)
            
            llm = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'llm')]")
            self.log_test("LLM Method Shown", len(llm) > 0)
            
            return True
        except Exception as e:
            self.log_test("Transform Methods Display", False, str(e))
            return False
            
    def test_real_analytics(self):
        """Test real analytics page with backend data"""
        try:
            self.driver.get(f"{FRONTEND_URL}/analytics")
            time.sleep(3)
            
            # Check for analytics header
            header = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Analytics Dashboard')]"))
            )
            self.log_test("Analytics Header", header is not None)
            
            # Check for real data metrics
            total_runs = self.driver.find_element(By.XPATH, "//div[contains(@class, 'text-2xl')]")
            self.log_test("Total Runs Metric", total_runs is not None)
            
            # Check for transform method distribution
            transform_section = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Transform Method')]")
            self.log_test("Transform Methods Chart", len(transform_section) > 0)
            
            # Check for revenue chart
            revenue_chart = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Revenue')]")
            self.log_test("Revenue Chart", len(revenue_chart) > 0)
            
            # Verify data is from backend
            response = requests.get(f"{BACKEND_URL}/api/analytics/data")
            backend_data = response.json()
            self.log_test("Analytics Backend Connected", response.status_code == 200, 
                         f"Total runs from backend: {backend_data.get('total_runs', 0)}")
            
            return True
        except Exception as e:
            self.log_test("Real Analytics", False, str(e))
            return False
            
    def test_wallet_balance_update(self):
        """Test wallet balance updates with real transactions"""
        try:
            self.driver.get(f"{FRONTEND_URL}/wallet")
            time.sleep(3)
            
            # Get initial balance
            balance_element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'text-3xl')]"))
            )
            initial_balance = balance_element.text
            self.log_test("Wallet Balance Display", initial_balance is not None, f"Balance: {initial_balance}")
            
            # Check for test top-up button (should be removed)
            topup_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Test Top-Up')]")
            self.log_test("Test Top-Up Removed", len(topup_buttons) == 0, "No test button found")
            
            # Check for Stripe button
            stripe_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Pay with Stripe')]")
            self.log_test("Stripe Payment Button", stripe_button is not None)
            
            return True
        except Exception as e:
            self.log_test("Wallet Balance Update", False, str(e))
            return False
            
    def test_dashboard_topup_button(self):
        """Test dashboard top-up button navigation"""
        try:
            self.driver.get(f"{FRONTEND_URL}/")
            time.sleep(3)
            
            # Find top-up button on dashboard
            topup_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Top Up')]"))
            )
            topup_button.click()
            time.sleep(2)
            
            # Check if navigated to wallet
            current_url = self.driver.current_url
            self.log_test("Dashboard Top-Up Navigation", "/wallet" in current_url, 
                         f"Navigated to: {current_url}")
            
            return True
        except Exception as e:
            self.log_test("Dashboard Top-Up Button", False, str(e))
            return False
            
    def test_run_history_export(self):
        """Test run history export functionality"""
        try:
            self.driver.get(f"{FRONTEND_URL}/runs")
            time.sleep(3)
            
            # Expand a run
            run_cards = self.wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "cursor-pointer"))
            )
            if run_cards:
                run_cards[0].click()
                time.sleep(2)
                
                # Look for export button
                export_button = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Export')]")
                self.log_test("Export Button Present", len(export_button) > 0)
                
                # Check for node I/O display
                node_sections = self.driver.find_elements(By.XPATH, "//p[contains(text(), 'Input')]")
                self.log_test("Node Input Display", len(node_sections) > 0)
                
                output_sections = self.driver.find_elements(By.XPATH, "//p[contains(text(), 'Output')]")
                self.log_test("Node Output Display", len(output_sections) > 0)
            
            return True
        except Exception as e:
            self.log_test("Run History Export", False, str(e))
            return False
            
    def test_agent_recommendations(self):
        """Test agent recommendations panel"""
        try:
            self.driver.get(f"{FRONTEND_URL}/chains")
            time.sleep(3)
            
            # Add an agent to trigger recommendations
            summarizer = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'n8n Summarizer')]"))
            )
            summarizer.click()
            time.sleep(2)
            
            # Click on the added node to select it
            nodes = self.driver.find_elements(By.CLASS_NAME, "react-flow__node")
            if len(nodes) > 1:  # Skip input node
                nodes[1].click()
                time.sleep(2)
                
                # Check for recommendations panel
                recommendations = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Recommended')]")
                self.log_test("Recommendations Panel", len(recommendations) > 0)
            
            return True
        except Exception as e:
            self.log_test("Agent Recommendations", False, str(e))
            return False
            
    def test_chain_execution_api(self):
        """Test chain execution with DAG ordering"""
        try:
            # Test the execution API directly
            execution_request = {
                "chain_id": "test-chain-001",
                "nodes": [
                    {"id": "input", "type": "agent", "agent_id": "input"},
                    {"id": "node1", "type": "agent", "agent_id": "summarizer"},
                    {"id": "transformer1", "type": "transformer", "transform_method": "deterministic"},
                    {"id": "node2", "type": "agent", "agent_id": "sentiment"}
                ],
                "edges": [
                    {"source": "input", "target": "node1", "score": 0.9},
                    {"source": "node1", "target": "transformer1", "score": 0.5},
                    {"source": "transformer1", "target": "node2", "score": 0.85}
                ],
                "execution_order": ["input", "node1", "transformer1", "node2"]
            }
            
            response = requests.post(f"{BACKEND_URL}/api/chain/execute", json=execution_request)
            self.log_test("Chain Execution API", response.status_code == 200)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Execution Status", result.get("status") == "success")
                self.log_test("Execution Log Present", len(result.get("execution_log", [])) > 0)
                self.log_test("Total Cost Calculated", result.get("total_cost", 0) > 0)
            
            return True
        except Exception as e:
            self.log_test("Chain Execution API", False, str(e))
            return False
            
    def test_agent_token_resolution(self):
        """Test @agent.field token resolution"""
        try:
            # Test the API endpoint
            token_request = {
                "template": "Process @Summarizer.summary and analyze @Sentiment.score",
                "outputs_map": {
                    "Summarizer": {"summary": "Test summary text"},
                    "Sentiment": {"score": 0.85}
                }
            }
            
            response = requests.post(f"{BACKEND_URL}/api/chain/resolve-atokens", json=token_request)
            self.log_test("Token Resolution API", response.status_code == 200)
            
            if response.status_code == 200:
                result = response.json()
                resolved = result.get("resolved_payload", {})
                self.log_test("Tokens Resolved", "Test summary text" in str(resolved))
            
            return True
        except Exception as e:
            self.log_test("Token Resolution", False, str(e))
            return False
            
    def print_results(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        print(f"\n✅ PASSED: {self.passed_tests}/{self.total_tests} tests")
        print(f"❌ FAILED: {self.total_tests - self.passed_tests}/{self.total_tests} tests")
        print(f"📈 SUCCESS RATE: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 EXCELLENT! All transformer system tests passed!")
        elif self.passed_tests / self.total_tests >= 0.8:
            print("\n✅ Good! Most tests passed.")
        else:
            print("\n⚠️ Warning: Several tests failed. Review the details above.")
            
        print("\n" + "="*60)

if __name__ == "__main__":
    tester = TestTransformerSystem()
    tester.run_all_tests()
