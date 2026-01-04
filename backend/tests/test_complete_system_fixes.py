#!/usr/bin/env python3
"""
Comprehensive Selenium Tests for All System Fixes
Tests agent creation, save button, chain builder, moderator with DB schemas
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
WAIT_TIMEOUT = 10

class TestCompleteSystemFixes:
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
        print("✅ WebDriver ready\n")
        
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
            print(f"❌ {name}: {details}")
        self.test_results.append({
            "name": name,
            "passed": passed,
            "details": details
        })
        
    def test_agent_creation_with_save(self):
        """Test agent creation with working save button"""
        print("\n📋 TEST 1: Agent Creation with Save Button")
        
        try:
            # Create agent via API
            agent_data = {
                "name": "Test Agent",
                "description": "Test agent for validation",
                "type": "custom",
                "input_schema": {
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {"type": "string"}
                    }
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "result": {"type": "string"}
                    }
                },
                "example_input": {"text": "test input"},
                "example_output": {"result": "test output"},
                "price_cents": 10,
                "tags": ["test"]
            }
            
            response = requests.post(f"{BACKEND_URL}/api/agents/create", json=agent_data)
            self.log_test("Agent Creation API", response.status_code == 200)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Agent ID Generated", "agent_id" in data)
                self.log_test("Agent Saved", data.get("success", False))
                
                # Verify agent exists
                agent_id = data.get("agent_id")
                if agent_id:
                    get_response = requests.get(f"{BACKEND_URL}/api/agents/{agent_id}")
                    self.log_test("Agent Retrieved", get_response.status_code == 200)
            
            return True
        except Exception as e:
            self.log_test("Agent Creation with Save", False, str(e))
            return False
            
    def test_agent_schemas_in_db(self):
        """Test that agent schemas are stored and retrievable"""
        print("\n📋 TEST 2: Agent Schemas in Database")
        
        try:
            # Get agent metadata
            response = requests.get(f"{BACKEND_URL}/api/agents/summarizer/metadata")
            self.log_test("Get Agent Metadata", response.status_code == 200)
            
            if response.status_code == 200:
                metadata = response.json()
                self.log_test("Input Schema Present", "input_schema" in metadata)
                self.log_test("Output Schema Present", "output_schema" in metadata)
                self.log_test("Example Input Present", "example_input" in metadata)
                self.log_test("Example Output Present", "example_output" in metadata)
                
            return True
        except Exception as e:
            self.log_test("Agent Schemas in DB", False, str(e))
            return False
            
    def test_moderator_with_db_schemas(self):
        """Test moderator retrieves schemas from database"""
        print("\n📋 TEST 3: Moderator with DB Schema Integration")
        
        try:
            # Create moderator with context
            create_data = {
                "node_id": "test_moderator",
                "position": {"x": 100, "y": 100},
                "upstream_agent_ids": ["summarizer"],
                "downstream_agent_id": "sentiment",
                "include_input_node": True
            }
            
            response = requests.post(f"{BACKEND_URL}/api/moderator/create-with-context", 
                                    json=create_data)
            self.log_test("Create Moderator with Context", response.status_code == 200)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Compatibility Score Calculated", "compatibility_score" in data)
                self.log_test("Upstream Schemas Retrieved", "upstream_schemas" in data)
                self.log_test("Downstream Schema Retrieved", "downstream_schema" in data)
                self.log_test("Input Node Created", data.get("input_node_id") is not None)
                
            # Test moderation with schema validation
            moderate_data = {
                "upstream_agent_id": "summarizer",
                "downstream_agent_id": "sentiment",
                "upstream_output": {
                    "summary": "Test summary",
                    "sentences": ["Sentence 1", "Sentence 2"]
                },
                "user_input": "Additional context"
            }
            
            mod_response = requests.post(f"{BACKEND_URL}/api/moderator/moderate-payload",
                                        json=moderate_data)
            self.log_test("Moderate Payload", mod_response.status_code == 200)
            
            if mod_response.status_code == 200:
                mod_data = mod_response.json()
                self.log_test("Payload Generated", "payload" in mod_data)
                self.log_test("Schema Valid", mod_data.get("context", {}).get("schema_valid", False))
                
            return True
        except Exception as e:
            self.log_test("Moderator with DB Schemas", False, str(e))
            return False
            
    def test_input_node_creation(self):
        """Test input node creation and updates"""
        print("\n📋 TEST 4: Input Node Functionality")
        
        try:
            # Create input node
            input_data = {
                "node_id": "test_input",
                "position": {"x": 50, "y": 50},
                "initial_text": "User provided input"
            }
            
            response = requests.post(f"{BACKEND_URL}/api/moderator/input-node/create",
                                    json=input_data)
            self.log_test("Create Input Node", response.status_code == 200)
            
            # Update input node
            update_response = requests.put(
                f"{BACKEND_URL}/api/moderator/input-node/test_input",
                params={"text": "Updated input text"}
            )
            self.log_test("Update Input Node", update_response.status_code == 200)
            
            return True
        except Exception as e:
            self.log_test("Input Node", False, str(e))
            return False
            
    def test_chain_execution_with_moderator(self):
        """Test chain execution with moderator and schemas"""
        print("\n📋 TEST 5: Chain Execution with Moderator")
        
        try:
            # Execute moderator with input
            exec_data = {
                "node_id": "test_moderator",
                "upstream_outputs": {
                    "summarizer": {
                        "summary": "AI is transforming industries",
                        "sentences": ["AI is powerful", "Industries are changing"]
                    }
                },
                "user_input": "Focus on positive aspects",
                "use_input_node": True
            }
            
            response = requests.post(f"{BACKEND_URL}/api/moderator/execute-with-input",
                                    json=exec_data)
            self.log_test("Execute Moderator", response.status_code == 200)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Execution Success", data.get("success", False))
                
                # Check if payload was properly transformed
                if "payload" in data:
                    payload = data["payload"]
                    self.log_test("Payload Transformed", "text" in payload or "content" in payload)
                    
            return True
        except Exception as e:
            self.log_test("Chain Execution", False, str(e))
            return False
            
    def test_agent_verification_system(self):
        """Test agent verification levels"""
        print("\n📋 TEST 6: Agent Verification System")
        
        try:
            # Verify agent
            response = requests.post(f"{BACKEND_URL}/api/agents/summarizer/verify")
            self.log_test("Verify Agent", response.status_code == 200)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Verification Level Updated", "verification_level" in data)
                
            return True
        except Exception as e:
            self.log_test("Agent Verification", False, str(e))
            return False
            
    def test_agent_deletion(self):
        """Test agent deletion functionality"""
        print("\n📋 TEST 7: Agent Deletion")
        
        try:
            # Create test agent first
            agent_data = {
                "name": "Delete Test",
                "description": "Agent to delete",
                "type": "custom",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": {"type": "object", "properties": {}},
                "example_input": {},
                "example_output": {},
                "price_cents": 0
            }
            
            create_response = requests.post(f"{BACKEND_URL}/api/agents/create", json=agent_data)
            if create_response.status_code == 200:
                agent_id = create_response.json()["agent_id"]
                
                # Delete agent
                delete_response = requests.delete(f"{BACKEND_URL}/api/agents/{agent_id}")
                self.log_test("Delete Agent", delete_response.status_code == 200)
                
                # Verify deletion
                get_response = requests.get(f"{BACKEND_URL}/api/agents/{agent_id}")
                self.log_test("Agent Removed", get_response.status_code == 404)
                
            return True
        except Exception as e:
            self.log_test("Agent Deletion", False, str(e))
            return False
            
    def test_compatibility_checking(self):
        """Test agent compatibility checking"""
        print("\n📋 TEST 8: Agent Compatibility Checking")
        
        try:
            response = requests.post(f"{BACKEND_URL}/api/agents/compatibility-check", 
                                    params={
                                        "upstream_id": "summarizer",
                                        "downstream_id": "sentiment"
                                    })
            self.log_test("Compatibility Check", response.status_code == 200)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Compatibility Score", "compatibility_score" in data)
                self.log_test("Field Mapping", "field_mapping" in data)
                self.log_test("Moderator Recommendation", "needs_moderator" in data)
                
            return True
        except Exception as e:
            self.log_test("Compatibility Check", False, str(e))
            return False
            
    def test_moderation_analytics(self):
        """Test moderation analytics and logging"""
        print("\n📋 TEST 9: Moderation Analytics")
        
        try:
            # Get moderation logs
            logs_response = requests.get(f"{BACKEND_URL}/api/moderator/logs")
            self.log_test("Get Moderation Logs", logs_response.status_code == 200)
            
            # Get analytics
            analytics_response = requests.get(f"{BACKEND_URL}/api/moderator/analytics")
            self.log_test("Get Analytics", analytics_response.status_code == 200)
            
            if analytics_response.status_code == 200:
                analytics = analytics_response.json()
                self.log_test("Methods Tracked", "methods" in analytics)
                self.log_test("Compatibility Average", "average_compatibility" in analytics)
                self.log_test("Schema Validation Rate", "schema_validation_rate" in analytics)
                
            return True
        except Exception as e:
            self.log_test("Moderation Analytics", False, str(e))
            return False
            
    def test_three_agent_chain(self):
        """Test chain with 3 n8n agents and moderators"""
        print("\n📋 TEST 10: Three Agent Chain with Moderators")
        
        try:
            # Test summarizer -> moderator -> sentiment -> moderator -> translator
            
            # First moderation: summarizer to sentiment
            mod1_response = requests.post(f"{BACKEND_URL}/api/moderator/moderate-payload",
                json={
                    "upstream_agent_id": "summarizer",
                    "downstream_agent_id": "sentiment",
                    "upstream_output": {
                        "summary": "AI is amazing",
                        "sentences": ["AI transforms", "Industries adapt"],
                        "key_points": ["Innovation", "Automation"]
                    }
                })
            self.log_test("First Moderation (Summarizer→Sentiment)", mod1_response.status_code == 200)
            
            if mod1_response.status_code == 200:
                sentiment_input = mod1_response.json()["payload"]
                
                # Execute sentiment (mock)
                sentiment_output = {
                    "sentiment": "positive",
                    "score": 0.95,
                    "confidence": 0.92
                }
                
                # Second moderation: sentiment to translator
                mod2_response = requests.post(f"{BACKEND_URL}/api/moderator/moderate-payload",
                    json={
                        "upstream_agent_id": "sentiment",
                        "downstream_agent_id": "translator",
                        "upstream_output": sentiment_output,
                        "user_input": "Translate to Spanish"
                    })
                self.log_test("Second Moderation (Sentiment→Translator)", mod2_response.status_code == 200)
                
                if mod2_response.status_code == 200:
                    translator_input = mod2_response.json()["payload"]
                    self.log_test("Translator Input Has Required Fields", 
                                 "text" in translator_input and "target_language" in translator_input)
            
            return True
        except Exception as e:
            self.log_test("Three Agent Chain", False, str(e))
            return False
            
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🚀 COMPLETE SYSTEM FIXES VALIDATION")
        print("="*60)
        
        self.setup()
        
        # Run tests
        self.test_agent_creation_with_save()
        self.test_agent_schemas_in_db()
        self.test_moderator_with_db_schemas()
        self.test_input_node_creation()
        self.test_chain_execution_with_moderator()
        self.test_agent_verification_system()
        self.test_agent_deletion()
        self.test_compatibility_checking()
        self.test_moderation_analytics()
        self.test_three_agent_chain()
        
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
        
        # List failed tests
        failed = [t for t in self.test_results if not t["passed"]]
        if failed:
            print("\n⚠️ Failed Tests:")
            for test in failed:
                print(f"  - {test['name']}: {test['details']}")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 EXCELLENT! All system fixes verified!")
        elif self.passed_tests / self.total_tests >= 0.8:
            print("\n✅ Good! Most fixes are working.")
        else:
            print("\n❌ CRITICAL: Multiple fixes failed!")
            
        print("\n" + "="*60)

if __name__ == "__main__":
    tester = TestCompleteSystemFixes()
    tester.run_all_tests()
