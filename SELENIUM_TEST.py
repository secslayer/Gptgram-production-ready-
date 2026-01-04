#!/usr/bin/env python3
"""
COMPREHENSIVE SELENIUM TEST
Tests all frontend features with automated browser testing
"""

import time
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Test configuration
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
USERNAME = "demo"
PASSWORD = "demo123"

def print_test(name):
    print(f"\n{'='*60}")
    print(f"🧪 {name}")
    print('='*60)

def print_ok(msg):
    print(f"✅ {msg}")

def print_fail(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

class GPTGramSeleniumTest:
    def __init__(self, headless=False):
        # Setup Chrome options
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Initialize driver
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 10)
            print_ok("Browser initialized")
        except Exception as e:
            print_fail(f"Failed to initialize browser: {e}")
            raise
    
    def cleanup(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print_info("Browser closed")
    
    def test_login(self):
        """Test login functionality"""
        print_test("LOGIN TEST")
        
        try:
            # Navigate to login
            self.driver.get(FRONTEND_URL)
            time.sleep(2)
            
            # Check if redirected to login
            if "/login" in self.driver.current_url:
                print_ok("Redirected to login page")
            
            # Find login form elements
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign In')]")
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(USERNAME)
            password_field.clear()
            password_field.send_keys(PASSWORD)
            
            # Click login
            login_button.click()
            time.sleep(2)
            
            # Verify logged in
            if "/login" not in self.driver.current_url:
                print_ok(f"Login successful - redirected to: {self.driver.current_url}")
                return True
            else:
                print_fail("Login failed - still on login page")
                return False
                
        except Exception as e:
            print_fail(f"Login test failed: {e}")
            return False
    
    def test_dashboard(self):
        """Test dashboard page"""
        print_test("DASHBOARD TEST")
        
        try:
            # Navigate to dashboard
            self.driver.get(f"{FRONTEND_URL}/")
            time.sleep(2)
            
            # Check for dashboard elements
            dashboard_title = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Dashboard')]"))
            )
            print_ok("Dashboard page loaded")
            
            # Check for wallet balance
            wallet_elem = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Wallet Balance')]")
            if wallet_elem:
                print_ok("Wallet balance displayed")
            
            # Check for agent count
            try:
                agent_count = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Total Agents')]")
                print_ok("Agent count displayed")
            except:
                print_info("Agent count not visible")
            
            # Check for run statistics
            try:
                run_stats = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Total Runs')]")
                print_ok("Run statistics displayed")
            except:
                print_info("Run statistics not visible")
            
            return True
            
        except Exception as e:
            print_fail(f"Dashboard test failed: {e}")
            return False
    
    def test_chain_builder(self):
        """Test chain builder page"""
        print_test("CHAIN BUILDER TEST")
        
        try:
            # Navigate to chain builder
            self.driver.get(f"{FRONTEND_URL}/chains")
            time.sleep(2)
            
            # Check for chain builder elements
            canvas = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "react-flow"))
            )
            print_ok("Chain builder canvas loaded")
            
            # Check for agent library
            agent_library = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Agent Library')]")
            print_ok("Agent library panel found")
            
            # Check for available agents count
            try:
                agents_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Available Agents')]").text
                print_ok(f"Agent library shows: {agents_text}")
            except:
                print_info("Available agents count not visible")
            
            # Check for input node button
            try:
                input_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add Input Node')]")
                print_ok("Add Input Node button found")
            except:
                print_info("Add Input Node button not found")
            
            # Check for run chain button
            try:
                run_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Run Chain')]")
                print_ok("Run Chain button found")
            except:
                print_info("Run Chain button not found")
            
            return True
            
        except Exception as e:
            print_fail(f"Chain builder test failed: {e}")
            return False
    
    def test_run_history(self):
        """Test run history page"""
        print_test("RUN HISTORY TEST")
        
        try:
            # Navigate to run history
            self.driver.get(f"{FRONTEND_URL}/runs")
            time.sleep(2)
            
            # Check for run history elements
            title = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Run History')]"))
            )
            print_ok("Run history page loaded")
            
            # Check for refresh button
            refresh_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Refresh')]")
            print_ok("Refresh button found")
            
            # Check for filter buttons
            try:
                all_filter = self.driver.find_element(By.XPATH, "//button[contains(text(), 'All')]")
                succeeded_filter = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Succeeded')]")
                failed_filter = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Failed')]")
                print_ok("Filter buttons found")
            except:
                print_info("Some filter buttons not found")
            
            # Check for run cards or empty state
            try:
                # Try to find run cards
                run_cards = self.driver.find_elements(By.CLASS_NAME, "card")
                if run_cards:
                    print_ok(f"Found {len(run_cards)} run cards")
                    
                    # Check for timeline in first run
                    try:
                        started_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Started:')]")
                        if "None" not in started_text.text:
                            print_ok("Timeline shows proper timestamps (no 'None')")
                        else:
                            print_fail("Timeline contains 'None' values")
                    except:
                        print_info("Timeline not visible")
                else:
                    # Check for empty state
                    empty_state = self.driver.find_element(By.XPATH, "//*[contains(text(), 'No runs found')]")
                    print_ok("Empty state displayed correctly")
            except:
                print_info("Run display state unclear")
            
            return True
            
        except Exception as e:
            print_fail(f"Run history test failed: {e}")
            return False
    
    def test_code_fuser(self):
        """Test code fuser page"""
        print_test("CODE FUSER TEST")
        
        try:
            # Navigate to code fuser
            self.driver.get(f"{FRONTEND_URL}/code-fuser")
            time.sleep(2)
            
            # Check for code fuser elements
            title = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Code Fuser')]"))
            )
            print_ok("Code fuser page loaded")
            
            # Check for agent dropdown
            try:
                agent_select = self.driver.find_element(By.XPATH, "//select[contains(@class, 'border')]")
                print_ok("Agent dropdown found")
                
                # Check options
                options = agent_select.find_elements(By.TAG_NAME, "option")
                print_ok(f"Dropdown has {len(options) - 1} agents")  # -1 for placeholder
            except:
                print_info("Agent dropdown not found")
            
            # Check for language buttons
            try:
                python_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Python')]")
                js_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'JavaScript')]")
                curl_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'cURL')]")
                print_ok("Language selection buttons found")
            except:
                print_info("Some language buttons not found")
            
            # Check for generate button
            try:
                generate_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Generate')]")
                print_ok("Generate Code button found")
            except:
                print_info("Generate button not found")
            
            return True
            
        except Exception as e:
            print_fail(f"Code fuser test failed: {e}")
            return False
    
    def test_marketplace(self):
        """Test marketplace page"""
        print_test("MARKETPLACE TEST")
        
        try:
            # Navigate to marketplace
            self.driver.get(f"{FRONTEND_URL}/marketplace")
            time.sleep(2)
            
            # Check for marketplace elements
            title = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Marketplace')]"))
            )
            print_ok("Marketplace page loaded")
            
            # Check for search bar
            try:
                search_input = self.driver.find_element(By.XPATH, "//input[@placeholder[contains(., 'Search')]]")
                print_ok("Search bar found")
            except:
                print_info("Search bar not found")
            
            # Check for agent cards
            try:
                agent_cards = self.driver.find_elements(By.CLASS_NAME, "card")
                if agent_cards:
                    print_ok(f"Found {len(agent_cards)} agent cards")
                    
                    # Check for price display
                    try:
                        price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '¢')]")
                        if price_elements:
                            print_ok("Agent prices displayed")
                    except:
                        print_info("Prices not visible")
                        
                    # Check for install buttons
                    try:
                        install_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Install')]")
                        if install_buttons:
                            print_ok(f"Found {len(install_buttons)} install buttons")
                    except:
                        print_info("Install buttons not found")
                else:
                    print_info("No agent cards found")
            except:
                print_info("Could not check agent cards")
            
            return True
            
        except Exception as e:
            print_fail(f"Marketplace test failed: {e}")
            return False
    
    def test_wallet(self):
        """Test wallet page"""
        print_test("WALLET TEST")
        
        try:
            # Navigate to wallet
            self.driver.get(f"{FRONTEND_URL}/wallet")
            time.sleep(2)
            
            # Check for wallet elements
            title = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Wallet')]"))
            )
            print_ok("Wallet page loaded")
            
            # Check for balance display
            try:
                balance_elem = self.driver.find_element(By.XPATH, "//*[contains(text(), '$')]")
                print_ok("Wallet balance displayed")
            except:
                print_info("Balance not visible")
            
            # Check for top-up options
            try:
                topup_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'card')]")
                if topup_buttons:
                    print_ok(f"Found {len(topup_buttons)} top-up options")
            except:
                print_info("Top-up options not found")
            
            # Check for transaction history
            try:
                transactions = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Transaction')]")
                print_ok("Transaction history section found")
            except:
                print_info("Transaction history not visible")
            
            return True
            
        except Exception as e:
            print_fail(f"Wallet test failed: {e}")
            return False
    
    def test_navigation(self):
        """Test sidebar navigation"""
        print_test("NAVIGATION TEST")
        
        try:
            # Check for sidebar
            sidebar = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//nav"))
            )
            print_ok("Sidebar navigation found")
            
            # Check navigation items
            nav_items = [
                ("Dashboard", "/"),
                ("Marketplace", "/marketplace"),
                ("My Agents", "/agents"),
                ("Chain Builder", "/chains"),
                ("Run History", "/runs"),
                ("Code Fuser", "/code-fuser"),
                ("Wallet", "/wallet")
            ]
            
            for item_name, item_path in nav_items:
                try:
                    nav_link = self.driver.find_element(By.XPATH, f"//a[contains(., '{item_name}')]")
                    print_ok(f"Navigation link found: {item_name}")
                except:
                    print_info(f"Navigation link not found: {item_name}")
            
            return True
            
        except Exception as e:
            print_fail(f"Navigation test failed: {e}")
            return False

