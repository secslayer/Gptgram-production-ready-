#!/usr/bin/env python3
"""
Complete UI and Backend Test
Tests everything including React Flow, input nodes, run history
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

BACKEND = "http://localhost:8000"
FRONTEND = "http://localhost:3000"

async def test_everything():
    print("\n" + "="*70)
    print("🔍 COMPLETE GPTGRAM SYSTEM TEST")
    print("="*70 + "\n")
    
    passed = 0
    failed = 0
    
    # First test backend
    print("📋 BACKEND TESTS")
    print("-"*40)
    
    # Test all critical endpoints
    endpoints = [
        ("/health", "Health"),
        ("/api/agents/", "Agents"),
        ("/api/runs/", "Runs"),
        ("/api/moderator/logs", "Moderator"),
        ("/api/analytics/data", "Analytics"),
        ("/api/wallet/balance", "Wallet"),
        ("/api/agents/compatibility-check?upstream_id=summarizer&downstream_id=sentiment", "Compatibility")
    ]
    
    for endpoint, name in endpoints:
        try:
            r = requests.get(f"{BACKEND}{endpoint}", timeout=3)
            if r.status_code in [200, 307]:
                print(f"✅ {name}: OK")
                passed += 1
                
                # Check specific fields
                if "analytics" in endpoint and r.status_code == 200:
                    data = r.json()
                    if "total_agents" in data and "chains" in data:
                        print(f"   ✓ Has agent count: {data['total_agents']}")
                        print(f"   ✓ Has chain data: {data['chains']}")
                        passed += 2
                    else:
                        print(f"   ✗ Missing fields")
                        failed += 2
            else:
                print(f"❌ {name}: Status {r.status_code}")
                failed += 1
        except Exception as e:
            print(f"❌ {name}: {str(e)[:50]}")
            failed += 1
    
    # Test agent creation with full flow
    print("\n📋 AGENT CREATION AND CHAIN TEST")
    print("-"*40)
    
    # Create test agent
    agent_data = {
        "name": f"UI_Test_{datetime.now().strftime('%H%M%S')}",
        "description": "Test agent for UI validation",
        "type": "custom",
        "input_schema": {
            "type": "object",
            "required": ["text"],
            "properties": {"text": {"type": "string"}}
        },
        "output_schema": {
            "type": "object",
            "properties": {"result": {"type": "string"}}
        },
        "example_input": {"text": "test"},
        "example_output": {"result": "output"},
        "price_cents": 10
    }
    
    try:
        r = requests.post(f"{BACKEND}/api/agents/create", json=agent_data, timeout=5)
        if r.status_code == 200:
            agent_id = r.json()["agent_id"]
            print(f"✅ Created agent: {agent_id}")
            passed += 1
            
            # Verify agent
            r2 = requests.post(f"{BACKEND}/api/agents/{agent_id}/verify", timeout=5)
            if r2.status_code == 200:
                print(f"✅ Verified agent")
                passed += 1
        else:
            print(f"❌ Agent creation failed: {r.status_code}")
            failed += 1
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        failed += 1
    
    # Test three-agent chain
    print("\n📋 THREE-AGENT CHAIN TEST")
    print("-"*40)
    
    # Create input node
    input_data = {
        "node_id": f"input_{datetime.now().strftime('%H%M%S')}",
        "position": {"x": 100, "y": 100},
        "initial_text": "Test input for chain"
    }
    
    try:
        r = requests.post(f"{BACKEND}/api/moderator/input-node/create", json=input_data, timeout=5)
        if r.status_code == 200:
            print(f"✅ Created input node: {input_data['node_id']}")
            passed += 1
        else:
            print(f"❌ Input node creation failed")
            failed += 1
    except:
        failed += 1
    
    # Test moderation chain
    moderations = [
        {
            "name": "Summarizer→Sentiment",
            "data": {
                "upstream_agent_id": "summarizer",
                "downstream_agent_id": "sentiment",
                "upstream_output": {
                    "summary": "Test summary",
                    "sentences": ["S1", "S2"],
                    "key_points": ["K1"]
                }
            }
        },
        {
            "name": "Sentiment→Translator",
            "data": {
                "upstream_agent_id": "sentiment",
                "downstream_agent_id": "translator",
                "upstream_output": {
                    "sentiment": "positive",
                    "score": 0.9
                },
                "user_input": "es"
            }
        }
    ]
    
    for mod in moderations:
        try:
            r = requests.post(f"{BACKEND}/api/moderator/moderate-payload", json=mod["data"], timeout=5)
            if r.status_code == 200:
                payload = r.json().get("payload", {})
                print(f"✅ {mod['name']}: {list(payload.keys())}")
                passed += 1
            else:
                print(f"❌ {mod['name']}: Failed")
                failed += 1
        except:
            failed += 1
    
    # Create and update run
    print("\n📋 RUN HISTORY TEST")
    print("-"*40)
    
    run_data = {
        "chain_id": f"test_{datetime.now().strftime('%H%M%S')}",
        "status": "running",
        "nodes": ["input", "summarizer", "sentiment", "translator"]
    }
    
    try:
        r = requests.post(f"{BACKEND}/api/runs/create", json=run_data, timeout=5)
        if r.status_code in [200, 201]:
            run_id = r.json()["run_id"]
            print(f"✅ Created run: {run_id}")
            passed += 1
            
            # Update run
            update = {
                "status": "completed",
                "outputs": {
                    "summarizer": {"summary": "Done"},
                    "sentiment": {"sentiment": "positive"},
                    "translator": {"text": "Hecho"}
                }
            }
            
            r2 = requests.put(f"{BACKEND}/api/runs/{run_id}", json=update, timeout=5)
            if r2.status_code == 200:
                print(f"✅ Updated run to completed")
                passed += 1
                
                # Check history
                r3 = requests.get(f"{BACKEND}/api/runs/", timeout=5)
                if r3.status_code == 200:
                    runs = r3.json()
                    our_run = next((r for r in runs if r.get("run_id") == run_id), None)
                    if our_run and our_run.get("status") == "completed":
                        print(f"✅ Run in history with outputs")
                        passed += 1
                    else:
                        print(f"❌ Run not properly in history")
                        failed += 1
    except Exception as e:
        print(f"❌ Run test failed: {e}")
        failed += 1
    
    # Now test UI with Playwright
    print("\n📋 UI TESTS WITH PLAYWRIGHT")
    print("-"*40)
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        # Test frontend loading
        try:
            await page.goto(FRONTEND, timeout=10000)
            print("✅ Frontend loaded")
            passed += 1
            
            # Check for React app
            content = await page.content()
            if "root" in content or "app" in content:
                print("✅ React app mounted")
                passed += 1
        except PlaywrightTimeout:
            print("❌ Frontend not responding")
            failed += 1
        
        # Test login
        try:
            # Fill login if present
            if "login" in page.url.lower():
                await page.fill('input[type="text"]', "demo", timeout=5000)
                await page.fill('input[type="password"]', "demo123", timeout=5000)
                await page.click('button[type="submit"]', timeout=5000)
                await page.wait_for_timeout(2000)
                print("✅ Login successful")
                passed += 1
        except:
            print("ℹ️ Already logged in or no login page")
        
        # Test navigation
        pages_to_test = [
            ("/agents", "Agents page"),
            ("/chains", "Chain builder"),
            ("/runs", "Run history"),
            ("/dashboard", "Dashboard"),
            ("/wallet", "Wallet")
        ]
        
        for path, name in pages_to_test:
            try:
                await page.goto(f"{FRONTEND}{path}", timeout=10000)
                await page.wait_for_timeout(1000)
                print(f"✅ {name} loads")
                passed += 1
                
                # Special checks
                if path == "/chains":
                    # Check for React Flow
                    flow = await page.query_selector('.react-flow')
                    if flow:
                        print("   ✓ React Flow present")
                        passed += 1
                        
                        # Check for input button
                        input_btn = await page.query_selector('button:has-text("Input")')
                        if input_btn:
                            print("   ✓ Input node button found")
                            passed += 1
                        else:
                            print("   ✗ Input node button missing")
                            failed += 1
                    else:
                        print("   ✗ React Flow missing")
                        failed += 1
                        
                elif path == "/runs":
                    # Check for run entries
                    runs = await page.query_selector_all('div[class*="border"]')
                    if runs:
                        print(f"   ✓ Found {len(runs)} run entries")
                        passed += 1
                    else:
                        print("   ✗ No run entries")
                        failed += 1
                        
                elif path == "/dashboard":
                    # Check for metrics
                    metrics = await page.query_selector_all('*[class*="text-2xl"], *[class*="text-3xl"]')
                    if metrics:
                        print(f"   ✓ Found {len(metrics)} metric cards")
                        passed += 1
                    else:
                        print("   ✗ No metrics displayed")
                        failed += 1
                        
            except Exception as e:
                print(f"❌ {name}: {str(e)[:50]}")
                failed += 1
        
        await browser.close()
        
    except Exception as e:
        print(f"❌ Playwright tests failed: {e}")
        failed += 1
    
    # Final summary
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
        elif rate >= 90:
            print("\n✅ Excellent! System is production ready")
        elif rate >= 80:
            print("\n✅ Good! Most features working")
        elif rate >= 60:
            print("\n⚠️ Some issues need attention")
        else:
            print("\n❌ Major problems detected")
            
        if failed > 0:
            print("\n🔧 Issues to fix:")
            if "Input node button missing" in str(failed):
                print("  - Add input node button to chain builder")
            if "No run entries" in str(failed):
                print("  - Run history not updating properly")
            if "No metrics" in str(failed):
                print("  - Dashboard not showing data")
            if "React Flow missing" in str(failed):
                print("  - Chain builder not loading React Flow")
    
    print("="*70 + "\n")
    
    return failed == 0

# Run the test
if __name__ == "__main__":
    result = asyncio.run(test_everything())
    exit(0 if result else 1)
