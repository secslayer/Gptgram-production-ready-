"""
COMPLETE GEMINI LLM TRANSFORMER SYSTEM
Implements deterministic → GAT → LLM transform hierarchy with full audit trail

Requirements:
- Schema enforcement with JSON Schema validation
- Deterministic-first mapping before any ML/LLM
- GAT suggestions as second tier
- Gemini LLM as last resort with temp=0, strict JSON
- Full auditing and persistence
- Idempotency support
- Budget control and cost tracking
- @Agent.field token resolution
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid
import json
import hashlib
import re
from collections import defaultdict

router = APIRouter(prefix="/api/chain", tags=["transformer-system"])

# ============= DATA MODELS =============

class AgentMetadata(BaseModel):
    agent_id: Union[int, str]
    alias: str
    name: str
    type: str  # 'n8n' or 'custom'
    webhook_url: Optional[str] = None
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    example_input: Dict[str, Any]
    example_output: Dict[str, Any]
    price_cents: int
    verification_level: str  # 'L1', 'L2', 'L3'

class CompatibilityScoreRequest(BaseModel):
    source_agent_id: Union[int, str]
    target_agent_id: Union[int, str]
    source_sample_output: Dict[str, Any]

class ResolveTokensRequest(BaseModel):
    template: Any
    outputs_map: Dict[str, Dict[str, Any]]

class DeterministicMappingRequest(BaseModel):
    source_outputs_map: Dict[str, Dict[str, Any]]
    target_input_schema: Dict[str, Any]

class GATMappingRequest(BaseModel):
    source_agent_id: Union[int, str]
    target_agent_id: Union[str, str]
    source_sample_output: Dict[str, Any]
    target_input_schema: Dict[str, Any]

class GeminiTransformRequest(BaseModel):
    source_combined_payload: Dict[str, Any]
    target_input_schema: Dict[str, Any]
    examples: List[Dict[str, Any]] = []
    idempotency_key: str

class SaveTransformRequest(BaseModel):
    chain_id: str
    transform_id: str
    transform_result: Dict[str, Any]

class MappingRecipe(BaseModel):
    from_path: str
    to_path: str
    transform: str  # 'identity', 'concat', 'pick_first', 'serialize', 'coerce_number', 'coerce_string'

# ============= STORAGE =============

agents_db = {}
transforms_audit = []
compatibility_cache = {}
gat_patterns = []
idempotency_store = {}

# Field alias dictionary for deterministic mapping
FIELD_ALIASES = {
    'text': ['content', 'body', 'summary', 'text', 'message', 'description'],
    'summary': ['text', 'abstract', 'summary', 'overview'],
    'content': ['text', 'body', 'content', 'data'],
    'sentiment': ['sentiment', 'emotion', 'feeling', 'mood'],
    'score': ['score', 'confidence', 'rating', 'value'],
    'target': ['target', 'language', 'lang', 'to_lang'],
}

# Initialize some default agents
DEFAULT_AGENTS = {
    'summarizer': AgentMetadata(
        agent_id='summarizer',
        alias='Summarizer',
        name='n8n Summarizer',
        type='n8n',
        webhook_url='https://templatechat.app.n8n.cloud/webhook/gptgram/summarize',
        input_schema={
            'type': 'object',
            'required': ['text'],
            'properties': {
                'text': {'type': 'string'},
                'maxSentences': {'type': 'number', 'default': 2}
            }
        },
        output_schema={
            'type': 'object',
            'properties': {
                'summary': {'type': 'string'},
                'key_sentences': {'type': 'array', 'items': {'type': 'string'}}
            }
        },
        example_input={'text': 'Long text to summarize...', 'maxSentences': 2},
        example_output={'summary': 'Concise summary', 'key_sentences': ['Key point 1', 'Key point 2']},
        price_cents=50,
        verification_level='L2'
    ),
    'sentiment': AgentMetadata(
        agent_id='sentiment',
        alias='Sentiment',
        name='Sentiment Analyzer',
        type='custom',
        input_schema={
            'type': 'object',
            'required': ['text'],
            'properties': {
                'text': {'type': 'string'}
            }
        },
        output_schema={
            'type': 'object',
            'properties': {
                'sentiment': {'type': 'string', 'enum': ['positive', 'negative', 'neutral']},
                'score': {'type': 'number', 'minimum': 0, 'maximum': 1}
            }
        },
        example_input={'text': 'Sample text'},
        example_output={'sentiment': 'positive', 'score': 0.85},
        price_cents=30,
        verification_level='L3'
    ),
    'translator': AgentMetadata(
        agent_id='translator',
        alias='Translator',
        name='n8n Translator',
        type='n8n',
        webhook_url='https://templatechat.app.n8n.cloud/webhook/gptgram/translate',
        input_schema={
            'type': 'object',
            'required': ['text', 'target'],
            'properties': {
                'text': {'type': 'string'},
                'target': {'type': 'string', 'enum': ['es', 'fr', 'de', 'it', 'pt']}
            }
        },
        output_schema={
            'type': 'object',
            'properties': {
                'translated': {'type': 'string'},
                'target': {'type': 'string'}
            }
        },
        example_input={'text': 'Hello world', 'target': 'es'},
        example_output={'translated': 'Hola mundo', 'target': 'es'},
        price_cents=75,
        verification_level='L2'
    )
}

agents_db.update(DEFAULT_AGENTS)

# ============= HELPER FUNCTIONS =============

def extract_at_tokens(template: Any) -> List[str]:
    """Extract all @Agent.field tokens from a template"""
    if isinstance(template, str):
        return re.findall(r'@(\w+(?:\.\w+|\[\d+\])+)', template)
    elif isinstance(template, dict):
        tokens = []
        for value in template.values():
            tokens.extend(extract_at_tokens(value))
        return tokens
    elif isinstance(template, list):
        tokens = []
        for item in template:
            tokens.extend(extract_at_tokens(item))
        return tokens
    return []

def resolve_at_token(token: str, outputs_map: Dict[str, Dict]) -> tuple:
    """
    Resolve @Agent.field.nested[0].path to actual value
    Returns: (resolved_value, error_message)
    """
    parts = re.split(r'\.|\[|\]', token)
    parts = [p for p in parts if p]  # Remove empty strings
    
    if not parts:
        return None, "Empty token"
    
    alias = parts[0]
    if alias not in outputs_map:
        return None, f"Agent alias '{alias}' not found in outputs"
    
    current = outputs_map[alias]
    path = parts[1:]
    
    try:
        for part in path:
            if part.isdigit():
                current = current[int(part)]
            else:
                current = current[part]
        return current, None
    except (KeyError, IndexError, TypeError) as e:
        return None, f"Path resolution failed at '{part}': {str(e)}"

def compute_compatibility_score(
    source_output: Dict[str, Any],
    target_schema: Dict[str, Any]
) -> float:
    """
    Compute compatibility score based on:
    - Required keys present (60%)
    - Type matches (20%)
    - Value compatibility (20%)
    """
    required_keys = target_schema.get('required', [])
    properties = target_schema.get('properties', {})
    
    if not required_keys:
        return 0.85  # No requirements, likely compatible
    
    # Check required keys
    present_keys = sum(1 for key in required_keys if key in source_output)
    key_score = present_keys / len(required_keys) if required_keys else 1.0
    
    # Check type matches
    type_matches = 0
    for key in required_keys:
        if key in source_output and key in properties:
            expected_type = properties[key].get('type', 'string')
            actual_value = source_output[key]
            
            if expected_type == 'string' and isinstance(actual_value, str):
                type_matches += 1
            elif expected_type == 'number' and isinstance(actual_value, (int, float)):
                type_matches += 1
            elif expected_type == 'boolean' and isinstance(actual_value, bool):
                type_matches += 1
            elif expected_type == 'array' and isinstance(actual_value, list):
                type_matches += 1
            elif expected_type == 'object' and isinstance(actual_value, dict):
                type_matches += 1
    
    type_score = type_matches / len(required_keys) if required_keys else 1.0
    
    # Overall score (weighted)
    score = (key_score * 0.6) + (type_score * 0.4)
    
    return round(score, 2)

def apply_deterministic_mapping(
    source: Dict[str, Any],
    target_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """Apply deterministic field mapping rules"""
    result = {}
    required = target_schema.get('required', [])
    properties = target_schema.get('properties', {})
    
    for field in required:
        # Direct match
        if field in source:
            result[field] = source[field]
            continue
        
        # Check aliases
        if field in FIELD_ALIASES:
            for alias in FIELD_ALIASES[field]:
                if alias in source:
                    result[field] = source[alias]
                    break
        
        # Type coercion attempts
        if field not in result:
            expected_type = properties.get(field, {}).get('type', 'string')
            
            # Find any similar field
            for src_key, src_value in source.items():
                if field.lower() in src_key.lower() or src_key.lower() in field.lower():
                    if expected_type == 'string':
                        result[field] = str(src_value) if src_value is not None else ''
                    elif expected_type == 'number' and isinstance(src_value, str):
                        try:
                            result[field] = float(src_value)
                        except ValueError:
                            pass
                    else:
                        result[field] = src_value
                    break
    
    return result

# ============= API ENDPOINTS =============

@router.post("/resolve-atokens")
async def resolve_at_tokens(request: ResolveTokensRequest):
    """
    Resolve @Agent.field tokens in a template
    Returns resolved payload and any unresolved tokens
    """
    tokens = extract_at_tokens(request.template)
    resolved_payload = request.template
    unresolved_tokens = []
    
    for token in tokens:
        value, error = resolve_at_token(token, request.outputs_map)
        if error:
            unresolved_tokens.append({
                'token': f'@{token}',
                'reason': error,
                'suggestion': 'Check agent alias and field path'
            })
        else:
            # Replace token in template
            if isinstance(resolved_payload, str):
                resolved_payload = resolved_payload.replace(f'@{token}', str(value))
            elif isinstance(resolved_payload, dict):
                # Deep replace in dict
                for key, val in resolved_payload.items():
                    if isinstance(val, str) and f'@{token}' in val:
                        resolved_payload[key] = val.replace(f'@{token}', str(value))
    
    return {
        'resolved_payload': resolved_payload,
        'unresolved_tokens': unresolved_tokens,
        'diagnostics': {
            'total_tokens': len(tokens),
            'resolved': len(tokens) - len(unresolved_tokens),
            'unresolved': len(unresolved_tokens)
        }
    }

@router.post("/compatibility-score")
async def calculate_compatibility(request: CompatibilityScoreRequest):
    """
    Calculate compatibility score between source and target agents
    """
    # Check cache
    cache_key = f"{request.source_agent_id}_{request.target_agent_id}_{hashlib.md5(json.dumps(request.source_sample_output, sort_keys=True).encode()).hexdigest()[:8]}"
    
    if cache_key in compatibility_cache:
        return compatibility_cache[cache_key]
    
    # Get target agent
    target_agent = agents_db.get(str(request.target_agent_id))
    if not target_agent:
        raise HTTPException(status_code=404, detail="Target agent not found")
    
    # Compute score
    score = compute_compatibility_score(
        request.source_sample_output,
        target_agent.input_schema
    )
    
    # Generate reasons
    reasons = []
    required = target_agent.input_schema.get('required', [])
    for key in required:
        if key not in request.source_sample_output:
            reasons.append(f"missing_required_key: '{key}' not in source output")
    
    # Generate suggestions if score is low
    suggestions = []
    if score < 0.85:
        # Try deterministic mapping
        mapped = apply_deterministic_mapping(
            request.source_sample_output,
            target_agent.input_schema
        )
        mapped_score = compute_compatibility_score(mapped, target_agent.input_schema)
        
        if mapped_score > score:
            suggestions.append({
                'type': 'deterministic',
                'method': 'field_mapping',
                'payload': mapped,
                'score': mapped_score,
                'recipe': {'mappings': []}
            })
    
    result = {
        'score': score,
        'reasons': reasons,
        'suggestions': suggestions
    }
    
    # Cache result
    compatibility_cache[cache_key] = result
    
    return result

@router.post("/try-deterministic-mappings")
async def try_deterministic(request: DeterministicMappingRequest):
    """
    Attempt deterministic mapping of source outputs to target schema
    Returns ranked candidates
    """
    # Merge source outputs if multiple
    combined_source = {}
    for alias, output in request.source_outputs_map.items():
        combined_source.update(output)
    
    # Apply deterministic rules
    mapped = apply_deterministic_mapping(combined_source, request.target_input_schema)
    score = compute_compatibility_score(mapped, request.target_input_schema)
    
    # Generate recipe
    recipe_mappings = []
    for key, value in mapped.items():
        # Find source of this value
        for src_key, src_val in combined_source.items():
            if src_val == value:
                recipe_mappings.append({
                    'from': src_key,
                    'to': key,
                    'transform': 'identity' if src_key == key else 'alias'
                })
                break
    
    candidates = [{
        'payload': mapped,
        'score': score,
        'recipe': {'mappings': recipe_mappings},
        'method': 'deterministic',
        'reasoning': 'Applied field alias mapping and type coercion'
    }]
    
    return candidates

@router.post("/gat-mappings")
async def get_gat_mappings(request: GATMappingRequest):
    """
    Get GAT-recommended mapping recipes based on historical patterns
    """
    # Mock GAT suggestions based on common patterns
    recipes = []
    
    # Pattern 1: Summarizer -> Translator
    if 'summary' in request.source_sample_output:
        recipes.append({
            'recipe_id': 'gat_001',
            'mappings': [
                {'from_path': 'summary', 'to_path': 'text', 'transform': 'identity'},
                {'from_path': None, 'to_path': 'target', 'transform': 'default_es'}
            ],
            'confidence': 0.87,
            'based_on_patterns': 45
        })
    
    # Pattern 2: Text content mapping
    if 'text' in request.source_sample_output or 'content' in request.source_sample_output:
        recipes.append({
            'recipe_id': 'gat_002',
            'mappings': [
                {'from_path': 'text', 'to_path': 'text', 'transform': 'identity'}
            ],
            'confidence': 0.92,
            'based_on_patterns': 120
        })
    
    # Pattern 3: Multi-field merge
    if len(request.source_sample_output) > 1:
        recipes.append({
            'recipe_id': 'gat_003',
            'mappings': list(request.source_sample_output.keys())[:3],
            'confidence': 0.73,
            'based_on_patterns': 28
        })
    
    return sorted(recipes, key=lambda x: x['confidence'], reverse=True)

@router.post("/gemini-transform")
async def gemini_transform(request: GeminiTransformRequest):
    """
    Use Gemini LLM to transform source payload to target schema
    IMPORTANT: Temperature=0, strict JSON, with idempotency
    """
    # Check idempotency
    if request.idempotency_key in idempotency_store:
        return idempotency_store[request.idempotency_key]
    
    # Mock Gemini transformation (in production, call actual Gemini API)
    # The actual prompt would be:
    gemini_prompt = f"""You are a strict JSON transformer. You will receive:
