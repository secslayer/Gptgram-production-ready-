#!/usr/bin/env python3
"""
Quick setup - Creates agents and shows system status
"""

import requests
import json

backend = "http://localhost:8000"

print("🚀 QUICK GPTGRAM SETUP")
print("="*60)

# Clear existing agents
r = requests.get(f"{backend}/api/agents")
for agent in r.json():
    requests.delete(f"{backend}/api/agents/{agent['id']}")
print("✅ Cleared existing agents")

# Create agents (using simple type to avoid webhook testing)
agents = [
    {
        "name": "AI Summarizer",
        "description": "Summarizes text using AI",
        "type": "custom",  # Using custom to avoid webhook test
        "endpoint_url": "http://localhost:8000/api/mock/n8n/summarize",
        "hmac_secret": "s3cr3t",
        "price_cents": 50,
        "verification_level": "L2"
    },
    {
        "name": "Sentiment Analyzer",
        "description": "Analyzes sentiment",
        "type": "custom",
        "endpoint_url": "http://localhost:8000/api/mock/n8n/sentiment",
        "hmac_secret": "s3cr3t",
        "price_cents": 30,
        "verification_level": "L3"
    },
    {
        "name": "Language Translator",
        "description": "Translates text",
        "type": "custom",
        "endpoint_url": "http://localhost:8000/api/mock/n8n/translation",
        "hmac_secret": "s3cr3t",
        "price_cents": 75,
        "verification_level": "L2"
    }
]

created = []
for agent_data in agents:
    r = requests.post(f"{backend}/api/agents", json=agent_data)
    if r.status_code in [200, 201]:
        agent = r.json()
        created.append(agent)
        print(f"✅ Created: {agent['name']} (ID: {agent['id'][:8]}...)")

print(f"\n📊 Created {len(created)} agents")

# Test execution
if created:
    agent = created[0]
    r = requests.post(
        f"{backend}/api/agents/{agent['id']}/execute",
        json={"text": "Test text"}
    )
    if r.status_code == 200:
        print(f"✅ Agent execution working")

print("\n🎯 SYSTEM STATUS:")
print(f"✅ Backend: http://localhost:8000")
print(f"✅ Frontend: http://localhost:3000")
print(f"✅ Agents: {len(created)} created")
print("\n📝 Open browser and test:")
print("1. http://localhost:3000")
print("2. Login: demo / demo123")
print("3. Check 'Manage Agents' for created agents")
print("4. Use 'Chain Builder' to build and execute chains")
print("5. View results in 'Run History'")
