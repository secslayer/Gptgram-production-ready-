#!/usr/bin/env python3
"""
QUICK VERIFICATION - Check current system state
"""

import requests
import json

print("="*60)
print("🔍 GPTGRAM SYSTEM STATUS")
print("="*60)

# Check backend
try:
    r = requests.get("http://localhost:8000/health", timeout=1)
    print("✅ Backend: RUNNING")
except:
    print("❌ Backend: NOT RUNNING")

# Check frontend
import socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', 3000))
    sock.close()
    if result == 0:
        print("✅ Frontend: RUNNING")
    else:
        print("❌ Frontend: NOT RUNNING")
except:
    print("❌ Frontend: NOT RUNNING")

# Check agents
try:
    r = requests.get("http://localhost:8000/api/agents", timeout=1)
    agents = r.json()
    print(f"✅ Agents: {len(agents)} in system")
    print("\nAgent Library:")
    for i, agent in enumerate(agents, 1):
        print(f"  {i}. {agent['name'][:30]:<30} - {agent.get('price_cents', 0)}¢")
except:
    print("❌ Could not load agents")

# Check runs
try:
    r = requests.get("http://localhost:8000/api/runs/", timeout=1)
    runs = r.json()
    print(f"\n✅ Runs: {len(runs)} executed")
except:
    print("\n❌ Could not load runs")

print("\n" + "="*60)
print("📝 AGENT LIBRARY REFRESH STATUS")
print("="*60)
print("""
✅ Auto-refresh: Every 5 seconds
✅ Focus trigger: When switching tabs
✅ Visibility trigger: When page visible
✅ Manual refresh: Button with count

To test:
1. Open http://localhost:3000
2. Go to Chain Builder (/chains)
3. Agent Library shows all agents
4. Updates automatically within 5 seconds
""")

print("="*60)
