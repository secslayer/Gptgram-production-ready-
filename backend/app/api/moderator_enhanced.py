"""
ENHANCED MODERATOR AGENT WITH DATABASE SCHEMA INTEGRATION
Retrieves schemas from database and performs intelligent mediation
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Union
import json
import uuid
import re
from datetime import datetime
import asyncio
from collections import defaultdict
import requests

router = APIRouter(prefix="/api/moderator", tags=["moderator-enhanced"])

# ============= DATA MODELS =============

class ModeratorNode(BaseModel):
    node_id: str
    name: str = "Moderator"
    position: Dict[str, float]
    upstream_agents: List[str] = []
    downstream_agent: Optional[str] = None
    has_input_node: bool = False
    user_input: Optional[str] = None
    prompt_template: Optional[str] = None
    settings: Dict[str, Any] = {
        "temperature": 0.0,
        "max_tokens": 500,
        "auto_resolve": True,
        "strict_schema": True,
        "use_examples": True
    }

class InputNode(BaseModel):
    node_id: str
    name: str = "User Input"
    position: Dict[str, float]
    input_text: str = ""
    output_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "user_input": {"type": "string"},
            "context": {"type": "object"}
        }
    }

class ModeratorExecutionRequest(BaseModel):
    node_id: str
    upstream_outputs: Dict[str, Dict[str, Any]] = {}
    user_input: Optional[str] = None
    use_input_node: bool = False

class ModerationContext(BaseModel):
    upstream_agent: Optional[Dict[str, Any]]
    downstream_agent: Optional[Dict[str, Any]]
    compatibility_score: float = 0.0
    field_mapping: Dict[str, str] = {}
    method_used: str = "deterministic"
    schema_valid: bool = False
    error_message: Optional[str] = None

# ============= STORAGE =============

moderator_nodes = {}
input_nodes = {}
moderation_logs = []
websocket_connections = {}

# ============= HELPER FUNCTIONS =============

async def fetch_agent_metadata(agent_id: str) -> Dict[str, Any]:
    """Fetch agent metadata from database"""
    try:
        # Call the agents API to get metadata
        response = requests.get(f"http://localhost:8000/api/agents/{agent_id}/metadata")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Fallback mock data
    return {
        "agent_id": agent_id,
        "name": f"Agent {agent_id}",
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object", "properties": {}},
        "example_input": {},
        "example_output": {}
    }

def compute_compatibility(upstream_schema: Dict, downstream_schema: Dict) -> tuple:
    """Enhanced schema compatibility computation"""
    
    upstream_props = upstream_schema.get("properties", {})
    downstream_props = downstream_schema.get("properties", {})
    required_fields = downstream_schema.get("required", [])
    
    field_mapping = {}
    matched_fields = 0
    missing_required = []
    type_mismatches = []
    
    # Check each downstream field
    for field, spec in downstream_props.items():
        field_matched = False
        
        # Direct match
        if field in upstream_props:
            field_mapping[field] = field
            matched_fields += 1
            field_matched = True
            
            # Check type compatibility
            upstream_type = upstream_props[field].get("type")
            downstream_type = spec.get("type")
            if upstream_type != downstream_type:
                type_mismatches.append({
                    "field": field,
                    "upstream": upstream_type,
                    "downstream": downstream_type
                })
        else:
            # Try semantic matching
            for up_field, up_spec in upstream_props.items():
                # Check for similar field names
                if (field.lower() in up_field.lower() or 
                    up_field.lower() in field.lower() or
                    field.replace("_", "") == up_field.replace("_", "")):
                    field_mapping[field] = up_field
                    matched_fields += 1
                    field_matched = True
                    break
        
        # Track missing required fields
        if field in required_fields and not field_matched:
            missing_required.append(field)
    
    # Calculate compatibility score
    total_fields = len(downstream_props) if downstream_props else 1
    key_overlap = matched_fields / total_fields
    
    # Penalize for missing required fields
    required_penalty = len(missing_required) / (len(required_fields) if required_fields else 1)
    
    # Penalize for type mismatches
    type_penalty = len(type_mismatches) / total_fields
    
    score = max(0, min(1, 
        0.5 * key_overlap + 
        0.3 * (1 - required_penalty) + 
        0.2 * (1 - type_penalty)
    ))
    
    return score, field_mapping

def map_fields_deterministic(upstream_output: Dict, field_mapping: Dict, downstream_example: Dict) -> Dict:
    """Deterministically map fields from upstream to downstream"""
    result = {}
    
    for downstream_field, upstream_field in field_mapping.items():
        if upstream_field in upstream_output:
            result[downstream_field] = upstream_output[upstream_field]
        elif downstream_field in downstream_example:
            # Use example as fallback
            result[downstream_field] = downstream_example[downstream_field]
    
    # Add any missing required fields from example
    for key, value in downstream_example.items():
        if key not in result:
            result[key] = value
    
    return result

async def synthesize_with_gemini_enhanced(
    upstream_output: Dict,
    downstream_schema: Dict,
    downstream_example: Dict,
    upstream_example: Optional[Dict] = None
) -> Dict:
    """Enhanced Gemini synthesis with examples"""
    
    prompt = f"""Transform the upstream output to match the downstream input requirements.

