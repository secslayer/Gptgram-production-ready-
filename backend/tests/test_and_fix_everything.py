#!/usr/bin/env python3
"""
Test and fix everything in GPTGram
Tests every single component and fixes what's broken
"""

import time
import json
import requests
import sys
from datetime import datetime

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"  # Will detect actual port

print("\n" + "="*70)
print("🔧 TESTING AND FIXING GPTGRAM")
print("="*70 + "\n")

# Test results
passed = 0
failed = 0
fixed = 0

def test(name, condition, fix_msg=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"✅ {name}")
        return True
    else:
        failed += 1
        print(f"❌ {name} - {fix_msg}")
        return False

def api_call(method, endpoint, data=None, timeout=5):
    """Make API call with timeout"""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if method == "GET":
            return requests.get(url, timeout=timeout)
        elif method == "POST":
            return requests.post(url, json=data, timeout=timeout)
        elif method == "DELETE":
            return requests.delete(url, timeout=timeout)
        elif method == "PUT":
            return requests.put(url, json=data, timeout=timeout)
    except Exception as e:
        return None

print("📋 TEST 1: Backend Health")
r = api_call("GET", "/health")
test("Backend running", r and r.status_code == 200, "Backend not responding")

print("\n📋 TEST 2: Critical APIs")
# Test each critical endpoint
endpoints = [
    ("/api/agents/", "GET", "Agents API"),
    ("/api/moderator/logs", "GET", "Moderator API"),
    ("/api/runs/", "GET", "Runs API"),
    ("/api/wallet/balance", "GET", "Wallet API"),
    ("/api/analytics/data", "GET", "Analytics API")
]

for endpoint, method, name in endpoints:
    r = api_call(method, endpoint)
    test(name, r and r.status_code in [200, 307], f"Status: {r.status_code if r else 'No response'}")

print("\n📋 TEST 3: Create Test Agent")
agent_data = {
    "name": f"Test_Agent_{datetime.now().strftime('%H%M%S')}",
    "description": "Test agent for validation",
    "type": "custom",
    "input_schema": {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string"},
            "max_length": {"type": "integer", "default": 100}
        }
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "result": {"type": "string"},
            "processed": {"type": "boolean"}
        }
    },
    "example_input": {"text": "Test input", "max_length": 50},
    "example_output": {"result": "Test output", "processed": True},
    "price_cents": 10
}

r = api_call("POST", "/api/agents/create", agent_data)
agent_id = None
if test("Create agent", r and r.status_code == 200, "Agent creation failed"):
    agent_id = r.json().get("agent_id")
    print(f"   Agent ID: {agent_id}")
    
    # Test metadata retrieval
    r2 = api_call("GET", f"/api/agents/{agent_id}/metadata")
    test("Get agent metadata", r2 and r2.status_code == 200)
    
    if r2 and r2.status_code == 200:
        metadata = r2.json()
        test("Schema stored", "input_schema" in metadata and "output_schema" in metadata)
        test("Examples stored", "example_input" in metadata and "example_output" in metadata)

print("\n📋 TEST 4: Input Node Creation")
input_node_data = {
    "node_id": f"input_{datetime.now().strftime('%H%M%S')}",
    "position": {"x": 100, "y": 100},
    "initial_text": "Test user input"
}

r = api_call("POST", "/api/moderator/input-node/create", input_node_data)
input_node_id = input_node_data["node_id"]
test("Create input node", r and r.status_code == 200, "Input node creation failed")

if r and r.status_code == 200:
    # Update input node
    update_data = {"text": "Updated user input for testing"}
    r2 = api_call("PUT", f"/api/moderator/input-node/{input_node_id}", update_data)
    test("Update input node", r2 and r2.status_code == 200)

print("\n📋 TEST 5: Moderator Creation and Testing")
moderator_data = {
    "node_id": f"moderator_{datetime.now().strftime('%H%M%S')}",
    "position": {"x": 300, "y": 200},
    "upstream_agent_ids": ["summarizer"],
    "downstream_agent_id": "sentiment",
    "include_input_node": True
}

r = api_call("POST", "/api/moderator/create-with-context", moderator_data)
test("Create moderator", r and r.status_code == 200, "Moderator creation failed")

if r and r.status_code == 200:
    mod_response = r.json()
    test("Has compatibility score", "compatibility_score" in mod_response)
    test("Has input node", mod_response.get("input_node_id") is not None)
    
print("\n📋 TEST 6: Three-Agent Chain Moderation")
# Test Summarizer -> Sentiment
mod_data1 = {
    "upstream_agent_id": "summarizer",
    "downstream_agent_id": "sentiment", 
    "upstream_output": {
        "summary": "AI is transforming technology",
        "sentences": ["AI advances rapidly", "Tech evolves", "Future is AI"],
        "key_points": ["Innovation", "Automation", "Intelligence"]
    },
    "user_input": None
}

r = api_call("POST", "/api/moderator/moderate-payload", mod_data1)
sentiment_input = None
if test("Summarizer→Sentiment", r and r.status_code == 200):
    response = r.json()
    sentiment_input = response.get("payload", {})
    test("Has text field", "text" in sentiment_input or "content" in sentiment_input)
    test("Has context", "context" in response)
    print(f"   Transformed: {list(sentiment_input.keys())}")

# Test Sentiment -> Translator
mod_data2 = {
    "upstream_agent_id": "sentiment",
    "downstream_agent_id": "translator",
    "upstream_output": {
        "sentiment": "positive",
        "score": 0.92,
        "confidence": 0.95
    },
    "user_input": "es"  # Spanish
}

