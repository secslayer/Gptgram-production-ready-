"""
ENHANCED AGENTS API WITH SCHEMA STORAGE
Stores input/output schemas and examples in database for Moderator Agent use
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid

router = APIRouter(prefix="/api/agents", tags=["agents"])

# ============= DATA MODELS =============

class AgentCreateRequest(BaseModel):
    name: str
    description: str
    type: str = Field(default="custom", pattern="^(custom|n8n|api)$")
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    example_input: Dict[str, Any]
    example_output: Dict[str, Any]
    webhook_url: Optional[str] = None
    price_cents: int = Field(default=10, ge=0)
    category: str = Field(default="general")
    tags: List[str] = []

class AgentMetadata(BaseModel):
    agent_id: str
    name: str
    alias: str
    description: str
    type: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    example_input: Dict[str, Any]
    example_output: Dict[str, Any]
    verification_level: str = "L1"
    owner_id: str
    webhook_url: Optional[str] = None
    price_cents: int
    category: str
    tags: List[str]
    created_at: str
    updated_at: str
    active: bool = True
    execution_count: int = 0
    success_rate: float = 100.0
    average_latency_ms: int = 0

# ============= STORAGE =============

agents_db = {}
agent_executions = []

# Pre-populated agents for testing
def initialize_agents():
    """Initialize with some default agents"""
    default_agents = [
        {
            "agent_id": "summarizer",
            "name": "Text Summarizer",
            "alias": "Summarizer",
            "description": "Summarizes text into key points",
            "type": "n8n",
            "input_schema": {
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {"type": "string", "description": "Text to summarize"},
                    "max_sentences": {"type": "integer", "default": 3}
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "sentences": {"type": "array", "items": {"type": "string"}},
                    "key_points": {"type": "array", "items": {"type": "string"}}
                }
            },
            "example_input": {
                "text": "Artificial intelligence is transforming industries worldwide...",
                "max_sentences": 3
            },
            "example_output": {
                "summary": "AI is transforming industries worldwide.",
                "sentences": ["AI is transforming industries.", "It enables automation.", "The future is AI-driven."],
                "key_points": ["Industry transformation", "Automation", "AI-driven future"]
            },
            "webhook_url": "https://n8n.gptgram.ai/webhook/summarizer",
            "verification_level": "L3",
            "owner_id": "system",
            "price_cents": 10,
            "category": "text",
            "tags": ["nlp", "summarization"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "agent_id": "sentiment",
            "name": "Sentiment Analyzer",
            "alias": "Sentiment",
            "description": "Analyzes sentiment of text",
            "type": "n8n",
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
                    "score": {"type": "number", "minimum": 0, "maximum": 1},
                    "confidence": {"type": "number"}
                }
            },
            "example_input": {
                "text": "This product is amazing! I love it."
            },
            "example_output": {
                "sentiment": "positive",
                "score": 0.92,
                "confidence": 0.95
            },
            "webhook_url": "https://n8n.gptgram.ai/webhook/sentiment",
            "verification_level": "L3",
            "owner_id": "system",
            "price_cents": 15,
            "category": "analysis",
            "tags": ["nlp", "sentiment"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "agent_id": "translator",
            "name": "Language Translator",
            "alias": "Translator",
            "description": "Translates text between languages",
            "type": "n8n",
            "input_schema": {
                "type": "object",
                "required": ["text", "target_language"],
                "properties": {
                    "text": {"type": "string"},
                    "target_language": {"type": "string", "enum": ["es", "fr", "de", "ja", "zh"]}
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "translated_text": {"type": "string"},
                    "source_language": {"type": "string"},
                    "target_language": {"type": "string"}
                }
            },
            "example_input": {
                "text": "Hello world",
                "target_language": "es"
            },
            "example_output": {
                "translated_text": "Hola mundo",
                "source_language": "en",
                "target_language": "es"
            },
            "webhook_url": "https://n8n.gptgram.ai/webhook/translator",
            "verification_level": "L2",
            "owner_id": "system",
            "price_cents": 20,
            "category": "translation",
            "tags": ["nlp", "translation"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    for agent_data in default_agents:
        agent = AgentMetadata(**agent_data)
        agents_db[agent.agent_id] = agent
        
initialize_agents()

# ============= HELPER FUNCTIONS =============

def generate_agent_alias(name: str) -> str:
    """Generate alias from agent name"""
    return ''.join(word.capitalize() for word in name.split())

def validate_json_schema(schema: Dict[str, Any]) -> bool:
    """Validate if the provided schema is a valid JSON Schema"""
    required_fields = ["type"]
    if not all(field in schema for field in required_fields):
        return False
    
    if schema["type"] == "object" and "properties" not in schema:
        return False
    
    return True

def compute_schema_compatibility(output_schema: Dict, input_schema: Dict) -> tuple:
    """Compute compatibility score between two schemas"""
    if not output_schema or not input_schema:
        return 0.0, {}
    
    output_props = output_schema.get("properties", {})
    input_props = input_schema.get("properties", {})
    required_fields = input_schema.get("required", [])
    
    field_mapping = {}
    matched_fields = 0
    total_fields = len(required_fields) if required_fields else len(input_props)
    
    if total_fields == 0:
        return 1.0, {}
    
    # Direct field matching
    for input_field, input_spec in input_props.items():
        if input_field in output_props:
            field_mapping[input_field] = input_field
            matched_fields += 1
        else:
            # Try fuzzy matching
            for output_field in output_props:
                if input_field.lower() in output_field.lower() or output_field.lower() in input_field.lower():
                    field_mapping[input_field] = output_field
                    matched_fields += 1
                    break
    
    # Check required fields
    missing_required = [f for f in required_fields if f not in field_mapping]
    
    # Calculate score
    key_overlap = matched_fields / total_fields
    type_match = 1.0  # Simplified for now
    semantic_similarity = 0.8 if len(missing_required) == 0 else 0.5
    
    score = 0.6 * key_overlap + 0.2 * type_match + 0.2 * semantic_similarity
    
    return score, field_mapping

# ============= API ENDPOINTS =============

@router.post("/create")
async def create_agent(request: AgentCreateRequest):
    """Create a new agent with full schema metadata"""
    
    # Validate schemas
    if not validate_json_schema(request.input_schema):
        raise HTTPException(status_code=400, detail="Invalid input schema")
    if not validate_json_schema(request.output_schema):
        raise HTTPException(status_code=400, detail="Invalid output schema")
    
    agent_id = str(uuid.uuid4())
    alias = generate_agent_alias(request.name)
    
    agent = AgentMetadata(
        agent_id=agent_id,
        name=request.name,
        alias=alias,
        description=request.description,
        type=request.type,
        input_schema=request.input_schema,
        output_schema=request.output_schema,
        example_input=request.example_input,
        example_output=request.example_output,
        webhook_url=request.webhook_url,
        verification_level="L1",
        owner_id=f"user_{uuid.uuid4().hex[:8]}",  # Mock user ID
        price_cents=request.price_cents,
        category=request.category,
        tags=request.tags,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    
    agents_db[agent_id] = agent
    
    return {
        "success": True,
        "agent_id": agent_id,
        "agent": agent.dict()
    }

@router.get("/")
async def list_agents(category: Optional[str] = None, active: bool = True):
    """List all agents with optional filtering"""
    agents = list(agents_db.values())
    
    if category:
        agents = [a for a in agents if a.category == category]
    
    if active is not None:
        agents = [a for a in agents if a.active == active]
    
    return [agent.dict() for agent in agents]

@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agents_db[agent_id].dict()

@router.get("/{agent_id}/metadata")
async def get_agent_metadata(agent_id: str):
    """Get agent metadata for schema validation"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents_db[agent_id]
    
    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "alias": agent.alias,
        "input_schema": agent.input_schema,
        "output_schema": agent.output_schema,
        "example_input": agent.example_input,
        "example_output": agent.example_output,
        "verification_level": agent.verification_level
    }

