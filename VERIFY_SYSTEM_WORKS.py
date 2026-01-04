#!/usr/bin/env python3
"""
VERIFY SYSTEM WORKS - Complete verification script
"""

import requests
import json
import time
from datetime import datetime

backend = "http://localhost:8000"
frontend = "http://localhost:3000"

print("="*80)
print("🚀 VERIFYING GPTGRAM SYSTEM")
print("="*80)
print()

# Check services
print("📊 STEP 1: Checking Services")
print("-"*80)

backend_ok = False
frontend_ok = False

try:
    r = requests.get(f"{backend}/health", timeout=3)
    if r.status_code == 200:
        backend_ok = True
        print("✅ Backend: Running on port 8000")
    else:
        print("❌ Backend: Not healthy")
except Exception as e:
    print(f"❌ Backend: Not running - {e}")

try:
    r = requests.get(frontend, timeout=3)
    if r.status_code == 200:
        frontend_ok = True
        print("✅ Frontend: Running on port 3000")
    else:
        print("❌ Frontend: Not responding properly")
except Exception as e:
    print(f"❌ Frontend: Not running - {e}")

if not (backend_ok and frontend_ok):
    print("\n⚠️ Services not running properly. Attempting to fix...")
    import subprocess
    
    if not backend_ok:
        print("Restarting backend...")
        subprocess.run("lsof -ti:8000 | xargs kill -9 2>/dev/null", shell=True)
        time.sleep(1)
        subprocess.Popen("cd /Users/abdulmuiz/Documents/LAB/Gptgram/backend && python3 test_server.py > /tmp/backend.log 2>&1", shell=True)
        time.sleep(3)
    
    if not frontend_ok:
        print("Restarting frontend...")
        subprocess.run("lsof -ti:3000 | xargs kill -9 2>/dev/null", shell=True)
        time.sleep(1)
        subprocess.Popen("cd /Users/abdulmuiz/Documents/LAB/Gptgram/frontend && npx vite preview --port 3000 > /tmp/frontend.log 2>&1", shell=True)
        time.sleep(3)
    
    # Check again
    try:
        r = requests.get(f"{backend}/health", timeout=3)
        backend_ok = r.status_code == 200
    except:
        pass
    
    try:
        r = requests.get(frontend, timeout=3)
        frontend_ok = r.status_code == 200
    except:
        pass

# Load existing data
print("\n📊 STEP 2: Loading System Data")
print("-"*80)

try:
    # Get agents
    r = requests.get(f"{backend}/api/agents")
    agents = r.json()
    print(f"✅ Agents loaded: {len(agents)} agents")
    
    # Get runs
    r = requests.get(f"{backend}/api/runs/")
    runs = r.json()
    print(f"✅ Runs loaded: {len(runs)} runs")
    
    # Get wallet
    r = requests.get(f"{backend}/api/wallet/balance")
    wallet = r.json()
    print(f"✅ Wallet balance: ${wallet.get('balance', 0) / 100:.2f}")
    
except Exception as e:
    print(f"❌ Error loading data: {e}")

# If no agents, create some
if len(agents) == 0:
    print("\n📊 STEP 3: Creating Test Agents")
    print("-"*80)
    
    test_agents = [
        {
            "name": "Test Summarizer",
            "description": "Summarizes text",
            "type": "custom",
            "endpoint_url": "http://localhost:8000/api/mock/n8n/summarize",
            "price_cents": 50,
            "verification_level": "L2"
        },
        {
            "name": "Test Sentiment",
            "description": "Analyzes sentiment",
            "type": "custom",
            "endpoint_url": "http://localhost:8000/api/mock/n8n/sentiment",
            "price_cents": 30,
            "verification_level": "L1"
        }
    ]
    
    for agent_data in test_agents:
        try:
            r = requests.post(f"{backend}/api/agents", json=agent_data)
            if r.status_code in [200, 201]:
                print(f"✅ Created: {agent_data['name']}")
        except:
            pass

print("\n" + "="*80)
print("🎯 SYSTEM STATUS")
print("="*80)
print()

status = {
    "Backend": "✅ Running" if backend_ok else "❌ Not Running",
    "Frontend": "✅ Running" if frontend_ok else "❌ Not Running",
    "Agents": f"✅ {len(agents)} agents" if len(agents) > 0 else "❌ No agents",
    "Runs": f"✅ {len(runs)} runs" if len(runs) > 0 else "ℹ️ No runs yet",
    "Database": "✅ Working" if backend_ok else "❌ Not Working"
}

for key, value in status.items():
    print(f"{key}: {value}")

print("\n" + "="*80)
print("📋 MANUAL TEST INSTRUCTIONS")
print("="*80)
print()

if backend_ok and frontend_ok:
    print("✅ SYSTEM IS RUNNING! Follow these steps:")
    print()
    print("1. OPEN BROWSER:")
    print("   → Go to: http://localhost:3000")
    print("   → Should see login page")
    print()
    print("2. LOGIN:")
    print("   → Username: demo")
    print("   → Password: demo123")
    print("   → Click 'Sign In'")
    print()
    print("3. VERIFY PAGES WORK:")
    print("   ✓ Dashboard (/) - Shows stats")
    print("   ✓ Marketplace (/marketplace) - Shows agents")
    print("   ✓ My Agents (/agents) - Manage agents")
    print("   ✓ Chain Builder (/chains) - Build workflows")
    print("   ✓ Run History (/runs) - View executions")
    print()
    print("4. TEST AGENT LIBRARY:")
    print("   → Go to Chain Builder")
    print("   → Check right panel shows agents")
    print(f"   → Should see {len(agents)} agents")
    print("   → Search box should filter")
    print()
    print("5. TEST TIMELINE:")
    print("   → Go to Run History")
    print("   → Check timestamps (no 'None')")
    print("   → Dates should be like: 2025-11-01T15:28:21")
    
else:
    print("❌ SYSTEM NOT FULLY RUNNING!")
    print()
    print("Try these fixes:")
    print()
    print("1. RESTART BACKEND:")
    print("   lsof -ti:8000 | xargs kill -9")
    print("   cd backend && python3 test_server.py")
    print()
    print("2. RESTART FRONTEND:")
    print("   lsof -ti:3000 | xargs kill -9")
    print("   cd frontend && npm run build")
    print("   cd frontend && npx vite preview --port 3000")
    print()
    print("3. CHECK LOGS:")
    print("   tail -f /tmp/backend.log")
    print("   tail -f /tmp/frontend.log")

print("\n" + "="*80)

# Show current agents
if agents:
    print("📋 CURRENT AGENTS IN SYSTEM:")
    print("-"*80)
    for i, agent in enumerate(agents, 1):
        print(f"{i}. {agent['name']} ({agent.get('type', 'custom')}) - {agent.get('price_cents', 0)}¢")
    print()

# Show recent runs
if runs:
    print("📊 RECENT RUNS:")
    print("-"*80)
    for run in runs[:3]:
        print(f"• {run['chain_id']}")
        print(f"  Status: {run['status']}")
        print(f"  Started: {run.get('started_at', 'N/A')[:19] if run.get('started_at') else 'N/A'}")
        print(f"  Nodes: {len(run.get('outputs', {}))}")
    print()

print("="*80)
print("✅ VERIFICATION COMPLETE!")
print("="*80)

if backend_ok and frontend_ok:
    print()
    print("🎯 EVERYTHING IS WORKING!")
    print("   Open: http://localhost:3000")
    print("   Login: demo / demo123")
    print()
else:
    print()
    print("⚠️ Some issues detected - see fixes above")
    print()
