"""
MODERATOR AGENT SYSTEM
Intelligent input/output mediator for React Flow chains
Replaces Custom Prompt Agent with embedded node functionality

Features:
- Live user input acceptance
- @AgentName.field token resolution
- Schema mismatch detection and correction
- Gemini LLM integration for synthesis
- Full audit trail and cost tracking
- Duplicatable and placeable anywhere in chain
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

router = APIRouter(prefix="/api/moderator", tags=["moderator-agent"])

# ============= DATA MODELS =============

class ModeratorNode(BaseModel):
    node_id: str
    name: str = "Moderator"
    position: Dict[str, float]  # {x, y} in React Flow
    prompt_template: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    upstream_agents: List[str] = []  # List of connected agent IDs
    settings: Dict[str, Any] = {
        "temperature": 0.0,
        "max_tokens": 500,
        "auto_resolve": True,
        "strict_schema": True
    }

class ModeratorExecutionRequest(BaseModel):
    node_id: str
    user_input: Optional[str] = None
    upstream_outputs: Dict[str, Dict[str, Any]] = {}
    context: Optional[Dict[str, Any]] = {}

class SchemaAlignmentRequest(BaseModel):
    source_output: Dict[str, Any]
    target_input_schema: Dict[str, Any]
    moderator_prompt: Optional[str] = None

class ModeratorState(BaseModel):
    execution_id: str
    node_id: str
    status: str  # 'pending', 'processing', 'success', 'failed'
    input_received: Dict[str, Any]
    upstream_references: List[str]
    gemini_prompt: Optional[str] = None
    output_generated: Optional[Dict[str, Any]] = None
    compatibility_score: float = 0.0
    cost_cents: int = 0
    error_message: Optional[str] = None
    timestamp: str

# ============= STORAGE =============

moderator_nodes = {}
moderator_executions = []
websocket_connections = {}
schema_alignment_cache = {}

# ============= HELPER FUNCTIONS =============

def extract_agent_tokens(template: str) -> List[Dict[str, str]]:
    """Extract all @AgentName.field tokens from template"""
    pattern = r'@([\w]+)(?:\.([\w\[\]\.]+))?'
    tokens = []
    
    for match in re.finditer(pattern, template):
        agent = match.group(1)
        field = match.group(2) if match.group(2) else None
        tokens.append({
            'token': match.group(0),
            'agent': agent,
            'field': field,
            'full_path': f"{agent}.{field}" if field else agent
        })
    
    return tokens

def resolve_token_path(agent_name: str, field_path: Optional[str], outputs: Dict[str, Dict]) -> Any:
    """Resolve @Agent.field.path to actual value"""
    if agent_name not in outputs:
        raise ValueError(f"Agent '{agent_name}' not found in outputs")
    
    data = outputs[agent_name]
    
    if not field_path:
        return data
    
    # Parse path supporting dots and brackets
    parts = re.split(r'\.|\[|\]', field_path)
    parts = [p for p in parts if p]
    
    current = data
    for part in parts:
        if part.isdigit():
            current = current[int(part)]
        else:
            current = current[part]
    
    return current

def detect_schema_mismatch(output: Dict[str, Any], input_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Detect mismatches between output and expected input schema"""
    mismatches = {
        'missing_fields': [],
        'type_mismatches': [],
        'extra_fields': [],
        'compatibility_score': 0.0,
        'needs_moderator': False
    }
    
    required = input_schema.get('required', [])
    properties = input_schema.get('properties', {})
    
    # Check required fields
    for field in required:
        if field not in output:
            mismatches['missing_fields'].append(field)
    
    # Check type matches
    for field, schema in properties.items():
        if field in output:
            expected_type = schema.get('type')
            actual_value = output[field]
            
            if not validate_type(actual_value, expected_type):
                mismatches['type_mismatches'].append({
                    'field': field,
                    'expected': expected_type,
                    'actual': type(actual_value).__name__
                })
    
    # Check extra fields
    for field in output:
        if field not in properties:
            mismatches['extra_fields'].append(field)
    
    # Calculate compatibility score
    total_checks = len(required) + len(properties)
    issues = len(mismatches['missing_fields']) + len(mismatches['type_mismatches'])
    
    if total_checks > 0:
        mismatches['compatibility_score'] = max(0, 1 - (issues / total_checks))
    else:
        mismatches['compatibility_score'] = 1.0
    
    mismatches['needs_moderator'] = mismatches['compatibility_score'] < 0.85
    
    return mismatches