@router.put("/{agent_id}")
async def update_agent(agent_id: str, update_data: Dict[str, Any]):
    """Update agent configuration"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents_db[agent_id]
    
    # Update allowed fields
    allowed_fields = ["name", "description", "webhook_url", "price_cents", "tags", "active"]
    for field in allowed_fields:
        if field in update_data:
            setattr(agent, field, update_data[field])
    
    # Update schemas if provided
    if "input_schema" in update_data:
        if validate_json_schema(update_data["input_schema"]):
            agent.input_schema = update_data["input_schema"]
    
    if "output_schema" in update_data:
        if validate_json_schema(update_data["output_schema"]):
            agent.output_schema = update_data["output_schema"]
    
    agent.updated_at = datetime.utcnow().isoformat()
    agents_db[agent_id] = agent
    
    return {"success": True, "agent": agent.dict()}

@router.post("/{agent_id}/verify")
async def verify_agent(agent_id: str):
    """Verify an agent and update its verification level"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents_db[agent_id]
    
    # Mock verification process
    # In production, this would run actual tests
    if agent.verification_level == "L1":
        agent.verification_level = "L2"
    elif agent.verification_level == "L2":
        agent.verification_level = "L3"
    
    agent.updated_at = datetime.utcnow().isoformat()
    agents_db[agent_id] = agent
    
    return {
        "success": True,
        "agent_id": agent_id,
        "verification_level": agent.verification_level
    }

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents_db.pop(agent_id)
    
    return {
        "success": True,
        "agent_id": agent_id,
        "message": f"Agent '{agent.name}' deleted successfully"
    }

@router.post("/compatibility-check")
async def check_compatibility(upstream_id: str, downstream_id: str):
    """Check compatibility between two agents"""
    
    if upstream_id not in agents_db:
        raise HTTPException(status_code=404, detail=f"Upstream agent {upstream_id} not found")
    if downstream_id not in agents_db:
        raise HTTPException(status_code=404, detail=f"Downstream agent {downstream_id} not found")
    
    upstream = agents_db[upstream_id]
    downstream = agents_db[downstream_id]
    
    score, field_mapping = compute_schema_compatibility(
        upstream.output_schema,
        downstream.input_schema
    )
    
    return {
        "upstream_agent": upstream.name,
        "downstream_agent": downstream.name,
        "compatibility_score": score,
        "field_mapping": field_mapping,
        "needs_moderator": score < 0.8,
        "recommendation": "Direct connection" if score >= 0.8 else "Insert Moderator"
    }

@router.post("/{agent_id}/execute")
async def execute_agent(agent_id: str, payload: Dict[str, Any]):
    """Execute an agent with the given payload"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents_db[agent_id]
    
    # Mock execution - in production, this would call the actual webhook
    execution_result = {
        "execution_id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "status": "success",
        "input": payload,
        "output": agent.example_output,  # Mock with example
        "latency_ms": 150,
        "cost_cents": agent.price_cents,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Update agent metrics
    agent.execution_count += 1
    agent.average_latency_ms = 150
    
    agent_executions.append(execution_result)
    
    return execution_result

@router.get("/executions/history")
async def get_execution_history(limit: int = 20):
    """Get recent agent executions"""
    return sorted(
        agent_executions,
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:limit]
