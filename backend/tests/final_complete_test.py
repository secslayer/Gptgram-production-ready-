#!/usr/bin/env python3
"""
FINAL COMPLETE TEST - NO HANGS, ALL WORKING
Tests everything without timeouts
"""

import requests
import json
import sys
import time

BACKEND_URL = "http://localhost:8000"
TESTS_PASSED = 0
TESTS_FAILED = 0

def test(name, condition, details=""):
    """Log test result"""
    global TESTS_PASSED, TESTS_FAILED
    if condition:
        TESTS_PASSED += 1
        print(f"✅ {name}")
        return True
    else:
        TESTS_FAILED += 1
        print(f"❌ {name}: {details}")
        return False

def safe_request(method, url, **kwargs):
    """Make request with short timeout"""
    kwargs['timeout'] = 2  # 2 second timeout
    try:
        return getattr(requests, method)(url, **kwargs)
    except Exception as e:
        return None

print("\n" + "="*60)
print("🚀 FINAL COMPLETE SYSTEM TEST")
print("="*60 + "\n")

# Test 1: Health Check
print("📋 TEST 1: Backend Health")
r = safe_request('get', f"{BACKEND_URL}/health")
test("Health Check", r and r.status_code == 200)

# Test 2: Agent APIs
print("\n📋 TEST 2: Agent System")
# Create agent
agent_data = {
    "name": "Test Agent",
    "description": "Test",
    "type": "custom",
    "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}},
    "output_schema": {"type": "object", "properties": {"result": {"type": "string"}}},
    "example_input": {"text": "test"},
    "example_output": {"result": "output"},
    "price_cents": 10
}

r = safe_request('post', f"{BACKEND_URL}/api/agents/create", json=agent_data)
agent_created = test("Create Agent", r and r.status_code == 200)

if agent_created and r:
    agent_id = r.json().get("agent_id")
    
    # Get metadata
    r2 = safe_request('get', f"{BACKEND_URL}/api/agents/{agent_id}/metadata")
    test("Get Metadata", r2 and r2.status_code == 200)
    
    # Verify agent
    r3 = safe_request('post', f"{BACKEND_URL}/api/agents/{agent_id}/verify")
    test("Verify Agent", r3 and r3.status_code == 200)
    
    # Delete agent
    r4 = safe_request('delete', f"{BACKEND_URL}/api/agents/{agent_id}")
    test("Delete Agent", r4 and r4.status_code == 200)

# Test 3: Input Node
print("\n📋 TEST 3: Input Node")
r = safe_request('post', f"{BACKEND_URL}/api/moderator/input-node/create",
                json={"node_id": "test_input", "position": {"x": 100, "y": 100}})
test("Create Input Node", r and r.status_code == 200)

r2 = safe_request('put', f"{BACKEND_URL}/api/moderator/input-node/test_input",
                 json={"text": "Updated"})
test("Update Input Node", r2 and r2.status_code == 200)

# Test 4: Moderator with Context
print("\n📋 TEST 4: Moderator System")
r = safe_request('post', f"{BACKEND_URL}/api/moderator/create-with-context",
                json={
                    "node_id": "test_mod",
                    "position": {"x": 200, "y": 200},
                    "upstream_agent_ids": ["summarizer"],
                    "downstream_agent_id": "sentiment",
                    "include_input_node": True
                })
test("Create Moderator", r and r.status_code == 200)

if r and r.status_code == 200:
    data = r.json()
    test("Has Compatibility Score", "compatibility_score" in data)
    test("Has Input Node ID", data.get("input_node_id") is not None)

# Test 5: Moderate Payload
print("\n📋 TEST 5: Payload Moderation")
r = safe_request('post', f"{BACKEND_URL}/api/moderator/moderate-payload",
                json={
                    "upstream_agent_id": "summarizer",
                    "downstream_agent_id": "sentiment",
                    "upstream_output": {"summary": "Test", "sentences": ["S1"]},
                    "user_input": "positive"
                })
test("Moderate Payload", r and r.status_code == 200)

if r and r.status_code == 200:
    data = r.json()
    test("Has Payload", "payload" in data)
    test("Has Context", "context" in data)

# Test 6: Three Agent Chain
print("\n📋 TEST 6: Three Agent Chain")
# Summarizer to Sentiment
r1 = safe_request('post', f"{BACKEND_URL}/api/moderator/moderate-payload",
                 json={
                     "upstream_agent_id": "summarizer",
                     "downstream_agent_id": "sentiment",
                     "upstream_output": {"summary": "AI is amazing", "sentences": ["S1", "S2"]}
                 })
test("Summarizer→Sentiment", r1 and r1.status_code == 200)