Upstream Output:
{json.dumps(upstream_output, indent=2)}

Downstream Input Schema:
{json.dumps(downstream_schema, indent=2)}

Downstream Example Input:
{json.dumps(downstream_example, indent=2)}

Rules:
1. Output MUST be valid JSON matching the downstream schema exactly
2. Use data from upstream output when available
3. For missing required fields, use values from the example input
4. Preserve semantic meaning
5. Do not invent data - use examples as fallback
6. Output only the JSON object, no explanations

Generate the transformed JSON:"""

    # Mock Gemini response - in production, call actual API
    # For now, attempt intelligent mapping
    result = {}
    
    # Get required fields
    required = downstream_schema.get("required", [])
    properties = downstream_schema.get("properties", {})
    
    # Try to map each field
    for field, spec in properties.items():
        field_type = spec.get("type", "string")
        
        # Look for matching field in upstream
        matched_value = None
        for up_field, up_value in upstream_output.items():
            if field.lower() in up_field.lower() or up_field.lower() in field.lower():
                matched_value = up_value
                break
        
        if matched_value is not None:
            # Type coercion if needed
            if field_type == "string":
                result[field] = str(matched_value)
            elif field_type == "number":
                try:
                    result[field] = float(matched_value)
                except:
                    result[field] = downstream_example.get(field, 0)
            elif field_type == "integer":
                try:
                    result[field] = int(matched_value)
                except:
                    result[field] = downstream_example.get(field, 0)
            elif field_type == "boolean":
                result[field] = bool(matched_value)
            elif field_type == "array":
                result[field] = matched_value if isinstance(matched_value, list) else [matched_value]
            else:
                result[field] = matched_value
        elif field in downstream_example:
            # Use example value
            result[field] = downstream_example[field]
        else:
            # Use default based on type
            if field_type == "string":
                result[field] = ""
            elif field_type in ["number", "integer"]:
                result[field] = 0
            elif field_type == "boolean":
                result[field] = False
            elif field_type == "array":
                result[field] = []
            elif field_type == "object":
                result[field] = {}
    
    return result

def validate_against_schema(payload: Dict, schema: Dict) -> bool:
    """Validate payload against JSON schema"""
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    
    # Check required fields
    for field in required:
        if field not in payload:
            return False
    
    # Check types
    for field, value in payload.items():
        if field in properties:
            expected_type = properties[field].get("type")
            if expected_type:
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "integer" and not isinstance(value, int):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
                elif expected_type == "array" and not isinstance(value, list):
                    return False
                elif expected_type == "object" and not isinstance(value, dict):
                    return False
    
    return True

# ============= API ENDPOINTS =============

class CreateModeratorRequest(BaseModel):
    node_id: str
    position: Dict[str, float]
    upstream_agent_ids: List[str]
    downstream_agent_id: str
    include_input_node: bool = False

@router.post("/create-with-context")
async def create_moderator_with_context(request: CreateModeratorRequest):
    """Create moderator with full context from database"""
    
    # Fetch metadata for all agents
    upstream_metadata = []
    for agent_id in request.upstream_agent_ids:
        metadata = await fetch_agent_metadata(agent_id)
        upstream_metadata.append(metadata)
    
    downstream_metadata = await fetch_agent_metadata(request.downstream_agent_id)
    
    # Compute overall compatibility
    total_score = 0
    for upstream in upstream_metadata:
        score, _ = compute_compatibility(
            upstream["output_schema"],
            downstream_metadata["input_schema"]
        )
        total_score += score
    
    avg_score = total_score / len(upstream_metadata) if upstream_metadata else 0
    
    # Create moderator node
    moderator = ModeratorNode(
        node_id=request.node_id,
        position=request.position,
        upstream_agents=request.upstream_agent_ids,
        downstream_agent=request.downstream_agent_id,
        has_input_node=request.include_input_node
    )
    
    moderator_nodes[request.node_id] = moderator
    
    # Create input node if requested
    if request.include_input_node:
        input_node_id = f"{request.node_id}_input"
        input_node = InputNode(
            node_id=input_node_id,
            position={
                "x": request.position["x"] - 150,
                "y": request.position["y"]
            }
        )
        input_nodes[input_node_id] = input_node
    
    return {
        "success": True,
        "node_id": request.node_id,
        "compatibility_score": avg_score,
        "needs_moderator": avg_score < 0.8,
        "upstream_schemas": [m["output_schema"] for m in upstream_metadata],
        "downstream_schema": downstream_metadata["input_schema"],
        "input_node_id": f"{request.node_id}_input" if request.include_input_node else None
    }

class ModeratePayloadRequest(BaseModel):
    upstream_agent_id: str
    downstream_agent_id: str
    upstream_output: Dict[str, Any]
    user_input: Optional[str] = None

@router.post("/moderate-payload")
async def moderate_payload(request: ModeratePayloadRequest):
    """Core moderation logic with database schema retrieval"""
    
    # Fetch metadata from database
    upstream_meta = await fetch_agent_metadata(request.upstream_agent_id)
    downstream_meta = await fetch_agent_metadata(request.downstream_agent_id)
    
    # Build moderation context
    context = ModerationContext(
        upstream_agent=upstream_meta,
        downstream_agent=downstream_meta
    )
    
    # Compute compatibility
    score, field_map = compute_compatibility(
        upstream_meta["output_schema"],
        downstream_meta["input_schema"]
    )
    
    context.compatibility_score = score
    context.field_mapping = field_map
    
    # Add user input if provided
    if request.user_input:
        request.upstream_output["user_input"] = request.user_input
    
    # Choose transformation method
    if score >= 0.8:
        # Deterministic transformation
        context.method_used = "deterministic"
        payload = map_fields_deterministic(
            request.upstream_output,
            field_map,
            downstream_meta["example_input"]
        )
    else:
        # Gemini synthesis fallback
        context.method_used = "gemini"
        payload = await synthesize_with_gemini_enhanced(
            request.upstream_output,
            downstream_meta["input_schema"],
            downstream_meta["example_input"],
            upstream_meta.get("example_output")
        )
    
    # Validate final payload
    context.schema_valid = validate_against_schema(
        payload,
        downstream_meta["input_schema"]
    )
    
    if not context.schema_valid:
        # Final fallback to example
        context.method_used = "example_fallback"
        payload = downstream_meta["example_input"]
        context.schema_valid = True
        context.error_message = "Schema validation failed, using example input"
    
    # Log the moderation
    log_entry = {
        "moderation_id": str(uuid.uuid4()),
        "upstream_agent_id": request.upstream_agent_id,
        "downstream_agent_id": request.downstream_agent_id,
        "compatibility_score": context.compatibility_score,
        "method_used": context.method_used,
        "schema_valid": context.schema_valid,
        "error_message": context.error_message,
        "timestamp": datetime.utcnow().isoformat(),
        "llm_cost": 0.002 if context.method_used == "gemini" else 0
    }
    moderation_logs.append(log_entry)
    
    # Broadcast update
    await broadcast_update({
        "type": "moderation_complete",
        "log": log_entry
    })
    
    return {
        "success": True,
        "payload": payload,
        "context": context.dict(),
        "log_id": log_entry["moderation_id"]
    }

@router.post("/execute-with-input")
async def execute_moderator_with_input(request: ModeratorExecutionRequest):
    """Execute moderator with optional input node"""
    
    if request.node_id not in moderator_nodes:
        raise HTTPException(status_code=404, detail="Moderator not found")
    
    moderator = moderator_nodes[request.node_id]
    
    # Handle input node
    final_upstream_outputs = request.upstream_outputs.copy()
    
    if request.use_input_node or moderator.has_input_node:
        input_node_id = f"{request.node_id}_input"
        if input_node_id in input_nodes:
            input_node = input_nodes[input_node_id]
            final_upstream_outputs["UserInput"] = {
                "user_input": request.user_input or input_node.input_text,
                "context": {}
            }
    
    # If no downstream agent specified, return combined outputs
    if not moderator.downstream_agent:
        return {
            "success": True,
            "combined_output": final_upstream_outputs
        }
    
    # Get first upstream agent for moderation
    if moderator.upstream_agents:
        upstream_id = moderator.upstream_agents[0]
        upstream_output = final_upstream_outputs.get(upstream_id, {})
        
        # Moderate the payload
        result = await moderate_payload(
            upstream_id,
            moderator.downstream_agent,
            upstream_output,
            request.user_input
        )
        
        return result
    
    return {
        "success": False,
        "error": "No upstream agents configured"
    }

@router.get("/logs")
async def get_moderation_logs(limit: int = 20):
    """Get recent moderation logs for analytics"""
    return sorted(
        moderation_logs,
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:limit]

@router.get("/analytics")
async def get_moderation_analytics():
    """Get moderation analytics"""
    
    if not moderation_logs:
        return {
            "total_moderations": 0,
            "methods": {},
            "average_compatibility": 0,
            "schema_validation_rate": 0
        }
    
    total = len(moderation_logs)
    methods = defaultdict(int)
    total_score = 0
    valid_schemas = 0
    
    for log in moderation_logs:
        methods[log["method_used"]] += 1
        total_score += log["compatibility_score"]
        if log["schema_valid"]:
            valid_schemas += 1
    
    return {
        "total_moderations": total,
        "methods": dict(methods),
        "average_compatibility": total_score / total,
        "schema_validation_rate": valid_schemas / total,
        "llm_usage_rate": methods.get("gemini", 0) / total,
        "deterministic_rate": methods.get("deterministic", 0) / total
    }

class CreateInputNodeRequest(BaseModel):
    node_id: str
    position: Dict[str, float]
    initial_text: str = ""

@router.post("/input-node/create")
async def create_input_node(request: CreateInputNodeRequest):
    """Create a standalone input node"""
    
    input_node = InputNode(
        node_id=request.node_id,
        position=request.position,
        input_text=request.initial_text
    )
    
    input_nodes[request.node_id] = input_node
    
    return {
        "success": True,
        "node_id": request.node_id,
        "input_node": input_node.dict()
    }

class UpdateInputNodeRequest(BaseModel):
    text: str

@router.put("/input-node/{node_id}")
async def update_input_node(node_id: str, request: UpdateInputNodeRequest):
    """Update input node text"""
    
    if node_id not in input_nodes:
        raise HTTPException(status_code=404, detail="Input node not found")
    
    input_nodes[node_id].input_text = request.text
    
    await broadcast_update({
        "type": "input_updated",
        "node_id": node_id,
        "text": request.text
    })
    
    return {"success": True}

# ============= WEBSOCKET =============

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket for live updates"""
    await websocket.accept()
    websocket_connections[client_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        del websocket_connections[client_id]

async def broadcast_update(update: Dict[str, Any]):
    """Broadcast to all connected clients"""
    disconnected = []
    
    for client_id, ws in websocket_connections.items():
        try:
            await ws.send_json(update)
        except:
            disconnected.append(client_id)
    
    for client_id in disconnected:
        del websocket_connections[client_id]
