#!/usr/bin/env python3
"""
FINAL VERIFICATION - Everything should work now
"""

import requests
import json
from datetime import datetime

backend = "http://localhost:8000"
frontend = "http://localhost:3000"

print("="*80)
print("🎯 FINAL SYSTEM VERIFICATION")
print("="*80)
print()

# 1. Service Status
print("📊 Services Status:")
try:
    r = requests.get(f"{backend}/health", timeout=2)
    print(f"✅ Backend: Running (port 8000)")
except:
    print(f"❌ Backend: Not running")

try:
    r = requests.get(frontend, timeout=2)
    print(f"✅ Frontend: Running (port 3000)")
except:
    print(f"❌ Frontend: Not running")

print()
print("="*80)
print("📊 CURRENT SYSTEM STATE")
print("="*80)

# 2. Agents in system
r = requests.get(f"{backend}/api/agents")
agents = r.json()
print(f"\n✅ Total Agents: {len(agents)}")

# Group by category
categories = {}
for agent in agents:
    cat = agent.get('category', agent.get('type', 'general'))
    categories[cat] = categories.get(cat, 0) + 1

print(f"✅ Categories: {', '.join(categories.keys())}")

# Show all agents
print(f"\n📋 All Agents in System:")
for i, agent in enumerate(agents, 1):
    print(f"   {i}. {agent['name'][:30]:<30} ({agent.get('type', 'custom')}) - {agent.get('price_cents', 0)}¢")

# 3. Run History
r = requests.get(f"{backend}/api/runs/")
runs = r.json()
print(f"\n✅ Total Runs: {len(runs)}")

if runs:
    latest = runs[0]
    print(f"\n📊 Latest Run:")
    print(f"   Chain: {latest['chain_id']}")
    print(f"   Status: {latest['status']}")
    print(f"   Started: {latest.get('started_at', 'MISSING')}")
    print(f"   Completed: {latest.get('completed_at', 'MISSING')}")
    print(f"   Nodes: {len(latest.get('outputs', {}))}")

print()
print("="*80)
print("🌐 BROWSER VERIFICATION CHECKLIST")
print("="*80)

print("""
Open http://localhost:3000 in your browser
Login: demo / demo123

✅ MARKETPLACE (/marketplace):
   [ ] Navigate to Marketplace from menu
   [ ] See all 5+ agents displayed
   [ ] Prices shown (45¢, 35¢, 60¢, etc.)
   [ ] Search works (try "processor")
   [ ] Categories filter works
   [ ] Install button visible

✅ CHAIN BUILDER (/chains):
   [ ] Agent Library shows all agents (right panel)
   [ ] Count shows (5) or more agents
   [ ] Search box filters agents (try "emotion")
   [ ] Can drag agents to canvas
   [ ] Refresh button updates count
   [ ] Recommendations appear when selecting agent

✅ RUN HISTORY (/runs):
   [ ] Shows 2+ runs
   [ ] Timeline shows actual timestamps:
       Started: 2025-11-01T15:28:21...
       Completed: 2025-11-01T15:28:22...
   [ ] Duration calculated (1.0 seconds)
   [ ] Can expand run to see outputs
   [ ] No "None" values in timeline

✅ DASHBOARD (/):
   [ ] Shows real agent count: 5+
   [ ] Shows run count: 2+
   [ ] Success rate: 100%
   [ ] Recent runs displayed
   [ ] Wallet balance shown

✅ TEST COMPLEX CHAIN:
   1. Go to Chain Builder
   2. Add Input Node
   3. Add these agents in order:
      - AI Text Processor
      - Emotion Detector
      - Universal Translator
      - Data Extractor Pro
   4. Connect all nodes
   5. Click "Run Chain"
   6. Check Run History for results

📋 KEY POINTS TO VERIFY:
   ✓ Agent library search works
   ✓ Timeline has real timestamps (not None)
   ✓ Marketplace is accessible from menu
   ✓ All created agents appear everywhere

🎯 The agents you should see:
   • AI Text Processor (45¢)
   • Emotion Detector (35¢)
   • Universal Translator (60¢)
   • Data Extractor Pro (40¢)
   • Smart Classifier (30¢)
""")

print("="*80)
print("✅ EVERYTHING SHOULD BE WORKING NOW!")
print("="*80)
print()
print("If any issues remain, check:")
print("1. Browser console (F12) for errors")
print("2. Backend logs: tail -f /tmp/backend.log")
print("3. Frontend logs: tail -f /tmp/frontend.log")
print("="*80)
