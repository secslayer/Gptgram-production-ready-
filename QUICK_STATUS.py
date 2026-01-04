#!/usr/bin/env python3
"""
QUICK STATUS CHECK - Non-blocking verification
"""

import requests
import socket
import json

print("="*60)
print("🔍 QUICK SYSTEM STATUS")
print("="*60)
print()

# Check backend
try:
    r = requests.get("http://localhost:8000/health", timeout=1)
    print("✅ Backend: RUNNING")
except:
    print("❌ Backend: NOT RUNNING")

# Check frontend port
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', 3000))
    sock.close()
    
    if result == 0:
        print("✅ Frontend: PORT OPEN (3000)")
    else:
        print("❌ Frontend: PORT CLOSED")
except:
    print("❌ Frontend: ERROR")

# Check data
try:
    r = requests.get("http://localhost:8000/api/agents", timeout=1)
    agents = r.json()
    print(f"✅ Agents: {len(agents)} created")
    
    r = requests.get("http://localhost:8000/api/runs/", timeout=1)
    runs = r.json()
    print(f"✅ Runs: {len(runs)} executed")
    
    if runs:
        latest = runs[0]
        if latest.get('started_at') and latest.get('started_at') != 'None':
            print(f"✅ Timeline: Working")
        else:
            print(f"❌ Timeline: Has None values")
            
except Exception as e:
    print(f"❌ Data check error: {str(e)[:30]}")

print("\n" + "="*60)
print("📝 BROWSER ACCESS")
print("="*60)
print()
print("URL: http://localhost:3000")
print("Login: demo / demo123")
print()
print("If page doesn't load, frontend needs restart:")
print("  1. Kill: lsof -ti:3000 | xargs kill -9")
print("  2. Start: cd frontend && npm run dev")
print()
print("="*60)