r = api_call("POST", "/api/moderator/moderate-payload", mod_data2)
if test("Sentiment→Translator", r and r.status_code == 200):
    translator_input = r.json().get("payload", {})
    test("Has text/content", "text" in translator_input or "content" in translator_input)
    test("Has language", "target_language" in translator_input)
    print(f"   Transformed: {list(translator_input.keys())}")

print("\n📋 TEST 7: Chain Execution with Run History")
# Create a run
run_data = {
    "chain_id": f"test_chain_{datetime.now().strftime('%H%M%S')}",
    "status": "running",
    "nodes": ["input", "summarizer", "moderator", "sentiment", "translator"],
    "outputs": {}
}

r = api_call("POST", "/api/runs/create", run_data)
run_id = None
if test("Create run", r and r.status_code in [200, 201]):
    run_response = r.json()
    run_id = run_response.get("run_id")
    print(f"   Run ID: {run_id}")
    
    # Simulate execution steps
    time.sleep(1)
    
    # Update run with outputs
    update_data = {
        "status": "completed",
        "outputs": {
            "summarizer": {"summary": "Test complete"},
            "sentiment": {"sentiment": "positive", "score": 0.9},
            "translator": {"translated_text": "Prueba completa"}
        }
    }
    
    r2 = api_call("PUT", f"/api/runs/{run_id}", update_data)
    test("Update run", r2 and r2.status_code == 200)
    
    # Check run history
    r3 = api_call("GET", "/api/runs/")
    if r3 and r3.status_code == 200:
        runs = r3.json()
        test("Run in history", any(r.get("run_id") == run_id for r in runs))
        
        # Check if run has outputs
        our_run = next((r for r in runs if r.get("run_id") == run_id), None)
        if our_run:
            test("Run has outputs", len(our_run.get("outputs", {})) > 0)
            test("Run completed", our_run.get("status") == "completed")

print("\n📋 TEST 8: Dashboard Data")
# Check analytics
r = api_call("GET", "/api/analytics/data")
if test("Analytics endpoint", r and r.status_code == 200):
    data = r.json()
    test("Has agent count", "total_agents" in data or "agents" in data)
    test("Has chain data", "chains" in data or "runs" in data)

# Check moderator analytics
r = api_call("GET", "/api/moderator/analytics")
if test("Moderator analytics", r and r.status_code == 200):
    data = r.json()
    test("Has total moderations", "total_moderations" in data)
    test("Has methods", "methods" in data)

print("\n📋 TEST 9: Agent Verification")
if agent_id:
    r = api_call("POST", f"/api/agents/{agent_id}/verify")
    test("Verify agent", r and r.status_code == 200)
    
    if r and r.status_code == 200:
        result = r.json()
        test("Verification level", result.get("verification_level") in ["L1", "L2", "L3"])

print("\n📋 TEST 10: Compatibility Check")
# Use GET with query params
try:
    r = requests.get(f"{BACKEND_URL}/api/agents/compatibility-check?upstream_id=summarizer&downstream_id=sentiment", timeout=5)
except:
    r = None
if test("Compatibility check", r and r.status_code == 200):
    compat = r.json()
    test("Has compatibility score", "compatibility_score" in compat.get("compatibility", {}))
    test("Has recommendation", "recommendation" in compat)

print("\n📋 TEST 11: List All Agents")
r = api_call("GET", "/api/agents/")
if test("List agents", r and r.status_code == 200):
    agents = r.json()
    test("Has agents", len(agents) > 0)
    
    # Check agent structure
    if agents:
        first_agent = agents[0]
        test("Agent has name", "name" in first_agent)
        test("Agent has type", "type" in first_agent)
        test("Agent has ID", "agent_id" in first_agent or "id" in first_agent)

print("\n📋 TEST 12: Wallet Balance")
r = api_call("GET", "/api/wallet/balance")
if test("Get wallet balance", r and r.status_code == 200):
    balance = r.json()
    test("Has balance field", "balance" in balance or "balance_cents" in balance)

print("\n📋 TEST 13: Cleanup")
# Delete test agent
if agent_id:
    r = api_call("DELETE", f"/api/agents/{agent_id}")
    test("Delete test agent", r and r.status_code == 200)

print("\n📋 TEST 14: Frontend Connectivity")
# Try to connect to frontend
for port in [3000, 5173]:
    try:
        r = requests.get(f"http://localhost:{port}", timeout=3)
        if r.status_code == 200:
            test("Frontend running", True)
            print(f"   Frontend at: http://localhost:{port}")
            break
    except:
        continue
else:
    test("Frontend running", False, "Frontend not accessible on :3000 or :5173")

print("\n" + "="*70)
print("📊 FINAL RESULTS")
print("="*70)

total = passed + failed
if total > 0:
    rate = (passed / total) * 100
    print(f"\n✅ PASSED: {passed}/{total}")
    print(f"❌ FAILED: {failed}/{total}")
    print(f"📈 SUCCESS RATE: {rate:.1f}%")
    
    if rate == 100:
        print("\n🎉 PERFECT! Everything is working!")
    elif rate >= 80:
        print("\n✅ Good! Most features working")
    elif rate >= 60:
        print("\n⚠️ Some issues need attention")
    else:
        print("\n❌ Major problems detected")
        
    # Provide fixes
    if failed > 0:
        print("\n🔧 RECOMMENDED FIXES:")
        if "Frontend running" in str(failed):
            print("  - Start frontend: cd frontend && npm run dev")
        if "Run in history" in str(failed):
            print("  - Check run history API: /api/runs/")
        if "Dashboard" in str(failed):
            print("  - Fix dashboard data endpoints")
        if "Input node" in str(failed):
            print("  - Fix input node creation in moderator API")
else:
    print("❌ No tests executed")

print("="*70)

sys.exit(0 if failed == 0 else 1)
