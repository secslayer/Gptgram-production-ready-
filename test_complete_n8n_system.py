#!/usr/bin/env python3
"""
Complete N8N Agent System Test
Tests the full flow: Create agents via UI → Execute in chain → View results
"""

import requests
import json
import time
from datetime import datetime

print("="*80)
print("🚀 COMPLETE N8N AGENT SYSTEM TEST")
print("="*80)
print()

backend = "http://localhost:8000"
frontend = "http://localhost:3000"

# Step 1: Clear all existing agents (fresh start)
print("📋 STEP 1: Clean Slate - Remove Old Agents")
print("-"*80)
try:
    r = requests.get(f"{backend}/api/agents")
    existing = r.json()
    for agent in existing:
        requests.delete(f"{backend}/api/agents/{agent['id']}")
    print(f"✅ Removed {len(existing)} existing agents")
except Exception as e:
    print(f"⚠️ Could not clear agents: {e}")

print()

# Step 2: Create Real N8N Agents
print("📋 STEP 2: Create Real N8N Agents")
print("-"*80)

agents_to_create = [
    {
        "name": "n8n Summarizer",
        "description": "Summarizes long text using n8n cloud webhook",
        "type": "n8n",
        "endpoint_url": "https://templatechat.app.n8n.cloud/webhook/gptgram/summarize",
        "hmac_secret": "",  # Add if you have one
        "price_cents": 50,
        "verification_level": "L2",
        "input_schema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string"},
                "maxSentences": {"type": "integer", "default": 2}
            }
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "sentences": {"type": "array"}
            }
        }
    },
    {
        "name": "Sentiment Analyzer",
        "description": "Analyzes sentiment using n8n cloud webhook",
        "type": "n8n",
        "endpoint_url": "https://templatechat.app.n8n.cloud/webhook/sentiment",
        "hmac_secret": "",
        "price_cents": 30,
        "verification_level": "L3",
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
                "sentiment": {"type": "string"},
                "score": {"type": "number"}
            }
        }
    },
    {
        "name": "Language Translator",
        "description": "Translates text using n8n cloud webhook",
        "type": "n8n",
        "endpoint_url": "https://templatechat.app.n8n.cloud/webhook/translation-webhook",
        "hmac_secret": "",
        "price_cents": 75,
        "verification_level": "L2",
        "input_schema": {
            "type": "object",
            "required": ["text", "target"],
            "properties": {
                "text": {"type": "string"},
                "target": {"type": "string", "default": "es"}
            }
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "translated": {"type": "string"},
                "target": {"type": "string"}
            }
        }
    }
]

created_agents = {}

