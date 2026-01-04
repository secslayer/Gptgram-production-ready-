#!/usr/bin/env python3
"""
COMPREHENSIVE GPTGRAM SYSTEM TEST
Tests the entire flow: Agent creation → Chain execution → Run history
"""

import requests
import json
import time
from datetime import datetime
from colorama import init, Fore, Style

init()

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{text}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

def print_step(text):
    print(f"\n{Fore.GREEN}▶ {text}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")

backend = "http://localhost:8000"

print_header("🚀 COMPREHENSIVE GPTGRAM SYSTEM TEST")

# Step 1: Clear existing agents
print_step("STEP 1: Clean Slate - Clear All Agents")
try:
    r = requests.get(f"{backend}/api/agents")
    existing = r.json()
    for agent in existing:
        requests.delete(f"{backend}/api/agents/{agent['id']}")
    print_success(f"Cleared {len(existing)} existing agents")
except Exception as e:
    print_error(f"Could not clear agents: {e}")

# Step 2: Create agents with real n8n webhook configuration
print_step("STEP 2: Create N8N Agents with HMAC Authentication")

agents_config = [
    {
        "name": "AI Summarizer",
        "description": "Intelligent text summarization using n8n",
        "type": "n8n",
        "endpoint_url": "https://templatechat.app.n8n.cloud/webhook/gptgram/summarize",
        "hmac_secret": "s3cr3t",
        "price_cents": 50,
        "verification_level": "L2",
        "input_schema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string", "description": "Text to summarize"},
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
        "description": "Advanced sentiment analysis via n8n",
        "type": "n8n",
        "endpoint_url": "https://templatechat.app.n8n.cloud/webhook/sentiment",
        "hmac_secret": "s3cr3t",
        "price_cents": 30,
        "verification_level": "L3",
        "input_schema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"}
            }
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                "score": {"type": "number", "minimum": -1, "maximum": 1}
            }
        }
    },
    {
        "name": "Language Translator",
        "description": "Multi-language translation powered by n8n",
        "type": "n8n",
        "endpoint_url": "https://templatechat.app.n8n.cloud/webhook/translation-webhook",
        "hmac_secret": "s3cr3t",
        "price_cents": 75,
        "verification_level": "L2",
        "input_schema": {
            "type": "object",
            "required": ["text", "target"],
            "properties": {
                "text": {"type": "string", "description": "Text to translate"},
                "target": {"type": "string", "description": "Target language", "default": "es"}
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
total_price = 0

for idx, agent_data in enumerate(agents_config, 1):
    try:
        print(f"\n{idx}. Creating: {agent_data['name']}")
        print_info(f"   Endpoint: {agent_data['endpoint_url']}")
        print_info(f"   Type: {agent_data['type']}")
        print_info(f"   Price: {agent_data['price_cents']}¢")
        
        response = requests.post(f"{backend}/api/agents", json=agent_data, timeout=10)
        
        if response.status_code in [200, 201]:
            agent = response.json()
            created_agents[agent_data['name']] = agent
            total_price += agent_data['price_cents']
            
            webhook_status = agent.get('webhook_status', 'unknown')
            if webhook_status == 'tested_ok':
                print_success(f"   Agent created & webhook tested successfully")
            elif webhook_status == 'test_failed':
                print_info(f"   Agent created (webhook test failed - will use mock)")
            else:
                print_success(f"   Agent created successfully")
            
            print_info(f"   ID: {agent['id']}")
        else:
            print_error(f"   Failed to create: {response.status_code}")
    except Exception as e:
        print_error(f"   Error creating {agent_data['name']}: {str(e)[:100]}")

print(f"\n{Fore.CYAN}{'─'*80}{Style.RESET_ALL}")
print_success(f"Created {len(created_agents)}/{len(agents_config)} agents")
print_info(f"Total price for chain: {total_price}¢")

# Step 3: Test Individual Agent Execution
print_step("STEP 3: Test Individual Agent Execution")

test_text = "Artificial intelligence is transforming industries worldwide. Machine learning algorithms can now process vast amounts of data in seconds."

test_cases = [
    {
        "agent_name": "AI Summarizer",
        "payload": {"text": test_text, "maxSentences": 2},
        "check_fields": ["summary"]
    },
    {
        "agent_name": "Sentiment Analyzer",
        "payload": {"text": test_text},
        "check_fields": ["sentiment", "score"]
    },
    {
        "agent_name": "Language Translator",
        "payload": {"text": "Hello world", "target": "es"},
        "check_fields": ["translated"]
    }
]

execution_results = {}

for test_case in test_cases:
    agent_name = test_case["agent_name"]
    if agent_name not in created_agents:
        print_error(f"   {agent_name} not found, skipping")
        continue
    
    agent = created_agents[agent_name]
    
    try:
        print(f"\n• Testing: {agent_name}")
        
        response = requests.post(
            f"{backend}/api/agents/{agent['id']}/execute",
            json=test_case['payload'],
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            output = result.get('output', {})
            execution_results[agent_name] = output
            
            print_success(f"  Execution successful")
            
            # Check expected fields
            for field in test_case['check_fields']:
                if field in output:
                    value = output[field]
                    if isinstance(value, str) and len(value) > 50:
                        print_info(f"  {field}: {value[:50]}...")
                    else:
                        print_info(f"  {field}: {value}")
                else:
                    print_error(f"  Missing field: {field}")
        else:
            print_error(f"  Execution failed: {response.status_code}")
            execution_results[agent_name] = {"error": f"Status {response.status_code}"}
    except Exception as e:
        print_error(f"  Error: {str(e)[:100]}")
        execution_results[agent_name] = {"error": str(e)}

# Step 4: Create & Execute Complete Chain
print_step("STEP 4: Create & Execute Complete Chain")

if len(created_agents) >= 3:
    test_id = datetime.now().strftime("%H%M%S")
    
    # Create input node
    input_id = f"input_{test_id}"
    print("\nCreating input node...")
    try:
        r = requests.post(f"{backend}/api/moderator/input-node/create",
                         json={"node_id": input_id, "position": {"x": 100, "y": 100},
                               "initial_text": test_text})
        print_success(f"Input node created: {input_id}")
    except Exception as e:
        print_error(f"Input node creation failed: {e}")
    
    # Get agents
    summarizer = created_agents.get("AI Summarizer")
    sentiment = created_agents.get("Sentiment Analyzer")
    translator = created_agents.get("Language Translator")
    
    if summarizer and sentiment and translator:
        nodes = [
            input_id,
            f"agent_{summarizer['id']}_{test_id}",
            f"agent_{sentiment['id']}_{test_id}",
            f"agent_{translator['id']}_{test_id}"
        ]
        
        # Create run
        run_data = {
            "chain_id": f"comprehensive_test_{test_id}",
            "status": "running",
            "nodes": nodes,
            "outputs": {}
        }
        
        print("\nCreating chain run...")
        try:
            r = requests.post(f"{backend}/api/runs/create", json=run_data)
            run_id = r.json().get("run_id")
            print_success(f"Run created: {run_id}")
            
            # Execute chain step by step
            outputs = {}
            
            # 1. Input
            outputs[input_id] = {"text": test_text, "type": "input"}
            print_success(f"  1. Input node ready")
            
            # 2. Summarizer
            print(f"  2. Executing {summarizer['name']}...")
            r = requests.post(
                f"{backend}/api/agents/{summarizer['id']}/execute",
                json={"text": test_text, "maxSentences": 2},
                timeout=30
            )
            if r.status_code == 200:
                sum_result = r.json()['output']
                outputs[nodes[1]] = {
                    **sum_result,
                    "type": "summarizer",
                    "agent_id": summarizer['id'],
                    "agent_name": summarizer['name']
                }
                print_success(f"     Summary: {sum_result.get('summary', 'N/A')[:60]}...")
            
            # 3. Sentiment
            print(f"  3. Executing {sentiment['name']}...")
            sum_text = outputs[nodes[1]].get('summary', test_text)
            r = requests.post(
                f"{backend}/api/agents/{sentiment['id']}/execute",
                json={"text": sum_text},
                timeout=30
            )
            if r.status_code == 200:
                sent_result = r.json()['output']
                outputs[nodes[2]] = {
                    **sent_result,
                    "type": "sentiment",
                    "agent_id": sentiment['id'],
                    "agent_name": sentiment['name']
                }
                print_success(f"     Sentiment: {sent_result.get('sentiment')} (score: {sent_result.get('score')})")
            
            # 4. Translator
            print(f"  4. Executing {translator['name']}...")
            r = requests.post(
                f"{backend}/api/agents/{translator['id']}/execute",
                json={"text": sum_text[:50], "target": "es"},
                timeout=30
            )
            if r.status_code == 200:
                trans_result = r.json()['output']
                outputs[nodes[3]] = {
                    **trans_result,
                    "type": "translator",
                    "agent_id": translator['id'],
                    "agent_name": translator['name']
                }
                print_success(f"     Translation: {trans_result.get('translated', 'N/A')[:60]}...")
            
            # Update run with completed status
            print("\nUpdating run status...")
            r = requests.put(f"{backend}/api/runs/{run_id}",
                            json={"status": "completed", "outputs": outputs})
            print_success(f"Chain execution completed with {len(outputs)} outputs")
            
            # Calculate total cost
            total_cost = sum(created_agents[name].get('price_cents', 0) for name in created_agents)
            print_info(f"Total cost: {total_cost}¢")
            
            # Step 5: Verify Run History & Timeline
            print_step("STEP 5: Verify Run History & Timeline")
            
            time.sleep(0.5)
            r = requests.get(f"{backend}/api/runs/")
            runs = r.json()
            our_run = next((r for r in runs if r.get("run_id") == run_id), None)
            
            if our_run:
                print_success("Run found in history")
                
                # Check timeline
                started = our_run.get('started_at', 'N/A')
                completed = our_run.get('completed_at', 'N/A')
                
                print_info(f"Chain ID: {our_run['chain_id']}")
                print_info(f"Status: {our_run['status']}")
                print_success(f"Started: {started[:19] if started != 'N/A' else 'N/A'}")
                print_success(f"Completed: {completed[:19] if completed != 'N/A' else 'N/A'}")
                
                # Calculate duration if both timestamps exist
                if started != 'N/A' and completed != 'N/A':
                    from datetime import datetime
                    start_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(completed.replace('Z', '+00:00'))
                    duration = (end_dt - start_dt).total_seconds()
                    print_success(f"Duration: {duration:.1f} seconds")
                
                print_info(f"Total outputs: {len(our_run.get('outputs', {}))}")
                
                # Verify each node output
                print("\nNode Outputs:")
                for node_id in nodes:
                    if node_id in our_run.get('outputs', {}):
                        output = our_run['outputs'][node_id]
                        output_type = output.get('type', 'unknown')
                        
                        if 'error' in output:
                            print_error(f"  • {node_id[:20]}... ({output_type}): ERROR")
                        else:
                            print_success(f"  • {node_id[:20]}... ({output_type}): OK")
                            
                            # Show key output fields
                            if output_type == 'input':
                                text = output.get('text', '')
                                if text and text != "Enter your input here...":
                                    print_info(f"    Text: {text[:50]}...")
                                else:
                                    print_error(f"    Bad text: {text[:50]}")
                            elif output_type == 'summarizer':
                                summary = output.get('summary', 'N/A')
                                print_info(f"    Summary: {summary[:50]}...")
                            elif output_type == 'sentiment':
                                print_info(f"    Sentiment: {output.get('sentiment', 'N/A')} ({output.get('score', 'N/A')})")
                            elif output_type == 'translator':
                                print_info(f"    Translated: {output.get('translated', 'N/A')[:50]}...")
                    else:
                        print_error(f"  • {node_id[:20]}...: MISSING")
            else:
                print_error("Run not found in history")
                
        except Exception as e:
            print_error(f"Chain execution failed: {e}")
    else:
        print_error("Not all required agents created")
else:
    print_error("Need at least 3 agents to test chain")

# Final Summary
print_header("📊 FINAL TEST SUMMARY")

print(f"\n{Fore.GREEN}System Components:{Style.RESET_ALL}")
print_success(f"Backend API: {backend}")
print_success(f"Frontend: http://localhost:3000")

print(f"\n{Fore.GREEN}Test Results:{Style.RESET_ALL}")
print_success(f"Agents Created: {len(created_agents)}/{len(agents_config)}")

if created_agents:
    print(f"\n{Fore.GREEN}Created Agents:{Style.RESET_ALL}")
    for name, agent in created_agents.items():
        print(f"  • {name} (ID: {agent['id'][:8]}...)")

if execution_results:
    print(f"\n{Fore.GREEN}Agent Execution:{Style.RESET_ALL}")
    for name, result in execution_results.items():
        if 'error' in result:
            print_error(f"  • {name}: Failed")
        else:
            print_success(f"  • {name}: Success")

print_header("🌐 MANUAL BROWSER TESTING")

print(f"""
{Fore.YELLOW}Steps to verify in browser:{Style.RESET_ALL}

1. {Fore.CYAN}Open:{Style.RESET_ALL} http://localhost:3000
2. {Fore.CYAN}Login:{Style.RESET_ALL} demo / demo123
3. {Fore.CYAN}Go to:{Style.RESET_ALL} "Manage Agents"
   - Verify 3 agents are listed
   - Each shows correct name, type (n8n), and price

4. {Fore.CYAN}Go to:{Style.RESET_ALL} "Chain Builder"
   - Check Agent Library (right sidebar)
   - All 3 agents should be visible
   
5. {Fore.CYAN}Build Chain:{Style.RESET_ALL}
   - Click "Add Input Node"
   - Double-click to edit text
   - Click agents from library to add
   - Connect: Input → Summarizer → Sentiment → Translator
   
6. {Fore.CYAN}Test Recommendations:{Style.RESET_ALL}
   - Click any agent node
   - Right panel should show "Recommended Agents"
   - Shows other available agents with compatibility scores
   
7. {Fore.CYAN}Execute:{Style.RESET_ALL}
   - Click "Run Chain"
   - Wait for completion
   - Should see success dialog
   
8. {Fore.CYAN}Check Run History:{Style.RESET_ALL}
   - Go to "Run History"
   - Click "Refresh"
   - Find your run (latest)
   - Expand to see outputs
   - {Fore.GREEN}Verify:{Style.RESET_ALL}
     ✓ Timeline shows actual dates
     ✓ Duration calculated correctly
     ✓ All node outputs visible
     ✓ No "Enter your input here..."
     ✓ No truncated JSON
""")

print_header("✅ COMPREHENSIVE TEST COMPLETE!")

# Final status check
try:
    r = requests.get(f"{backend}/health")
    print_success("Backend: RUNNING")
except:
    print_error("Backend: NOT RUNNING")

try:
    r = requests.get("http://localhost:3000", timeout=2)
    print_success("Frontend: RUNNING")
except:
    print_info("Frontend: Check if running at http://localhost:3000")

print(f"\n{Fore.GREEN}🚀 System is ready for testing!{Style.RESET_ALL}\n")