if r1 and r1.status_code == 200:
    sentiment_input = r1.json().get("payload", {})
    
    # Sentiment to Translator
    r2 = safe_request('post', f"{BACKEND_URL}/api/moderator/moderate-payload",
                     json={
                         "upstream_agent_id": "sentiment",
                         "downstream_agent_id": "translator",
                         "upstream_output": {"sentiment": "positive", "score": 0.9},
                         "user_input": "es"
                     })
    test("Sentiment→Translator", r2 and r2.status_code == 200)
    
    if r2 and r2.status_code == 200:
        translator_input = r2.json().get("payload", {})
        test("Has Text Field", "text" in translator_input or "content" in translator_input)
        test("Has Language", "target_language" in translator_input)

# Test 7: Compatibility Check
print("\n📋 TEST 7: Compatibility")
r = safe_request('post', f"{BACKEND_URL}/api/agents/compatibility-check",
                params={"upstream_id": "summarizer", "downstream_id": "sentiment"})
test("Compatibility Check", r and r.status_code == 200)

# Test 8: Run History
print("\n📋 TEST 8: Run History")
r = safe_request('post', f"{BACKEND_URL}/api/runs/create",
                json={
                    "chain_id": "test_chain",
                    "status": "running",
                    "nodes": ["node1", "node2"]
                })
test("Create Run", r and r.status_code in [200, 201])

r2 = safe_request('get', f"{BACKEND_URL}/api/runs")
test("Get Run History", r2 and r2.status_code == 200)

# Test 9: Wallet
print("\n📋 TEST 9: Wallet")
r = safe_request('get', f"{BACKEND_URL}/api/wallet/balance")
test("Get Balance", r and r.status_code == 200)

# Test 10: Analytics
print("\n📋 TEST 10: Analytics")
r1 = safe_request('get', f"{BACKEND_URL}/api/moderator/analytics")
test("Moderator Analytics", r1 and r1.status_code == 200)

r2 = safe_request('get', f"{BACKEND_URL}/api/moderator/logs")
test("Moderator Logs", r2 and r2.status_code == 200)

r3 = safe_request('get', f"{BACKEND_URL}/api/analytics/data")
test("General Analytics", r3 and r3.status_code == 200)

# Test 11: Prompt Agent
print("\n📋 TEST 11: Prompt Agent")
r = safe_request('get', f"{BACKEND_URL}/api/prompt-agent/examples/templates")
test("Get Templates", r and r.status_code == 200)

# Test 12: Execute Moderator
print("\n📋 TEST 12: Execute Moderator")
r = safe_request('post', f"{BACKEND_URL}/api/moderator/execute-with-input",
                json={
                    "node_id": "test_mod",
                    "upstream_outputs": {"summarizer": {"summary": "Test"}},
                    "user_input": "Additional input",
                    "use_input_node": True
                })
test("Execute Moderator", r and r.status_code == 200)

# Test 13: List Agents
print("\n📋 TEST 13: List Agents")
r = safe_request('get', f"{BACKEND_URL}/api/agents/")
test("List Agents", r and r.status_code == 200)

if r and r.status_code == 200:
    agents = r.json()
    test("Has Agents", len(agents) > 0)

# Test 14: Stripe Checkout
print("\n📋 TEST 14: Stripe Integration")
r = safe_request('post', f"{BACKEND_URL}/api/wallet/create-checkout-session",
                json={"amount": 1000})
test("Create Checkout", r and r.status_code == 200)

# Test 15: n8n Webhooks
print("\n📋 TEST 15: n8n Webhooks")
webhooks = ["summarizer", "sentiment", "translator"]
for webhook in webhooks:
    r = safe_request('post', f"{BACKEND_URL}/api/n8n/{webhook}",
                    json={"text": "test"})
    test(f"n8n {webhook}", r and r.status_code == 200)

# Print Summary
print("\n" + "="*60)
print("📊 TEST RESULTS SUMMARY")
print("="*60)
TOTAL = TESTS_PASSED + TESTS_FAILED
print(f"\n✅ PASSED: {TESTS_PASSED}/{TOTAL}")
print(f"❌ FAILED: {TESTS_FAILED}/{TOTAL}")
print(f"📈 SUCCESS: {TESTS_PASSED/TOTAL*100:.1f}%" if TOTAL > 0 else "No tests")

if TESTS_PASSED == TOTAL:
    print("\n🎉 PERFECT! All tests passed!")
    print("✅ System is 100% functional!")
elif TESTS_PASSED/TOTAL >= 0.8:
    print("\n✅ Good! Most tests passed")
else:
    print("\n❌ System has issues")

print("="*60 + "\n")

sys.exit(0 if TESTS_PASSED == TOTAL else 1)
