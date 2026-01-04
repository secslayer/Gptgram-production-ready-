#!/usr/bin/env python3
"""
Simple test server with in-memory database
For testing without full Docker setup
"""

from fastapi import FastAPI, HTTPException, Request, Body, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
import uuid
import random
import sys
import os
import hmac
import hashlib
import json
import requests

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import the complete transformer system
try:
    from app.api.complete_transformer_system import router as transformer_router
    from app.api.prompt_agent_system import router as prompt_agent_router
    from app.api.agents_enhanced import router as agents_router
    from app.api.moderator_fixed import router as moderator_fixed_router
    from app.api.run_history import router as run_router
except ImportError:
    transformer_router = None
    prompt_agent_router = None
    agents_router = None
    moderator_fixed_router = None
    run_router = None

import json
import hmac
import hashlib
from datetime import datetime
import stripe

# Configure Stripe
stripe.api_key = ""

app = FastAPI(title="GPTGram Test Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory databases (for testing)
agents = {}  # Agent storage
agents_db = []
chains_db = []
runs_db = []  # Add runs database
runs = {}  # Run storage by ID
users = {}
wallets = {}

# Test data
demo_user = {
    "id": str(uuid.uuid4()),
    "username": "demo",
    "email": "demo@gptgram.ai",
    "password": "demo123",  # In real app, this would be hashed
    "wallet_balance": 5000
}
users["demo"] = demo_user

# Models
class UserRegister(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Agent(BaseModel):
    name: str
    description: Optional[str] = ""
    type: str = "custom"  # "n8n" or "custom"
    endpoint_url: str
    hmac_secret: Optional[str] = None  # For n8n webhook authentication
    price_cents: int = 50
    verification_level: str = "L1"
    input_schema: Optional[Dict] = None
    output_schema: Optional[Dict] = None

class Chain(BaseModel):
    name: str
    descriptor: Dict
    mode: str = "balanced"

# Routes
@app.get("/")
async def root():
    return {"message": "GPTGram Test Server Running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/auth/register")
async def register(user: UserRegister):
    if user.username in users:
        raise HTTPException(400, "Username already exists")
    
    new_user = {
        "id": str(uuid.uuid4()),
        "username": user.username,
        "email": user.email,
        "password": user.password,
        "wallet_balance": 5000
    }
    users[user.username] = new_user
    
    return {"message": "User registered", "user_id": new_user["id"]}

@app.post("/api/auth/token")
async def login(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or user["password"] != password:
        raise HTTPException(401, "Invalid credentials")
    
    # Simple token (in real app, would be JWT)
    token = f"token_{user['id']}"
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/auth/me")
async def get_current_user():
    return demo_user

@app.get("/api/agents")
async def list_agents():
    # Return only user-created agents (no hardcoded demos)
    return list(agents.values())

def generate_hmac_signature(payload: str, secret: str) -> str:
    """Generate HMAC SHA256 signature for n8n webhook"""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

async def call_n8n_webhook(url: str, data: dict, hmac_secret: str = None) -> dict:
    """Call n8n webhook with HMAC authentication"""
    headers = {"Content-Type": "application/json"}
    
    # For testing, redirect to local mock endpoints
    if "templatechat.app.n8n.cloud" in url:
        # Use local mock endpoints instead
        if "sentiment" in url:
            url = "http://localhost:8000/api/mock/n8n/sentiment"
        elif "translation" in url:
            url = "http://localhost:8000/api/mock/n8n/translation"
        elif "summarize" in url:
            url = "http://localhost:8000/api/mock/n8n/summarize"
        print(f"Redirecting to mock endpoint: {url}")
    
    # Add HMAC signature if secret provided
    if hmac_secret:
        payload = json.dumps(data, separators=(',', ':'))
        signature = generate_hmac_signature(payload, hmac_secret)
        headers["X-GPTGRAM-Signature"] = f"sha256={signature}"
        headers["X-GPTGRAM-Idempotency"] = f"gptgram-{uuid.uuid4().hex[:12]}"
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Try to parse JSON
        try:
            result = response.json()
            print(f"Webhook response: {json.dumps(result)[:200]}")
            return result
        except json.JSONDecodeError:
            # If response is empty, return mock data
            if not response.text:
                print("Warning: Empty response from webhook, using mock data")
                if "sentiment" in url:
                    return {"sentiment": "neutral", "score": 0}
                elif "translation" in url:
                    return {"translated": "[Translation]", "target": "es"}
                elif "summarize" in url:
                    return {"summary": "[Summary]"}
            print(f"Warning: n8n returned non-JSON: {response.text[:200]}")
            return {"result": response.text or "[empty]", "raw_response": True}
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" | Status: {e.response.status_code}"
        print(f"Webhook error: {error_msg}")
        # Return mock data on error for testing
        if "sentiment" in url:
            return {"sentiment": "neutral", "score": 0, "error": "Using mock due to error"}
        elif "translation" in url:
            return {"translated": "Hola mundo", "target": "es", "error": "Using mock due to error"}
        elif "summarize" in url:
            return {"summary": "AI transforms industries.", "error": "Using mock due to error"}
        raise HTTPException(500, f"n8n webhook call failed: {error_msg}")

@app.post("/api/agents")
async def create_agent(agent: Agent):
    """Create a new agent and optionally test the webhook"""
    agent_id = str(uuid.uuid4())
    agent_data = agent.dict()
    agent_data["id"] = agent_id
    agent_data["status"] = "active"
    agent_data["created_at"] = datetime.utcnow().isoformat()
    
    # For n8n agents, test the webhook
    if agent_data["type"] == "n8n" and agent_data.get("endpoint_url"):
        try:
            # Test with minimal payload
            test_payload = {"text": "test"}
            await call_n8n_webhook(
                agent_data["endpoint_url"],
                test_payload,
                agent_data.get("hmac_secret")
            )
            agent_data["webhook_status"] = "tested_ok"
        except Exception as e:
            print(f"Warning: Webhook test failed for {agent_data['name']}: {e}")
            agent_data["webhook_status"] = "test_failed"
            agent_data["test_error"] = str(e)
    
    agents[agent_id] = agent_data
    return agent_data

@app.post("/api/agents/{agent_id}/execute")
async def execute_agent(agent_id: str, payload: dict = Body(...)):
    """Execute an agent with the given payload"""
    if agent_id not in agents:
        raise HTTPException(404, "Agent not found")
    
    agent = agents[agent_id]
    
    if agent["type"] == "n8n":
        result = await call_n8n_webhook(
            agent["endpoint_url"],
            payload,
            agent.get("hmac_secret")
        )
        return {
            "agent_id": agent_id,
            "agent_name": agent["name"],
            "input": payload,
            "output": result
        }
    else:
        # Custom agent - would call custom endpoint
        return {
            "agent_id": agent_id,
            "agent_name": agent["name"],
            "output": {"result": "Custom agent executed"}
        }

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    if agent_id not in agents:
        raise HTTPException(404, "Agent not found")
    
    deleted = agents.pop(agent_id)
    return {"message": "Agent deleted", "agent": deleted}

@app.get("/api/chains")
async def list_chains():
    demo_chains = [
        {
            "id": "1",
            "name": "Text Processing Pipeline",
            "nodes": 3,
            "estimated_cost_cents": 155
        }
    ]
    return list(chains.values()) + demo_chains

@app.post("/api/chains")
async def create_chain(chain: Chain):
    chain_id = str(uuid.uuid4())
    chain_data = chain.dict()
    chain_data["id"] = chain_id
    chains[chain_id] = chain_data
    return chain_data

@app.post("/api/chains/{chain_id}/run")
async def run_chain(chain_id: str):
    run_id = str(uuid.uuid4())
    run = {
        "run_id": run_id,
        "chain_id": chain_id,
        "status": "running",
        "started_at": datetime.utcnow().isoformat()
    }
    runs[run_id] = run
    
    # Simulate completion after a moment
    run["status"] = "succeeded"
    run["output"] = {
        "summary": "AI is transforming industries",
        "sentiment": "positive",
        "translation": "La IA está transformando las industrias"
    }
    
    return run

@app.get("/api/chains/runs")
async def list_runs():
    demo_runs = [
        {
            "run_id": "1",
            "chain_name": "Text Processing Pipeline",
            "status": "succeeded",
            "started_at": "2025-10-31T10:30:00",
            "spent_cents": 155,
            "nodes_executed": 3
        }
    ]
    return list(runs.values()) + demo_runs

# Stripe endpoints
@app.post("/api/wallet/create-checkout-session")
async def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'GPTGram Wallet Top-Up',
                        'description': 'Add funds to your GPTGram wallet'
                    },
                    'unit_amount': 1000,  # $10.00 in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='http://localhost:3000/wallet/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:3000/wallet/cancel',
            metadata={
                'user_id': demo_user['id'],
                'type': 'wallet_topup'
            }
        )
        return {"url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/api/wallet/verify-checkout")
async def verify_checkout(session_id: str):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Update user's wallet balance
            if "demo" in users:
                users["demo"]["wallet_balance"] += session.amount_total
            
            return {
                "status": "success",
                "amount": session.amount_total,
                "balance": users.get("demo", {}).get("wallet_balance", 0)
            }
        else:
            return {"status": "pending"}
    except Exception as e:
        raise HTTPException(400, str(e))

# Mock n8n webhook endpoints for testing
@app.post("/api/mock/n8n/sentiment")
async def mock_sentiment(request: Request, data: Dict = Body(...)):
    """Mock sentiment webhook with HMAC verification"""
    # Check HMAC if provided
    signature_header = request.headers.get("X-GPTGRAM-Signature", "")
    if signature_header:
        # Verify HMAC
        pass  # For now, accept all
    
    text = data.get("text", "")
    # Simple sentiment logic for testing
    if "transform" in text.lower() or "intelligence" in text.lower():
        return {"sentiment": "positive", "score": 0.7}
    elif "error" in text.lower() or "fail" in text.lower():
        return {"sentiment": "negative", "score": -0.6}
    else:
        return {"sentiment": "neutral", "score": 0}

@app.post("/api/mock/n8n/translation")
async def mock_translation(request: Request, data: Dict = Body(...)):
    """Mock translation webhook"""
    text = data.get("text", "")
    target = data.get("target", "es")
    
    # Simple mock translations
    if target == "es":
        if "Hello world" in text:
            return {"translated": "Hola mundo", "target": "es"}
        elif "artificial intelligence" in text.lower():
            return {"translated": "inteligencia artificial", "target": "es"}
        else:
            return {"translated": f"[ES] {text}", "target": "es"}
    else:
        return {"translated": f"[{target.upper()}] {text}", "target": target}

@app.post("/api/mock/n8n/summarize")
async def mock_summarize(request: Request, data: Dict = Body(...)):
    """Mock summarization webhook"""
    text = data.get("text", "")
    max_sentences = data.get("maxSentences", 2)
    style = data.get("style", "brief")
    
    # Enhanced summary with metadata
    sentences = text.split(". ")
    if len(sentences) > max_sentences:
        summary = ". ".join(sentences[:max_sentences]) + "."
    else:
        summary = text
    
    if "artificial intelligence" in text.lower():
        summary = "AI is transforming industries worldwide by enabling machine learning algorithms to process vast amounts of data rapidly."
        key_points = ["AI transformation", "Machine learning", "Data processing"]
    else:
        key_points = ["Key point 1", "Key point 2"]
    
    return {
        "summary": summary,
        "word_count": len(summary.split()),
        "key_points": key_points,
        "style": style
    }

# Additional agent endpoints
@app.post("/api/agents/keyword")
async def extract_keywords(data: Dict = Body(...)):
    """Extract keywords from text"""
    text = data.get("text", "")
    max_keywords = data.get("max_keywords", 10)
    
    # Mock keyword extraction
    words = text.lower().split()
    keywords = list(set([w for w in words if len(w) > 4]))[:max_keywords]
    
    return {
        "keywords": keywords,
        "entities": {"persons": [], "organizations": ["OpenAI", "Google"], "locations": []},
        "topics": ["technology", "AI", "data"]
    }

@app.post("/api/agents/classify")
async def classify_content(data: Dict = Body(...)):
    """Classify content into categories"""
    text = data.get("text", "")
    
    # Mock classification
    if "artificial" in text.lower() or "technology" in text.lower():
        category = "technology"
    elif "business" in text.lower():
        category = "business"
    else:
        category = "general"
    
    return {
        "primary_category": category,
        "all_categories": [category, "science", "innovation"],
        "confidence_scores": {category: 0.85, "science": 0.65, "innovation": 0.55}
    }

@app.post("/api/agents/format")
async def format_data(data: Dict = Body(...)):
    """Format data"""
    input_data = data.get("data", {})
    format_type = data.get("format", "json")
    
    if format_type == "json":
        formatted = json.dumps(input_data, indent=2)
    elif format_type == "xml":
        formatted = "<data>formatted_xml</data>"
    else:
        formatted = str(input_data)
    
    return {
        "formatted": formatted,
        "format": format_type,
        "valid": True
    }

@app.post("/api/llm/gemini/generate")
async def gemini_generate(data: Dict = Body(...)):
    """Mock Gemini LLM generation"""
    prompt = data.get("prompt", "")
    style = data.get("style", "creative")
    
    # Mock LLM response
    content = f"Generated content based on: {prompt[:50]}... This is a creative response in {style} style."
    
    return {
        "content": content,
        "tokens_used": len(prompt.split()) * 2,
        "model": "gemini-pro"
    }

@app.post("/api/llm/openai/chat")
async def openai_chat(data: Dict = Body(...)):
    """Mock OpenAI chat"""
    message = data.get("message", "")
    role = data.get("role", "assistant")
    
    # Mock chat response
    response = f"As your {role}, I can help with: {message[:50]}... Here's my detailed response."
    
    return {
        "response": response,
        "reasoning": "Based on context analysis",
        "confidence": 0.92
    }

@app.post("/api/agents/code")
async def analyze_code(data: Dict = Body(...)):
    """Analyze code quality"""
    code = data.get("code", "")
    language = data.get("language", "python")
    
    return {
        "issues": ["Consider using type hints", "Add docstrings"],
        "suggestions": ["Optimize loop at line 10", "Extract method for readability"],
        "complexity_score": 7,
        "security_warnings": []
    }

@app.post("/api/agents/pricing")
async def calculate_pricing(data: Dict = Body(...)):
    """Calculate pricing"""
    usage = data.get("usage", 0)
    tier = data.get("tier", "basic")
    
    base_cost = {"basic": 10, "pro": 50, "enterprise": 200}[tier]
    total = base_cost + (usage * 0.01)
    
    return {
        "total_cost": total,
        "breakdown": {"base": base_cost, "usage": usage * 0.01},
        "savings": total * 0.1
    }

@app.post("/api/agents/risk")
async def assess_risk(data: Dict = Body(...)):
    """Assess risk level"""
    threshold = data.get("threshold", 0.7)
    
    score = random.uniform(0.3, 0.9)
    if score < 0.4:
        level = "low"
    elif score < 0.7:
        level = "medium"
    elif score < 0.85:
        level = "high"
    else:
        level = "critical"
    
    return {
        "risk_level": level,
        "score": score,
        "factors": ["Data quality", "Processing time", "Resource usage"],
        "recommendations": ["Monitor closely", "Set alerts"]
    }

@app.post("/api/agents/quality")
async def check_quality(data: Dict = Body(...)):
    """Check data quality"""
    strict = data.get("strict", False)
    
    score = random.uniform(0.6, 1.0) if not strict else random.uniform(0.4, 0.8)
    
    return {
        "quality_score": score,
        "passed": score >= 0.7,
        "issues": ["Missing field X"] if score < 0.8 else [],
        "suggestions": ["Add validation for field Y"]
    }

@app.get("/api/wallet/balance")
async def get_wallet_balance():
    """Get wallet balance"""
    return {"balance": 5000, "balance_cents": 500000}

@app.get("/api/wallet")
async def get_wallet():
    user = users.get("demo", demo_user)
    return {
        "balance_cents": user.get("wallet_balance", 5000),
        "currency": "usd"
    }

@app.post("/api/wallet/topup")
async def topup_wallet(amount_cents: int):
    """Simple top-up for testing without Stripe"""
    if "demo" in users:
        users["demo"]["wallet_balance"] += amount_cents
    return {
        "balance_cents": users.get("demo", {}).get("wallet_balance", 5000),
        "message": f"Added ${amount_cents/100:.2f} to wallet"
    }

@app.post("/webhooks/stripe")
async def stripe_webhook(request: dict):
    """Handle Stripe webhooks"""
    # In production, verify webhook signature
    event_type = request.get("type")
    
    if event_type == "checkout.session.completed":
        session = request.get("data", {}).get("object", {})
        user_id = session.get("metadata", {}).get("user_id")
        
        if user_id and "demo" in users:
            users["demo"]["wallet_balance"] += session.get("amount_total", 0)
    
    return {"received": True}

# Transformer endpoints for chain builder
@app.post("/api/chain/resolve-atokens")
async def resolve_atokens(request: dict):
    """Resolve @Agent.field tokens in template"""
    import re
    template = request.get("template", "")
    outputs_map = request.get("outputs_map", {})
    
    # Extract tokens
    pattern = r'@(\w+)\.([.\w\[\]]+)'
    tokens = re.findall(pattern, template)
    unresolved = []
    
    for agent, path in tokens:
        token = f"@{agent}.{path}"
        if agent in outputs_map:
            value = outputs_map[agent]
            for part in path.split('.'):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    unresolved.append(token)
                    break
            if value is not None:
                template = template.replace(token, str(value))
        else:
            unresolved.append(token)
    
    return {
        "resolved_payload": {"text": template},
        "unresolved_tokens": unresolved
    }

@app.post("/api/chain/compatibility-score")
async def compatibility_score(request: dict):
    """Calculate compatibility between agents"""
    source_output = request.get("source_sample_output", {})
    target_agent_id = request.get("target_agent_id", "")
    
    # Simple compatibility calculation
    score = 0.85  # Default high score
    if "text" in source_output or "summary" in source_output:
        score = 0.92
    
    return {
        "score": score,
        "reasons": ["Fields are compatible"],
        "suggestions": ["Direct connection possible"]
    }

@app.post("/api/chain/try-deterministic-mappings")
async def try_deterministic_mappings(request: dict):
    """Try deterministic mapping rules"""
    source_outputs = request.get("source_outputs", [])
    target_schema = request.get("target_input_schema", {})
    
    candidates = []
    for source in source_outputs:
        # Simple mapping
        result = {}
        for field in target_schema.get("required", []):
            if field in source:
                result[field] = source[field]
            elif "text" in source and field == "text":
                result[field] = source["text"]
            elif "summary" in source and field == "text":
                result[field] = source["summary"]
        
        if result:
            candidates.append({
                "payload": result,
                "score": 0.85,
                "recipe": {"mappings": [{"from": k, "to": k} for k in result]},
                "method": "deterministic"
            })
    
    return candidates

@app.get("/api/chain/recommend-agents")
async def recommend_agents(context_node_ids: list = [], top_k: int = 5):
    """Recommend compatible agents"""
    recommendations = [
        {
            "agent_id": "sentiment",
            "name": "Sentiment Analyzer",
            "compatibility_score": 0.92,
            "reasons": ["High compatibility", "Commonly used next"]
        },
        {
            "agent_id": "translator",
            "name": "Language Translator",
            "compatibility_score": 0.86,
            "reasons": ["Can process text output", "Useful for localization"]
        }
    ]
    return recommendations[:top_k]

# Chain execution endpoints
@app.post("/api/chain/execute")
async def execute_chain(request: dict):
    """Execute chain with transforms"""
    execution_log = []
    outputs = {}
    total_cost = 0
    
    for node_id in request.get("execution_order", []):
        node = next((n for n in request["nodes"] if n["id"] == node_id), None)
        if not node:
            continue
        
        # Mock execution
        if node["type"] == "transformer":
            outputs[node_id] = {"transformed": True, "method": node.get("transform_method")}
            execution_log.append({
                "node": node_id,
                "type": "transformer",
                "method": node.get("transform_method", "deterministic")
            })
            if node.get("transform_method") == "llm":
                total_cost += 15
        else:
            outputs[node_id] = {"processed": True, "agent": node.get("agent_id")}
            execution_log.append({
                "node": node_id,
                "type": "agent",
                "agent_id": node.get("agent_id")
            })
            total_cost += 50
    
    return {
        "execution_id": f"exec-{int(time.time())}",
        "status": "success",
        "outputs": outputs,
        "total_cost": total_cost,
        "execution_log": execution_log
    }

@app.post("/api/chain/save")
async def save_chain(request: dict):
    """Save chain configuration"""
    chain_id = f"chain-{int(time.time())}"
    chains[chain_id] = request
    return {"chain_id": chain_id, "status": "saved"}

@app.post("/api/wallet/deduct")
async def deduct_wallet(request: dict):
    """Deduct from wallet balance"""
    amount = request.get("amount_cents", 0)
    if "demo" in users:
        users["demo"]["wallet_balance"] = max(0, users["demo"]["wallet_balance"] - amount)
    return {"new_balance": users["demo"]["wallet_balance"]}

@app.post("/api/analytics/save-run")
async def save_analytics(request: dict):
    """Save run to analytics"""
    # Update mock analytics data
    return {"status": "saved"}

@app.get("/api/analytics/data")
async def get_analytics():
    """Get analytics data"""
    return {
        "total_runs": len(runs_db),
        "total_llm_calls": random.randint(100, 1000),
        "total_cost": random.randint(500, 5000),
        "total_agents": len(agents_db),
        "agents": len(agents_db),
        "chains": len(runs_db),
        "runs": runs_db[:5],  # Last 5 runs
        "agents_by_type": {
            "n8n": 3,
            "custom": 2,
            "prompt": 1
        },
        "success_rate": 95.2,
        "transform_methods": {
            "deterministic": 45,
            "gat": 30,
            "llm": 25
        },
        "revenue_over_time": [
            {"date": "2025-10-25", "revenue": 2500},
            {"date": "2025-10-26", "revenue": 3200},
            {"date": "2025-10-27", "revenue": 2800},
            {"date": "2025-10-28", "revenue": 3500},
            {"date": "2025-10-29", "revenue": 4200},
            {"date": "2025-10-30", "revenue": 3800},
            {"date": "2025-10-31", "revenue": 4500}
        ],
        "agent_performance": [
            {"name": "Summarizer", "runs": 150, "success_rate": 98},
            {"name": "Sentiment", "runs": 120, "success_rate": 95},
            {"name": "Translator", "runs": 100, "success_rate": 92}
        ]
    }

# Include transformer router if available
if transformer_router:
    app.include_router(transformer_router)

# Include prompt agent router if available
if prompt_agent_router:
    app.include_router(prompt_agent_router)

# Compatibility check endpoint
@app.get("/api/agents/compatibility-check")
async def check_compatibility(upstream_id: str, downstream_id: str):
    """Check agent compatibility"""
    # Simple mock implementation
    compatibility_score = 0.85 if upstream_id == "summarizer" and downstream_id == "sentiment" else 0.65
    
    return {
        "compatibility": {
            "compatibility_score": compatibility_score,
            "missing_fields": [],
            "type_mismatches": [],
            "extra_fields": ["summary"] if upstream_id == "summarizer" else []
        },
        "recommendation": "Direct connection" if compatibility_score > 0.8 else "Use moderator",
        "needs_moderator": compatibility_score < 0.8
    }

# Include enhanced APIs if available
if agents_router:
    app.include_router(agents_router)
    
# Use fixed moderator
if moderator_fixed_router:
    app.include_router(moderator_fixed_router)

# Include run history router if available
if run_router:
    app.include_router(run_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