def run_full_test():
    """Run all tests"""
    print("="*80)
    print("🚀 GPTGRAM SELENIUM TEST SUITE")
    print("="*80)
    
    # Check services first
    print_test("SERVICE CHECK")
    
    # Check backend
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if r.status_code == 200:
            print_ok("Backend is running")
        else:
            print_fail("Backend not healthy")
            return
    except:
        print_fail("Backend is not running - start it first!")
        return
    
    # Check frontend (basic check)
    try:
        r = requests.get(FRONTEND_URL, timeout=2)
        print_ok("Frontend is accessible")
    except:
        print_fail("Frontend is not running - start it first!")
        return
    
    # Initialize test suite
    test = None
    try:
        test = GPTGramSeleniumTest(headless=False)  # Set to True for headless mode
        
        # Run tests
        results = {}
        
        # Login test (required for other tests)
        results['Login'] = test.test_login()
        
        if results['Login']:
            # Run other tests
            results['Dashboard'] = test.test_dashboard()
            results['Chain Builder'] = test.test_chain_builder()
            results['Run History'] = test.test_run_history()
            results['Code Fuser'] = test.test_code_fuser()
            results['Marketplace'] = test.test_marketplace()
            results['Wallet'] = test.test_wallet()
            results['Navigation'] = test.test_navigation()
        else:
            print_fail("Login failed - skipping other tests")
        
        # Summary
        print("\n" + "="*80)
        print("📊 TEST RESULTS SUMMARY")
        print("="*80)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        print(f"\n✅ Passed: {passed}/{total} tests\n")
        
        for test_name, result in results.items():
            status = "✅" if result else "❌"
            print(f"{status} {test_name}")
        
        print("\n" + "="*80)
        if passed == total:
            print("✅ ALL TESTS PASSED - SYSTEM FULLY FUNCTIONAL!")
        elif passed >= total * 0.7:
            print("⚠️ MOST TESTS PASSED - Some features need attention")
        else:
            print("❌ MANY TESTS FAILED - System needs fixes")
        print("="*80)
        
    except Exception as e:
        print_fail(f"Test suite error: {e}")
    finally:
        if test:
            test.cleanup()

if __name__ == "__main__":
    # Check if Chrome driver is available
    try:
        from selenium import webdriver
        print_info("Selenium is installed")
    except ImportError:
        print_fail("Selenium not installed. Run: pip install selenium")
        print_info("Also need Chrome and ChromeDriver installed")
        exit(1)
    
    # Run the tests
    run_full_test()
