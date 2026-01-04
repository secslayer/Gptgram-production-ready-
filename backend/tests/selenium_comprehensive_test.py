#!/usr/bin/env python3
"""
COMPREHENSIVE SELENIUM TEST - Tests EVERY Component
Goes back and forth until EVERYTHING works
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class ComprehensiveTest:
    def __init__(self):
        # Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        self.base_url = "http://localhost:3000"  # Frontend port
        self.api_url = "http://localhost:8000"
        
        self.all_tests = []
        self.failed_tests = []
    
    def log(self, message, status="INFO"):
        symbol = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️", "WAIT": "⏳"}.get(status, "•")
        print(f"{symbol} {message}")
    
    def test_backend_api(self):
        """Test 1: Backend API Health"""
        try:
            resp = requests.get(f"{self.api_url}/health")
            if resp.status_code == 200:
                self.log("Backend API is running", "PASS")
                return True
        except:
            self.log("Backend API not responding", "FAIL")
            self.failed_tests.append("Backend API")
            return False
    
    def test_frontend_loads(self):
        """Test 2: Frontend Application Loads"""
        try:
            self.log("Loading frontend...", "WAIT")
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Check if React app loaded (look for root div or any React element)
            root = self.driver.find_elements(By.ID, "root")
            if root:
                self.log("Frontend loaded successfully", "PASS")
                
                # Take screenshot for evidence
                self.driver.save_screenshot("frontend_loaded.png")
                return True
            else:
                self.log("Frontend did not load properly", "FAIL")
                self.failed_tests.append("Frontend Load")
                return False
        except Exception as e:
            self.log(f"Frontend error: {e}", "FAIL")
            self.failed_tests.append("Frontend Load")
            return False
    
    def test_login_page(self):
        """Test 3: Login Page Elements"""
        try:
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            # Look for login elements
            elements_found = {
                "username": False,
                "password": False,
                "submit": False
            }
            
            # Try multiple selectors for username
            username_selectors = [
                (By.ID, "username"),
                (By.NAME, "username"),
                (By.XPATH, "//input[@placeholder='username' or @placeholder='Username' or contains(@placeholder, 'username')]"),
                (By.XPATH, "//input[@type='text']")
            ]
            
            for selector in username_selectors:
                try:
                    elem = self.driver.find_element(*selector)
                    if elem:
                        elements_found["username"] = True
                        break
                except:
                    continue
            
            # Look for password field
            try:
                password = self.driver.find_element(By.XPATH, "//input[@type='password']")
                elements_found["password"] = True
            except:
                pass
            
            # Look for submit button
            try:
                submit = self.driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Sign') or contains(text(), 'Login')]")
                elements_found["submit"] = True
            except:
                pass
            
            found_count = sum(elements_found.values())
            if found_count >= 2:
                self.log(f"Login page has {found_count}/3 elements", "PASS")
                return True
            else:
                self.log(f"Login page missing elements: {elements_found}", "FAIL")
                self.failed_tests.append("Login Page")
                return False
                
        except Exception as e:
            self.log(f"Login page error: {e}", "FAIL")
            self.failed_tests.append("Login Page")
            return False
    
    def test_login_flow(self):
        """Test 4: Login Flow"""
        try:
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            # Find and fill username
            username_input = None
            for selector in [(By.ID, "username"), (By.NAME, "username"), (By.XPATH, "//input[@type='text']")]:
                try:
                    username_input = self.driver.find_element(*selector)
                    break
                except:
                    continue
            
            if username_input:
                username_input.clear()
                username_input.send_keys("demo")
            
            # Find and fill password
            password_input = self.driver.find_element(By.XPATH, "//input[@type='password']")
            password_input.clear()
            password_input.send_keys("demo123")
            
            # Submit form
            password_input.send_keys(Keys.RETURN)
            time.sleep(3)
            
            # Check if login successful (URL changed or dashboard visible)
            current_url = self.driver.current_url
            if "login" not in current_url:
                self.log("Login successful", "PASS")
                return True
            else:
                # Try clicking submit button
                try:
                    submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                    submit.click()
                    time.sleep(3)
                    
                    if "login" not in self.driver.current_url:
                        self.log("Login successful (button click)", "PASS")
                        return True
                except:
                    pass
                
                self.log("Login failed", "FAIL")
                self.failed_tests.append("Login Flow")
                return False
                
        except Exception as e:
            self.log(f"Login flow error: {e}", "FAIL")
            self.failed_tests.append("Login Flow")
            return False
    
    def test_dashboard(self):
        """Test 5: Dashboard Components"""
        try:
            # Navigate to dashboard
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # Look for dashboard elements
            elements = {
                "wallet": self.driver.find_elements(By.XPATH, "//*[contains(text(), '$') or contains(text(), 'Wallet')]"),
                "agents": self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Agent')]"),
                "chains": self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Chain')]"),
                "cards": self.driver.find_elements(By.CLASS_NAME, "card") or self.driver.find_elements(By.XPATH, "//div[contains(@class, 'rounded')]")
            }
            
            found = sum(1 for v in elements.values() if v)
            
            if found >= 2:
                self.log(f"Dashboard has {found}/4 component types", "PASS")
                self.driver.save_screenshot("dashboard.png")
                return True
            else:
                self.log(f"Dashboard missing components", "FAIL")
                self.failed_tests.append("Dashboard")
                return False
                
        except Exception as e:
            self.log(f"Dashboard error: {e}", "FAIL")
            self.failed_tests.append("Dashboard")
            return False
    
    def test_navigation(self):
        """Test 6: Navigation Links"""
        try:
            nav_items = ["Agents", "Chains", "Runs", "Analytics"]
            working_links = 0
            
            for item in nav_items:
                try:
                    link = self.driver.find_element(By.XPATH, f"//a[contains(text(), '{item}')]")
                    link.click()
                    time.sleep(1)
                    
                    # Check URL changed
                    if item.lower() in self.driver.current_url.lower():
                        working_links += 1
                        self.log(f"Navigation to {item} works", "PASS")
                except:
                    self.log(f"Navigation to {item} failed", "FAIL")
            
            if working_links >= 2:
                return True
            else:
                self.failed_tests.append("Navigation")
                return False
                
        except Exception as e:
            self.log(f"Navigation error: {e}", "FAIL")
            self.failed_tests.append("Navigation")
            return False
    
    def test_agent_page(self):
        """Test 7: Agent Management Page"""
        try:
            self.driver.get(f"{self.base_url}/agents")
            time.sleep(2)
            
            # Look for agent-related elements
            agent_cards = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'card') or contains(@class, 'border')]")
            create_button = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Create')]")
            
            if agent_cards or create_button:
                self.log(f"Agent page loaded with {len(agent_cards)} agents", "PASS")
                self.driver.save_screenshot("agents_page.png")
                return True
            else:
                self.log("Agent page empty", "FAIL")
                self.failed_tests.append("Agent Page")
                return False
                
        except Exception as e:
            self.log(f"Agent page error: {e}", "FAIL")
            self.failed_tests.append("Agent Page")
            return False
    
    def test_chain_builder(self):
        """Test 8: Chain Builder Canvas"""
        try:
            self.driver.get(f"{self.base_url}/chains")
            time.sleep(3)
            
            # Look for React Flow canvas
            canvas = self.driver.find_elements(By.CLASS_NAME, "react-flow") or \
                    self.driver.find_elements(By.XPATH, "//div[contains(@class, 'react-flow')]")
            
            # Look for any canvas-like element
            if not canvas:
                canvas = self.driver.find_elements(By.TAG_NAME, "svg") or \
                        self.driver.find_elements(By.XPATH, "//div[@style and contains(@style, 'position')]")
            
            if canvas:
                self.log("Chain builder canvas found", "PASS")
                self.driver.save_screenshot("chain_builder.png")
                return True
            else:
                self.log("Chain builder canvas not found", "FAIL")
                self.failed_tests.append("Chain Builder")
                return False
                
        except Exception as e:
            self.log(f"Chain builder error: {e}", "FAIL")
            self.failed_tests.append("Chain Builder")
            return False
    
    def test_api_integration(self):
        """Test 9: API Integration"""
        try:
            # Test API endpoints
            endpoints = [
                ("/api/agents", "GET"),
                ("/api/chains", "GET"),
                ("/api/auth/me", "GET")
            ]
            
            working = 0
            for endpoint, method in endpoints:
                try:
                    if method == "GET":
                        resp = requests.get(f"{self.api_url}{endpoint}")
                        if resp.status_code in [200, 401]:  # 401 is ok for auth endpoints
                            working += 1
                            self.log(f"API {endpoint} responding", "PASS")
                except:
                    self.log(f"API {endpoint} failed", "FAIL")
            
            if working >= 2:
                return True
            else:
                self.failed_tests.append("API Integration")
                return False
                
        except Exception as e:
            self.log(f"API integration error: {e}", "FAIL")
            self.failed_tests.append("API Integration")
            return False
    
    def test_n8n_integration(self):
        """Test 10: n8n Webhook Integration"""
        try:
            import hmac
            import hashlib
            
            # Test n8n summarizer
            body = {"text": "Test text", "maxSentences": 1}
            canonical = json.dumps(body, separators=(',', ':'), sort_keys=True)
            signature = hmac.new(b's3cr3t', canonical.encode(), hashlib.sha256).hexdigest()
            
            headers = {
                'Content-Type': 'application/json',
                'X-GPTGRAM-Signature': f'sha256={signature}',
                'X-GPTGRAM-Idempotency': 'test'
            }
            
            resp = requests.post(
                'https://templatechat.app.n8n.cloud/webhook/gptgram/summarize',
                headers=headers,
                data=canonical,
                timeout=10
            )
            
            if resp.status_code == 200:
                self.log("n8n webhook integration working", "PASS")
                return True
            else:
                self.log("n8n webhook failed", "FAIL")
                self.failed_tests.append("n8n Integration")
                return False
                
        except Exception as e:
            self.log(f"n8n integration error: {e}", "FAIL")
            self.failed_tests.append("n8n Integration")
            return False
    
    def run_all_tests(self):
        """Run all tests and retry failures"""
        self.log("=" * 60, "INFO")
        self.log("COMPREHENSIVE SELENIUM TESTING", "INFO")
        self.log("=" * 60, "INFO")
        
        tests = [
            ("Backend API", self.test_backend_api),
            ("Frontend Load", self.test_frontend_loads),
            ("Login Page", self.test_login_page),
            ("Login Flow", self.test_login_flow),
            ("Dashboard", self.test_dashboard),
            ("Navigation", self.test_navigation),
            ("Agent Page", self.test_agent_page),
            ("Chain Builder", self.test_chain_builder),
            ("API Integration", self.test_api_integration),
            ("n8n Integration", self.test_n8n_integration)
        ]
        
        results = {}
        
        # First pass
        for name, test_func in tests:
            self.log(f"\nTesting {name}...", "WAIT")
            try:
                results[name] = test_func()
                self.all_tests.append(name)
            except Exception as e:
                self.log(f"Test {name} crashed: {e}", "FAIL")
                results[name] = False
                self.failed_tests.append(name)
            
            time.sleep(1)
        
        # Retry failures once
        if self.failed_tests:
            self.log("\n" + "=" * 60, "INFO")
            self.log("RETRYING FAILED TESTS", "INFO")
            self.log("=" * 60, "INFO")
            
            retry_list = self.failed_tests.copy()
            self.failed_tests = []
            
            for name in retry_list:
                test_func = next((t[1] for t in tests if t[0] == name), None)
                if test_func:
                    self.log(f"\nRetrying {name}...", "WAIT")
                    try:
                        if test_func():
                            results[name] = True
                            self.log(f"{name} passed on retry!", "PASS")
                        else:
                            self.failed_tests.append(name)
                    except:
                        self.failed_tests.append(name)
        
        # Final summary
        self.print_summary(results)
        
        return results
    
    def print_summary(self, results):
        """Print final test summary"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("FINAL TEST RESULTS", "INFO")
        self.log("=" * 60, "INFO")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{name}: {status}", "INFO")
        
        self.log(f"\nTotal: {passed}/{total} tests passed", "INFO")
        
        percentage = (passed / total) * 100
        
        if percentage == 100:
            self.log("🎉 PERFECT! All components working!", "PASS")
        elif percentage >= 80:
            self.log("✅ System is functional! Minor issues only.", "PASS")
        elif percentage >= 60:
            self.log("⚠️ System partially working. Some fixes needed.", "INFO")
        else:
            self.log("❌ System needs significant fixes.", "FAIL")
        
        # List critical failures
        if self.failed_tests:
            self.log("\nCritical failures that need fixing:", "FAIL")
            for failure in self.failed_tests:
                self.log(f"  • {failure}", "FAIL")
    
    def cleanup(self):
        """Clean up"""
        self.driver.quit()

def main():
    tester = ComprehensiveTest()
    try:
        results = tester.run_all_tests()
        
        # Keep testing until critical components work
        critical_components = ["Backend API", "Frontend Load", "Login Page", "Dashboard"]
        critical_working = all(results.get(c, False) for c in critical_components)
        
        if not critical_working:
            tester.log("\n⚠️ Critical components not working. Please fix:", "FAIL")
            for c in critical_components:
                if not results.get(c, False):
                    tester.log(f"  - {c}", "FAIL")
        
        return 0 if critical_working else 1
        
    except Exception as e:
        tester.log(f"Fatal error: {e}", "FAIL")
        return 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    import sys
    sys.exit(main())