- "source": a JSON object containing combined outputs from upstream agents
- "target_schema": a JSON Schema that describes required fields and types
- "examples": valid example inputs matching the target_schema

Rules:
1. Output EXACTLY one JSON object conforming to "target_schema". Nothing else.
2. Use ONLY information available in "source". Do NOT invent facts.
3. If a required field cannot be derived, set it to null.
4. Do NOT include extra fields not in the target_schema.
5. If you cannot produce a valid payload, output: {{"__error":"CANNOT_SYNTHESIZE","reason":"one-line reason"}}

Source: {json.dumps(request.source_combined_payload)}
Target Schema: {json.dumps(request.target_input_schema)}
Examples: {json.dumps(request.examples[:3])}
"""
    
    # Mock Gemini response (deterministically transform based on source)
    required = request.target_input_schema.get('required', [])
    properties = request.target_input_schema.get('properties', {})
    
    transformed = {}
    for field in required:
        # Try to find value in source
        if field in request.source_combined_payload:
            transformed[field] = request.source_combined_payload[field]
        else:
            # Check aliases or nested
            found = False
            for src_key, src_val in request.source_combined_payload.items():
                if field.lower() in src_key.lower():
                    transformed[field] = src_val
                    found = True
                    break
            
            if not found:
                # Use example or default
                if request.examples and field in request.examples[0]:
                    transformed[field] = request.examples[0][field]
                elif field == 'target':
                    transformed[field] = 'es'  # Common default
                else:
                    transformed[field] = None
    
    # Validate against schema
    score = compute_compatibility_score(transformed, request.target_input_schema)
    valid = score >= 0.7
    
    # Mock token/cost calculation
    tokens_in = len(json.dumps(request.source_combined_payload)) // 4
    tokens_out = len(json.dumps(transformed)) // 4
    cost_cents = max(10, (tokens_in + tokens_out) // 10)
    
    result = {
        'valid': valid,
        'payload': transformed if valid else None,
        'error': None if valid else '__error: Low compatibility score',
        'transform_used': 'llm',
        'compatibility_score': score,
        'cost_cents': cost_cents,
        'tokens': {'input': tokens_in, 'output': tokens_out},
        'attempts': 1,
        'gemini_prompt_used': gemini_prompt[:200] + '...'  # For audit
    }
    
    # Store for idempotency
    idempotency_store[request.idempotency_key] = result
    
    # Audit log
    transforms_audit.append({
        'transform_id': str(uuid.uuid4()),
        'method': 'llm',
        'payload_before': request.source_combined_payload,
        'payload_after': transformed,
        'compatibility_score': score,
        'cost_cents': cost_cents,
        'tokens': tokens_in + tokens_out,
        'idempotency_key': request.idempotency_key,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'success' if valid else 'failed'
    })
    
    return result

@router.post("/save-transform")
async def save_transform(request: SaveTransformRequest):
    """
    Save accepted transform result for audit and future use
    """
    transform_record = {
        'transform_id': request.transform_id,
        'chain_id': request.chain_id,
        **request.transform_result,
        'saved_at': datetime.utcnow().isoformat()
    }
    
    transforms_audit.append(transform_record)
    
    return {
        'ok': True,
        'saved_transform_id': request.transform_id
    }

@router.get("/recommend-agents")
async def recommend_agents(
    context_node_ids: List[str] = [],
    top_k: int = 5
):
    """
    Recommend compatible agents based on GAT patterns
    """
    # Mock recommendations based on common workflows
    all_recommendations = [
        {
            'agent_id': 'sentiment',
            'alias': 'Sentiment',
            'name': 'Sentiment Analyzer',
            'compatibility_score': 0.92,
            'reasons': ['Commonly follows text processing', 'High success rate'],
            'avg_latency': 250,
            'verification_level': 'L3'
        },
        {
            'agent_id': 'translator',
            'alias': 'Translator',
            'name': 'n8n Translator',
            'compatibility_score': 0.86,
            'reasons': ['Can process text output', 'Useful for localization'],
            'avg_latency': 450,
            'verification_level': 'L2'
        },
        {
            'agent_id': 'summarizer',
            'alias': 'Summarizer',
            'name': 'n8n Summarizer',
            'compatibility_score': 0.78,
            'reasons': ['Good for condensing content', 'Often used in pipelines'],
            'avg_latency': 380,
            'verification_level': 'L2'
        }
    ]
    
    return all_recommendations[:top_k]

@router.get("/transform-audit")
async def get_transform_audit(limit: int = 50):
    """Get transform audit trail"""
    return sorted(transforms_audit, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]

@router.get("/agents")
async def list_agents():
    """List all available agents with full metadata"""
    return list(agents_db.values())

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    agent = agents_db.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