for agent_data in agents_to_create:
    try:
        print(f"\nCreating: {agent_data['name']}")
        print(f"  URL: {agent_data['endpoint_url']}")
        
        response = requests.post(f"{backend}/api/agents", json=agent_data, timeout=10)
        
        if response.status_code in [200, 201]:
            agent = response.json()
            created_agents[agent_data['name']] = agent
            
            webhook_status = agent.get('webhook_status', 'unknown')
            if webhook_status == 'tested_ok':
                print(f"  ✅ Created & tested successfully")
            elif webhook_status == 'test_failed':
                print(f"  ⚠️ Created but webhook test failed")
                print(f"     Error: {agent.get('test_error', 'Unknown')}")
            else:
                print(f"  ✅ Created")
            
            print(f"  ID: {agent['id']}")
        else:
            print(f"  ❌ Failed: {response.status_code}")
            print(f"     {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print()
print(f"📊 Created {len(created_agents)} agents")

# Step 3: Test Individual Agent Execution
print("\n" + "="*80)
print("📋 STEP 3: Test Individual Agent Execution")
print("-"*80)

test_text = "Artificial intelligence is revolutionizing technology and transforming industries globally"

for agent_name, agent in created_agents.items():
    try:
        print(f"\nTesting: {agent_name}")
        
        payload = {"text": test_text}
        if "Translator" in agent_name:
            payload["target"] = "es"
        
        response = requests.post(
            f"{backend}/api/agents/{agent['id']}/execute",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            output = result.get('output', {})
            
            print(f"  ✅ Execution successful")
            print(f"  Input: {test_text[:50]}...")
            
            # Show key outputs
            if 'summary' in output:
                print(f"  Output (summary): {output['summary'][:60]}...")
            elif 'sentiment' in output:
                print(f"  Output: {output['sentiment']} ({output.get('score', 'N/A')})")
            elif 'translated' in output:
                print(f"  Output (translated): {output['translated'][:60]}...")
            else:
                print(f"  Output: {json.dumps(output)[:100]}...")
        else:
            print(f"  ❌ Execution failed: {response.status_code}")
            print(f"     {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")

# Step 4: Create Complex Chain
print("\n" + "="*80)
print("📋 STEP 4: Create Complex Chain Run")
print("-"*80)

test_id = datetime.now().strftime("%H%M%S")

# Create input node
input_id = f"input_{test_id}"
try:
    r = requests.post(f"{backend}/api/moderator/input-node/create",
                     json={"node_id": input_id, "position": {"x": 100, "y": 100},
                           "initial_text": test_text})
    print(f"✅ Created input node: {input_id}")
except Exception as e:
    print(f"❌ Input node creation failed: {e}")

# Create chain run
if len(created_agents) >= 3:
    summarizer = list(created_agents.values())[0]
    sentiment = list(created_agents.values())[1]
    translator = list(created_agents.values())[2]
    
    nodes = [
        input_id,
        f"agent_{summarizer['id']}_{test_id}",
        f"agent_{sentiment['id']}_{test_id}",
        f"agent_{translator['id']}_{test_id}"
    ]
    
    run_data = {
        "chain_id": f"n8n_test_{test_id}",
        "status": "running",
        "nodes": nodes,
        "outputs": {}
    }
    
    try:
        r = requests.post(f"{backend}/api/runs/create", json=run_data)
        run_id = r.json().get("run_id")
        print(f"✅ Created run: {run_id}")
        
        # Execute chain
        outputs = {}
        
        # Input
        outputs[input_id] = {"text": test_text, "type": "input"}
        print(f"\n1. Input node executed")
        
        # Summarizer
        print(f"2. Executing {summarizer['name']}...")
        r = requests.post(
            f"{backend}/api/agents/{summarizer['id']}/execute",
            json={"text": test_text},
            timeout=30
        )
        sum_result = r.json()
        outputs[nodes[1]] = {**sum_result['output'], "type": "summarizer", "agent_id": summarizer['id']}
        print(f"   ✅ Result: {json.dumps(sum_result['output'])[:80]}...")
        
        # Sentiment
        print(f"3. Executing {sentiment['name']}...")
        sum_text = sum_result['output'].get('summary', test_text)
        r = requests.post(
            f"{backend}/api/agents/{sentiment['id']}/execute",
            json={"text": sum_text},
            timeout=30
        )
        sent_result = r.json()
        outputs[nodes[2]] = {**sent_result['output'], "type": "sentiment", "agent_id": sentiment['id']}
        print(f"   ✅ Result: {json.dumps(sent_result['output'])[:80]}...")
        
        # Translator
        print(f"4. Executing {translator['name']}...")
        r = requests.post(
            f"{backend}/api/agents/{translator['id']}/execute",
            json={"text": sum_text, "target": "es"},
            timeout=30
        )
        trans_result = r.json()
        outputs[nodes[3]] = {**trans_result['output'], "type": "translator", "agent_id": translator['id']}
        print(f"   ✅ Result: {json.dumps(trans_result['output'])[:80]}...")
        
        # Update run
        r = requests.put(f"{backend}/api/runs/{run_id}",
                        json={"status": "completed", "outputs": outputs})
        print(f"\n✅ Chain completed with {len(outputs)} outputs")
        
        # Verify in run history
        r = requests.get(f"{backend}/api/runs/")
        runs = r.json()
        our_run = next((r for r in runs if r.get("run_id") == run_id), None)
        
        if our_run:
            print(f"\n✅ Run found in history")
            print(f"   Chain: {our_run['chain_id']}")
            print(f"   Status: {our_run['status']}")
            print(f"   Outputs: {len(our_run.get('outputs', {}))} nodes")
            
            # Verify outputs
            for node_id in nodes:
                if node_id in our_run.get('outputs', {}):
                    print(f"   ✅ {node_id}: Output saved")
                else:
                    print(f"   ❌ {node_id}: Output missing")
        else:
            print(f"❌ Run not found in history")
            
    except Exception as e:
        print(f"❌ Chain execution failed: {e}")
        import traceback
        traceback.print_exc()

# Summary
print("\n" + "="*80)
print("📊 TEST SUMMARY")
print("="*80)
print()
print(f"✅ Agents Created: {len(created_agents)}")
print(f"✅ System Components:")
print(f"   • Agent Manager UI: {frontend}/agents")
print(f"   • Chain Builder: {frontend}/chains")
print(f"   • Run History: {frontend}/runs")
print()
print("📝 Next Steps (Manual UI Testing):")
print("1. Open browser: http://localhost:3000")
print("2. Login: demo / demo123")
print("3. Go to 'Manage Agents'")
print("4. Verify the 3 n8n agents are listed")
print("5. Go to 'Chain Builder'")
print("6. Add input node")
print("7. Add agents from library (drag or click)")
print("8. Connect: Input → Summarizer → Sentiment → Translator")
print("9. Click 'Run Chain'")
print("10. Go to 'Run History' and verify outputs")
print()
print("="*80)
print("✅ COMPLETE N8N AGENT SYSTEM TEST FINISHED")
print("="*80)
