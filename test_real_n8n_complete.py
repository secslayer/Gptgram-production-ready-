#!/usr/bin/env python3
"""
Complete Real N8N Test with Correct HMAC
Tests the full system with actual n8n cloud webhooks
"""

import requests
import json
from datetime import datetime
import time

print("="*80)
print("🚀 COMPLETE REAL N8N TEST WITH CORRECT CREDENTIALS")
print("="*80)
print()

backend = "http://localhost:8000"
HMAC_SECRET = "s3cr3t"  # Real secret for n8n webhooks

# Step 1: Clear existing agents
print("📋 STEP 1: Clear Old Agents")
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

# Step 2: Create Real N8N Agents with Correct Credentials
print("📋 STEP 2: Create Real N8N Agents")
print("-"*80)

agents_config = [
    {
        "name": "n8n Summarizer",
        "description": "Summarizes text using n8n cloud",
        "type": "n8n",
        "endpoint_url": "https://templatechat.app.n8n.cloud/webhook/gptgram/summarize",
        "hmac_secret": HMAC_SECRET,
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
                "summary": {"type": "string"}
            }
        }
    },
    {
        "name": "Sentiment Analyzer",
        "description": "Analyzes text sentiment using n8n cloud",
        "type": "n8n",
        "endpoint_url": "https://templatechat.app.n8n.cloud/webhook/sentiment",
        "hmac_secret": HMAC_SECRET,
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
        "description": "Translates text using n8n cloud",
        "type": "n8n",
        "endpoint_url": "https://templatechat.app.n8n.cloud/webhook/translation-webhook",
        "hmac_secret": HMAC_SECRET,
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

for agent_data in agents_config:
    try:
        print(f"\nCreating: {agent_data['name']}")
        print(f"  URL: {agent_data['endpoint_url']}")
        print(f"  Secret: {'***' if agent_data['hmac_secret'] else 'None'}")
        
        response = requests.post(f"{backend}/api/agents", json=agent_data, timeout=10)
        
        if response.status_code in [200, 201]:
            agent = response.json()
            created_agents[agent_data['name']] = agent
            
            webhook_status = agent.get('webhook_status', 'unknown')
            if webhook_status == 'tested_ok':
                print(f"  ✅ Created & webhook tested OK")
            elif webhook_status == 'test_failed':
                print(f"  ⚠️ Created but webhook test failed")
                print(f"     Error: {agent.get('test_error', 'Unknown')[:100]}")
            else:
                print(f"  ✅ Created (no test)")
            
            print(f"  ID: {agent['id']}")
        else:
            print(f"  ❌ Failed: {response.status_code}")
            print(f"     {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")

print()
print(f"📊 Created {len(created_agents)} agents")

# Step 3: Test Individual Agent Execution with Real Data
print("\n" + "="*80)
print("📋 STEP 3: Test Individual Agent Execution")
print("-"*80)

test_text = "Artificial intelligence is transforming industries worldwide. Machine learning algorithms can now process vast amounts of data in seconds."

test_cases = [
    {
        "agent_name": "n8n Summarizer",
        "payload": {"text": test_text, "maxSentences": 2},
        "expected_fields": ["summary"]
    },
    {
        "agent_name": "Sentiment Analyzer",
        "payload": {"text": test_text},
        "expected_fields": ["sentiment", "score"]
    },
    {
        "agent_name": "Language Translator",
        "payload": {"text": "Hello world", "target": "es"},
        "expected_fields": ["translated", "target"]
    }
]

execution_results = {}

for test_case in test_cases:
    agent_name = test_case["agent_name"]
    if agent_name not in created_agents:
        print(f"\n⚠️ {agent_name} not created, skipping")
        continue
    
    agent = created_agents[agent_name]
    
    try:
        print(f"\nTesting: {agent_name}")
        print(f"  Payload: {json.dumps(test_case['payload'])}")
        
        response = requests.post(
            f"{backend}/api/agents/{agent['id']}/execute",
            json=test_case['payload'],
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            output = result.get('output', {})
            execution_results[agent_name] = output
            
            print(f"  ✅ Execution successful")
            
            # Check expected fields
            missing_fields = [f for f in test_case['expected_fields'] if f not in output]
            if missing_fields:
                print(f"  ⚠️ Missing fields: {missing_fields}")
            else:
                print(f"  ✅ All expected fields present")
            
            # Show output
            for key, value in output.items():
                if isinstance(value, str) and len(value) > 60:
                    print(f"  {key}: {value[:60]}...")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"  ❌ Execution failed: {response.status_code}")
            print(f"     {response.text[:200]}")
            execution_results[agent_name] = {"error": response.text}
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        execution_results[agent_name] = {"error": str(e)}

# Step 4: Create Complete Chain
print("\n" + "="*80)
print("📋 STEP 4: Create & Execute Complete Chain")
print("-"*80)

if len(created_agents) >= 3:
    test_id = datetime.now().strftime("%H%M%S")
    
    # Create input node
    input_id = f"input_{test_id}"
    try:
        r = requests.post(f"{backend}/api/moderator/input-node/create",
                         json={"node_id": input_id, "position": {"x": 100, "y": 100},
                               "initial_text": test_text})
        print(f"✅ Created input node: {input_id}")
    except Exception as e:
        print(f"❌ Input node failed: {e}")
    
    # Get agents
    summarizer = created_agents.get("n8n Summarizer")
    sentiment = created_agents.get("Sentiment Analyzer")
    translator = created_agents.get("Language Translator")
    
    if summarizer and sentiment and translator:
        nodes = [
            input_id,
            f"agent_{summarizer['id']}_{test_id}",
            f"agent_{sentiment['id']}_{test_id}",
            f"agent_{translator['id']}_{test_id}"
        ]
        
        run_data = {
            "chain_id": f"real_n8n_test_{test_id}",
            "status": "running",
            "nodes": nodes,
            "outputs": {}
        }
        
        try:
            r = requests.post(f"{backend}/api/runs/create", json=run_data)
            run_id = r.json().get("run_id")
            print(f"✅ Created run: {run_id}")
            
            # Execute chain step by step
            outputs = {}
            
            # 1. Input
            outputs[input_id] = {"text": test_text, "type": "input"}
            print(f"\n1. ✅ Input node")
            
            # 2. Summarizer
            print(f"2. Executing Summarizer...")
            r = requests.post(
                f"{backend}/api/agents/{summarizer['id']}/execute",
                json={"text": test_text, "maxSentences": 2},
                timeout=30
            )
            if r.status_code == 200:
                sum_result = r.json()['output']
                outputs[nodes[1]] = {**sum_result, "type": "summarizer", "agent_id": summarizer['id']}
                print(f"   ✅ Summary: {sum_result.get('summary', 'N/A')[:60]}...")
            else:
                print(f"   ❌ Failed: {r.status_code}")
                outputs[nodes[1]] = {"error": "Summarizer failed", "type": "error"}
            
            # 3. Sentiment
            print(f"3. Executing Sentiment Analyzer...")
            sum_text = outputs[nodes[1]].get('summary', test_text)
            r = requests.post(
                f"{backend}/api/agents/{sentiment['id']}/execute",
                json={"text": sum_text},
                timeout=30
            )
            if r.status_code == 200:
                sent_result = r.json()['output']
                outputs[nodes[2]] = {**sent_result, "type": "sentiment", "agent_id": sentiment['id']}
                print(f"   ✅ Sentiment: {sent_result.get('sentiment')} ({sent_result.get('score')})")
            else:
                print(f"   ❌ Failed: {r.status_code}")
                outputs[nodes[2]] = {"error": "Sentiment failed", "type": "error"}
            
            # 4. Translator
            print(f"4. Executing Translator...")
            r = requests.post(
                f"{backend}/api/agents/{translator['id']}/execute",
                json={"text": sum_text, "target": "es"},
                timeout=30
            )
            if r.status_code == 200:
                trans_result = r.json()['output']
                outputs[nodes[3]] = {**trans_result, "type": "translator", "agent_id": translator['id']}
                print(f"   ✅ Translation: {trans_result.get('translated', 'N/A')[:60]}...")
            else:
                print(f"   ❌ Failed: {r.status_code}")
                outputs[nodes[3]] = {"error": "Translator failed", "type": "error"}
            
            # Update run
            r = requests.put(f"{backend}/api/runs/{run_id}",
                            json={"status": "completed", "outputs": outputs})
            print(f"\n✅ Chain completed with {len(outputs)} node outputs")
            
            # Verify in run history
            time.sleep(0.5)
            r = requests.get(f"{backend}/api/runs/")
            runs = r.json()
            our_run = next((r for r in runs if r.get("run_id") == run_id), None)
            
            if our_run:
                print(f"\n✅ Run found in history")
                print(f"   Chain: {our_run['chain_id']}")
                print(f"   Status: {our_run['status']}")
                print(f"   Started: {our_run.get('started_at', 'N/A')[:19]}")
                print(f"   Completed: {our_run.get('completed_at', 'N/A')[:19]}")
                print(f"   Outputs: {len(our_run.get('outputs', {}))} nodes")
                
                # Verify all outputs present
                for node_id in nodes:
                    if node_id in our_run.get('outputs', {}):
                        output = our_run['outputs'][node_id]
                        output_type = output.get('type', 'unknown')
                        has_error = 'error' in output
                        status = "❌ Error" if has_error else "✅ OK"
                        print(f"   {status} {node_id}: {output_type}")
                    else:
                        print(f"   ❌ Missing: {node_id}")
            else:
                print(f"❌ Run not found in history")
                
        except Exception as e:
            print(f"❌ Chain execution failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Not all agents created")
else:
    print("❌ Need at least 3 agents")

# Final Summary
print("\n" + "="*80)
print("📊 FINAL SUMMARY")
print("="*80)
print()
print(f"✅ Agents Created: {len(created_agents)}")
for name in created_agents:
    print(f"   • {name}")

print(f"\n✅ Individual Tests:")
for name, result in execution_results.items():
    if 'error' in result:
        print(f"   ❌ {name}: {result['error'][:50]}")
    else:
        print(f"   ✅ {name}: Working")

print()
print("="*80)
print("🌐 TEST IN BROWSER")
print("="*80)
print()
print("1. Open: http://localhost:3000")
print("2. Login: demo / demo123")
print("3. Go to: Manage Agents")
print("4. Verify: 3 agents listed with correct names")
print("5. Go to: Chain Builder")
print("6. Add: Input node → Edit text")
print("7. Add: Agents from library")
print("8. Connect: Input → Summarizer → Sentiment → Translator")
print("9. Click: Agent to see recommendations (right panel)")
print("10. Execute: Click 'Run Chain'")
print("11. Go to: Run History")
print("12. Refresh: Click refresh button")
print("13. Expand: Your run to see all outputs")
print("14. Verify: Timeline shows dates/times")
print()
print("="*80)
print("✅ REAL N8N TEST COMPLETE!")
print("="*80)
