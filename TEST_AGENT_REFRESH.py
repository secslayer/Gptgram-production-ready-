#!/usr/bin/env python3
"""
TEST AGENT LIBRARY REFRESH
Tests that newly added agents appear in the chain builder
"""

import requests
import json
import time
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

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

# Main test
print("="*80)
print("🚀 AGENT LIBRARY REFRESH TEST")
print("="*80)

# 1. Check current agents
print_test("INITIAL AGENT COUNT")

try:
    r = requests.get(f"{BACKEND_URL}/api/agents", timeout=2)
    if r.status_code == 200:
        initial_agents = r.json()
        print_ok(f"Initial agents: {len(initial_agents)}")
        
        # List current agents
        for agent in initial_agents:
            print_info(f"  • {agent['name']} ({agent['id'][:8]}...)")
    else:
        print_fail("Failed to get initial agents")
        exit(1)
except Exception as e:
    print_fail(f"Error getting agents: {e}")
    exit(1)

# 2. Create a new test agent
print_test("CREATING NEW AGENT")

test_agent = {
    "name": f"Test Agent {datetime.now().strftime('%H%M%S')}",
    "description": "Agent to test library refresh",
    "type": "custom",
    "category": "test",
    "endpoint_url": "http://localhost:8000/api/mock/test",
    "hmac_secret": "test123",
    "price_cents": 99,
    "verification_level": "L2"
}

try:
    r = requests.post(f"{BACKEND_URL}/api/agents", json=test_agent, timeout=2)
    if r.status_code in [200, 201]:
        new_agent = r.json()
        print_ok(f"Created: {new_agent['name']} (ID: {new_agent['id'][:8]}...)")
    else:
        print_fail(f"Failed to create agent: {r.status_code}")
        exit(1)
except Exception as e:
    print_fail(f"Error creating agent: {e}")
    exit(1)

# 3. Verify agent appears in API
print_test("VERIFYING AGENT IN API")

time.sleep(1)

try:
    r = requests.get(f"{BACKEND_URL}/api/agents", timeout=2)
    if r.status_code == 200:
        updated_agents = r.json()
        print_ok(f"Updated agents: {len(updated_agents)}")
        
        # Check if new agent is present
        agent_found = any(a['id'] == new_agent['id'] for a in updated_agents)
        
        if agent_found:
            print_ok(f"New agent '{new_agent['name']}' found in API")
        else:
            print_fail("New agent not found in API")
        
        # Calculate difference
        if len(updated_agents) > len(initial_agents):
            print_ok(f"Agent count increased by {len(updated_agents) - len(initial_agents)}")
        else:
            print_fail("Agent count did not increase")
    else:
        print_fail("Failed to get updated agents")
except Exception as e:
    print_fail(f"Error verifying agent: {e}")

# 4. Test agent execution
print_test("TESTING NEW AGENT EXECUTION")

try:
    r = requests.post(
        f"{BACKEND_URL}/api/agents/{new_agent['id']}/execute",
        json={"text": "Test execution"},
        timeout=2
    )
    if r.status_code == 200:
        result = r.json()
        print_ok("New agent executes successfully")
    else:
        print_fail(f"Agent execution failed: {r.status_code}")
except Exception as e:
    print_fail(f"Execution error: {e}")

# Summary
print("\n" + "="*80)
print("📊 TEST SUMMARY")
print("="*80)

print(f"""
Initial Agent Count: {len(initial_agents)}
Final Agent Count: {len(updated_agents) if 'updated_agents' in locals() else 'Unknown'}
New Agent Created: {new_agent['name'] if 'new_agent' in locals() else 'Failed'}
Agent Found in API: {'Yes' if agent_found else 'No'}

BROWSER VERIFICATION:
1. Open http://localhost:3000
2. Login: demo / demo123
3. Go to Chain Builder (/chains)
4. Check Agent Library panel on right

EXPECTED:
• Should show {len(updated_agents) if 'updated_agents' in locals() else '?'} agents
• New agent "{new_agent['name'] if 'new_agent' in locals() else '?'}" should appear
• Refresh happens automatically every 5 seconds
• Manual refresh button shows updated count

REFRESH TRIGGERS:
• Automatic: Every 5 seconds
• Manual: Click "Refresh Agents" button
• Focus: When switching back to browser tab
• Visibility: When page becomes visible

IF NOT UPDATING:
1. Click "Refresh Agents" button manually
2. Wait 5 seconds for auto-refresh
3. Switch tabs and switch back
4. Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)
""")

print("="*80)
print("✅ TEST COMPLETE - CHECK BROWSER!")
print("="*80)