def validate_type(value: Any, expected_type: str) -> bool:
    """Validate if value matches expected JSON Schema type"""
    type_map = {
        'string': str,
        'number': (int, float),
        'integer': int,
        'boolean': bool,
        'array': list,
        'object': dict
    }
    
    expected = type_map.get(expected_type)
    if not expected:
        return True
    
    return isinstance(value, expected)

async def synthesize_with_gemini(
    source_data: Dict[str, Any],
    target_schema: Dict[str, Any],
    moderator_prompt: Optional[str] = None,
    temperature: float = 0.0
) -> Dict[str, Any]:
    """Use Gemini to synthesize compatible output"""
    
    # Build the synthesis prompt
    system_prompt = f"""You are a data synthesis moderator. Your job is to transform input data to match a target schema.

Target Schema:
{json.dumps(target_schema, indent=2)}

Rules:
1. Output MUST be valid JSON matching the target schema exactly
2. Use ONLY information from the source data - do not invent facts
3. If a required field cannot be derived, use reasonable defaults or null
4. Maintain data integrity and relationships
5. Output ONLY the JSON object, no explanations

{moderator_prompt if moderator_prompt else ''}

Source Data:
{json.dumps(source_data, indent=2)}

Generate the output JSON:"""

    # Mock Gemini response for now
    # In production: call actual Gemini API with temperature=0
    
    # Attempt to map fields intelligently
    result = {}
    required = target_schema.get('required', [])
    properties = target_schema.get('properties', {})
    
    for field in required:
        prop_schema = properties.get(field, {})
        field_type = prop_schema.get('type', 'string')
        
        # Try to find matching field in source
        matched_value = None
        
        # Direct match
        if field in source_data:
            matched_value = source_data[field]
        else:
            # Try fuzzy matching
            for src_field, src_value in source_data.items():
                if field.lower() in src_field.lower() or src_field.lower() in field.lower():
                    matched_value = src_value
                    break
        
        # Set value with type coercion
        if matched_value is not None:
            if field_type == 'string':
                result[field] = str(matched_value)
            elif field_type in ['number', 'integer']:
                try:
                    result[field] = float(matched_value) if field_type == 'number' else int(matched_value)
                except:
                    result[field] = 0
            elif field_type == 'boolean':
                result[field] = bool(matched_value)
            elif field_type == 'array':
                result[field] = matched_value if isinstance(matched_value, list) else [matched_value]
            elif field_type == 'object':
                result[field] = matched_value if isinstance(matched_value, dict) else {}
        else:
            # Use defaults
            if field_type == 'string':
                result[field] = ""
            elif field_type in ['number', 'integer']:
                result[field] = 0
            elif field_type == 'boolean':
                result[field] = False
            elif field_type == 'array':
                result[field] = []
            elif field_type == 'object':
                result[field] = {}
    
    # Calculate cost (mock)
    tokens_used = len(json.dumps(source_data)) // 4 + len(json.dumps(result)) // 4
    cost_cents = max(10, tokens_used // 10)
    
    return {
        'output': result,
        'tokens_used': tokens_used,
        'cost_cents': cost_cents,
        'gemini_prompt': system_prompt[:500] + '...',
        'success': True
    }

# ============= API ENDPOINTS =============

@router.post("/create")
async def create_moderator_node(node: ModeratorNode):
    """Create a new moderator node in the chain"""
    moderator_nodes[node.node_id] = node
    
    return {
        'status': 'created',
        'node_id': node.node_id,
        'name': node.name,
        'position': node.position
    }

@router.get("/nodes")
async def list_moderator_nodes():
    """List all moderator nodes in current chain"""
    return list(moderator_nodes.values())

@router.get("/node/{node_id}")
async def get_moderator_node(node_id: str):
    """Get specific moderator node details"""
    if node_id not in moderator_nodes:
        raise HTTPException(status_code=404, detail="Moderator node not found")
    return moderator_nodes[node_id]

@router.put("/node/{node_id}")
async def update_moderator_node(node_id: str, update_data: Dict[str, Any]):
    """Update moderator node configuration"""
    if node_id not in moderator_nodes:
        raise HTTPException(status_code=404, detail="Moderator node not found")
    
    node = moderator_nodes[node_id]
    
    # Update allowed fields
    if 'prompt_template' in update_data:
        node.prompt_template = update_data['prompt_template']
    if 'position' in update_data:
        node.position = update_data['position']
    if 'settings' in update_data:
        node.settings.update(update_data['settings'])
    if 'upstream_agents' in update_data:
        node.upstream_agents = update_data['upstream_agents']
    
    moderator_nodes[node_id] = node
    
    # Notify connected clients
    await broadcast_update({
        'type': 'node_updated',
        'node_id': node_id,
        'data': node.dict()
    })
    
    return {'status': 'updated', 'node': node}

@router.post("/execute")
async def execute_moderator(request: ModeratorExecutionRequest):
    """Execute a moderator node with user input and upstream outputs"""
    
    if request.node_id not in moderator_nodes:
        raise HTTPException(status_code=404, detail="Moderator node not found")
    
    node = moderator_nodes[request.node_id]
    execution_id = str(uuid.uuid4())
    
    # Create execution state
    state = ModeratorState(
        execution_id=execution_id,
        node_id=request.node_id,
        status='processing',
        input_received={
            'user_input': request.user_input,
            'upstream_outputs': request.upstream_outputs
        },
        upstream_references=[],
        timestamp=datetime.utcnow().isoformat()
    )
    
    try:
        # Extract and resolve tokens
        tokens = extract_agent_tokens(node.prompt_template)
        resolved_prompt = node.prompt_template
        
        for token_info in tokens:
            try:
                value = resolve_token_path(
                    token_info['agent'],
                    token_info['field'],
                    request.upstream_outputs
                )
                resolved_prompt = resolved_prompt.replace(
                    token_info['token'],
                    json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                )
                state.upstream_references.append(token_info['full_path'])
            except Exception as e:
                # Token couldn't be resolved
                pass
        
        # Add user input if provided
        if request.user_input:
            resolved_prompt = f"{resolved_prompt}\n\nUser Input: {request.user_input}"
        
        # Combine all upstream outputs
        combined_data = {}
        for agent_name, output in request.upstream_outputs.items():
            combined_data.update(output)
        
        # If user input provided, add it
        if request.user_input:
            combined_data['user_input'] = request.user_input
        
        # Check schema alignment
        mismatch = detect_schema_mismatch(combined_data, node.output_schema)
        
        # If misalignment detected or auto_resolve enabled, use Gemini
        if mismatch['needs_moderator'] or node.settings.get('auto_resolve', True):
            synthesis_result = await synthesize_with_gemini(
                combined_data,
                node.output_schema,
                resolved_prompt,
                node.settings.get('temperature', 0.0)
            )
            
            state.output_generated = synthesis_result['output']
            state.gemini_prompt = synthesis_result['gemini_prompt']
            state.cost_cents = synthesis_result['cost_cents']
        else:
            # Direct pass-through if schemas match
            state.output_generated = combined_data
            state.cost_cents = 0
        
        state.compatibility_score = mismatch['compatibility_score']
        state.status = 'success'
        
    except Exception as e:
        state.status = 'failed'
        state.error_message = str(e)
    
    # Store execution
    moderator_executions.append(state)
    
    # Broadcast to connected clients
    await broadcast_update({
        'type': 'execution_complete',
        'execution_id': execution_id,
        'node_id': request.node_id,
        'status': state.status,
        'output': state.output_generated
    })
    
    return state

@router.post("/check-compatibility")
async def check_compatibility(request: SchemaAlignmentRequest):
    """Check compatibility between source output and target schema"""
    
    mismatch = detect_schema_mismatch(request.source_output, request.target_input_schema)
    
    # If moderator needed, provide synthesis preview
    synthesis_preview = None
    if mismatch['needs_moderator']:
        result = await synthesize_with_gemini(
            request.source_output,
            request.target_input_schema,
            request.moderator_prompt
        )
        synthesis_preview = result['output']
    
    return {
        'compatibility': mismatch,
        'synthesis_preview': synthesis_preview,
        'recommendation': 'Insert Moderator' if mismatch['needs_moderator'] else 'Direct Connection OK'
    }

@router.post("/duplicate/{node_id}")
async def duplicate_moderator_node(node_id: str, new_position: Dict[str, float]):
    """Duplicate an existing moderator node"""
    
    if node_id not in moderator_nodes:
        raise HTTPException(status_code=404, detail="Moderator node not found")
    
    original = moderator_nodes[node_id]
    new_id = f"{node_id}_copy_{uuid.uuid4().hex[:8]}"
    
    # Create duplicate with new position
    duplicate = ModeratorNode(
        node_id=new_id,
        name=f"{original.name} (Copy)",
        position=new_position,
        prompt_template=original.prompt_template,
        input_schema=original.input_schema,
        output_schema=original.output_schema,
        upstream_agents=[],
        settings=original.settings.copy()
    )
    
    moderator_nodes[new_id] = duplicate
    
    await broadcast_update({
        'type': 'node_duplicated',
        'original_id': node_id,
        'new_id': new_id,
        'data': duplicate.dict()
    })
    
    return {
        'status': 'duplicated',
        'original_id': node_id,
        'new_id': new_id,
        'node': duplicate
    }

@router.delete("/node/{node_id}")
async def delete_moderator_node(node_id: str):
    """Delete a moderator node"""
    
    if node_id not in moderator_nodes:
        raise HTTPException(status_code=404, detail="Moderator node not found")
    
    del moderator_nodes[node_id]
    
    await broadcast_update({
        'type': 'node_deleted',
        'node_id': node_id
    })
    
    return {'status': 'deleted', 'node_id': node_id}

@router.get("/executions")
async def get_executions(limit: int = 20):
    """Get recent moderator executions"""
    return sorted(
        moderator_executions,
        key=lambda x: x.timestamp,
        reverse=True
    )[:limit]

@router.get("/upstream-schemas/{node_id}")
async def get_upstream_schemas(node_id: str):
    """Get schemas of upstream agents for autocompletion"""
    
    if node_id not in moderator_nodes:
        raise HTTPException(status_code=404, detail="Moderator node not found")
    
    node = moderator_nodes[node_id]
    schemas = {}
    
    # Get schemas from connected upstream agents
    # This would fetch from the main agent database
    # For now, return mock schemas
    
    for agent_id in node.upstream_agents:
        schemas[agent_id] = {
            'output_schema': {
                'type': 'object',
                'properties': {
                    'summary': {'type': 'string'},
                    'sentences': {'type': 'array', 'items': {'type': 'string'}},
                    'sentiment': {'type': 'string'},
                    'score': {'type': 'number'}
                }
            }
        }
    
    return schemas

# ============= WEBSOCKET =============

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket connection for live updates"""
    await websocket.accept()
    websocket_connections[client_id] = websocket
    
    try:
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get('type') == 'ping':
                await websocket.send_json({'type': 'pong'})
            
    except WebSocketDisconnect:
        del websocket_connections[client_id]

async def broadcast_update(update: Dict[str, Any]):
    """Broadcast update to all connected WebSocket clients"""
    disconnected = []
    
    for client_id, ws in websocket_connections.items():
        try:
            await ws.send_json(update)
        except:
            disconnected.append(client_id)
    
    # Clean up disconnected clients
    for client_id in disconnected:
        del websocket_connections[client_id]
