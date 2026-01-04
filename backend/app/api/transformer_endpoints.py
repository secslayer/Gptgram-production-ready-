"""
Comprehensive Transformer API Endpoints
Implements deterministic, GAT, and LLM-based transformations with @agent tokens
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import json
import hashlib
import re
from datetime import datetime

router = APIRouter(prefix="/api/chain", tags=["transformers"])

# ============= Data Models =============

class ResolveTokensRequest(BaseModel):
    template: str
    outputs_map: Dict[str, Any]

class ResolveTokensResponse(BaseModel):
    resolved_payload: Dict[str, Any]
    unresolved_tokens: List[str]

class CompatibilityRequest(BaseModel):
    source_agent_id: str
    target_agent_id: str
    source_sample_output: Dict[str, Any]

class CompatibilityResponse(BaseModel):
    score: float
    reasons: List[str]
    suggestions: List[str]

class DeterministicMappingRequest(BaseModel):
    source_outputs: List[Dict[str, Any]]
    target_input_schema: Dict[str, Any]

class MappingCandidate(BaseModel):
    payload: Dict[str, Any]
    score: float
    recipe: Dict[str, Any]
    method: str = "deterministic"

class GATMappingRequest(BaseModel):
    source_agent_id: str
    target_agent_id: str
    source_sample_output: Dict[str, Any]
    target_input_schema: Dict[str, Any]

class GATRecipe(BaseModel):
    recipe_id: str
    mappings: List[Dict[str, Any]]
    confidence: float

class GeminiTransformRequest(BaseModel):
    source_combined_payload: Dict[str, Any]
    target_input_schema: Dict[str, Any]
    examples: List[Dict[str, Any]] = []
    idempotency_key: str

class GeminiTransformResponse(BaseModel):
    valid: bool
    payload: Optional[Dict[str, Any]]
    compatibility_score: float
    tokens: int
    cost_cents: float
    errors: List[str] = []

class SaveTransformRequest(BaseModel):
    chain_id: str
    transform_id: str
    transform_result: Dict[str, Any]

class RecommendAgentsRequest(BaseModel):
    context_node_ids: List[str]
    top_k: int = 5

class AgentRecommendation(BaseModel):
    agent_id: str
    name: str
    compatibility_score: float
    reasons: List[str]

# ============= Cache & Storage =============

compatibility_cache = {}
transform_storage = {}
idempotency_cache = {}

# ============= Helper Functions =============

def extract_tokens_from_template(template: str) -> List[str]:
    """Extract @Agent.field tokens from template"""
    pattern = r'@(\w+)\.([.\w\[\]]+)'
    matches = re.findall(pattern, template)
    return [f"@{agent}.{path}" for agent, path in matches]

def resolve_token(token: str, outputs_map: Dict[str, Any]) -> Optional[Any]:
    """Resolve a single @Agent.field token"""
    match = re.match(r'@(\w+)\.([.\w\[\]]+)', token)
    if not match:
        return None
    
    agent_alias, path = match.groups()
    
    if agent_alias not in outputs_map:
        return None
    
    value = outputs_map[agent_alias]
    
    # Handle nested paths
    for part in path.split('.'):
        if '[' in part and ']' in part:
            # Handle array indexing
            field, index = part.split('[')
            index = int(index.rstrip(']'))
            if field:
                value = value.get(field, None)
            if isinstance(value, list) and index < len(value):
                value = value[index]
            else:
                return None
        else:
            if isinstance(value, dict):
                value = value.get(part, None)
            else:
                return None
    
    return value

def calculate_compatibility_score(source_schema: Dict, target_schema: Dict, sample_data: Dict) -> float:
    """Calculate compatibility score between schemas"""
    required_fields = target_schema.get('required', [])
    properties = target_schema.get('properties', {})
    
    score = 0.0
    max_score = len(required_fields) * 0.6 + len(properties) * 0.2 + 0.2
    
    # Check required fields (60% weight)
    for field in required_fields:
        if field in sample_data:
            score += 0.6
        elif any(k.lower() == field.lower() or field in k.lower() for k in sample_data.keys()):
            score += 0.4  # Partial match
    
    # Check type compatibility (20% weight)
    for field, schema in properties.items():
        if field in sample_data:
            expected_type = schema.get('type')
            actual_type = type(sample_data[field]).__name__
            if expected_type == actual_type or \
               (expected_type == 'string' and actual_type == 'str') or \
               (expected_type == 'number' and actual_type in ['int', 'float']):
                score += 0.2 / len(properties)
    
    # Check validation rules (20% weight)
    if all(field in sample_data for field in required_fields):
        score += 0.2
    
    return min(score / max_score, 1.0)

def apply_deterministic_mapping(source_data: Dict, target_schema: Dict) -> MappingCandidate:
    """Apply deterministic mapping rules"""
    # Key alias dictionary
    alias_map = {
        'summary': ['abstract', 'text', 'content', 'description'],
        'text': ['content', 'message', 'body', 'data'],
        'sentiment': ['emotion', 'feeling', 'mood'],
        'score': ['confidence', 'probability', 'rating', 'value']
    }
    
    result = {}
    recipe = {"mappings": [], "transforms": []}
    
    required_fields = target_schema.get('required', [])
    properties = target_schema.get('properties', {})
    
    for field in required_fields:
        # Direct match
        if field in source_data:
            result[field] = source_data[field]
            recipe["mappings"].append({"from": field, "to": field, "transform": "identity"})
            continue
        
        # Alias match
        found = False
        for key, aliases in alias_map.items():
            if field == key:
                for alias in aliases:
                    if alias in source_data:
                        result[field] = source_data[alias]
                        recipe["mappings"].append({"from": alias, "to": field, "transform": "alias"})
                        found = True
                        break
            if found:
                break
        
        if not found:
            # Try case-insensitive match
            for src_key in source_data:
                if src_key.lower() == field.lower():
                    result[field] = source_data[src_key]
                    recipe["mappings"].append({"from": src_key, "to": field, "transform": "case_convert"})
                    found = True
                    break
        
        # Type coercion
        if field in result:
            expected_type = properties.get(field, {}).get('type')
            if expected_type == 'string' and not isinstance(result[field], str):
                result[field] = str(result[field])
                recipe["transforms"].append({"field": field, "type": "to_string"})
    
    score = calculate_compatibility_score({}, target_schema, result)
    
    return MappingCandidate(
        payload=result,
        score=score,
        recipe=recipe,
        method="deterministic"
    )

def get_gat_recommendations(source_agent_id: str, target_agent_id: str) -> List[GATRecipe]:
    """Get GAT-based mapping recommendations"""
    # Mock GAT recommendations based on historical patterns
    common_patterns = {
        ("summarizer", "sentiment"): [
            {
                "recipe_id": "sum_to_sent_v1",
                "mappings": [
                    {"from": "summary", "to": "text", "transform": "identity"},
                    {"from": "_meta.confidence", "to": "confidence", "transform": "copy"}
                ],
                "confidence": 0.92
            }
        ],
        ("sentiment", "translator"): [
            {
                "recipe_id": "sent_to_trans_v1",
                "mappings": [
                    {"from": "@Summarizer.summary", "to": "text", "transform": "reference"},
                    {"from": "_context.target_lang", "to": "target", "transform": "default", "value": "es"}
                ],
                "confidence": 0.86
            }
        ]
    }
    
    key = (source_agent_id.lower(), target_agent_id.lower())
    return [GATRecipe(**recipe) for recipe in common_patterns.get(key, [])]

# ============= API Endpoints =============

@router.post("/resolve-atokens", response_model=ResolveTokensResponse)
async def resolve_atokens(request: ResolveTokensRequest):
    """Resolve @Agent.field tokens in template"""
    template = request.template
    outputs_map = request.outputs_map
    
    tokens = extract_tokens_from_template(template)
    resolved = {}
    unresolved = []
    
    for token in tokens:
        value = resolve_token(token, outputs_map)
        if value is not None:
            # Replace token in template
            template = template.replace(token, json.dumps(value) if isinstance(value, (dict, list)) else str(value))
            resolved[token] = value
        else:
            unresolved.append(token)
    
    # Try to parse as JSON if possible
    try:
        resolved_payload = json.loads(template) if template.strip().startswith('{') else {"text": template}
    except:
        resolved_payload = {"text": template}
    
    return ResolveTokensResponse(
        resolved_payload=resolved_payload,
        unresolved_tokens=unresolved
    )

@router.post("/compatibility-score", response_model=CompatibilityResponse)
async def compatibility_score(request: CompatibilityRequest):
    """Calculate compatibility score between agents"""
    # Create cache key
    cache_key = hashlib.md5(
        f"{request.source_agent_id}:{request.target_agent_id}:{json.dumps(request.source_sample_output)}".encode()
    ).hexdigest()
    
    if cache_key in compatibility_cache:
        return compatibility_cache[cache_key]
    
    # Mock target schema (in production, fetch from database)
    target_schemas = {
        "sentiment": {
            "required": ["text"],
            "properties": {
                "text": {"type": "string"},
                "confidence": {"type": "number"}
            }
        },
        "translator": {
            "required": ["text", "target"],
            "properties": {
                "text": {"type": "string"},
                "target": {"type": "string"}
            }
        }
    }
    
    target_schema = target_schemas.get(request.target_agent_id, {})
    score = calculate_compatibility_score({}, target_schema, request.source_sample_output)
    
    reasons = []
    suggestions = []
    
    if score < 0.5:
        reasons.append("Low field overlap between source and target")
        suggestions.append("Consider adding a transformer node")
    elif score < 0.8:
        reasons.append("Some fields may need mapping")
        suggestions.append("Use deterministic mapping or GAT suggestions")
    else:
        reasons.append("High compatibility, direct connection possible")
    
    response = CompatibilityResponse(
        score=score,
        reasons=reasons,
        suggestions=suggestions
    )
    
    compatibility_cache[cache_key] = response
    return response

@router.post("/try-deterministic-mappings", response_model=List[MappingCandidate])
async def try_deterministic_mappings(request: DeterministicMappingRequest):
    """Try deterministic mapping rules"""
    candidates = []
    
    for source in request.source_outputs:
        candidate = apply_deterministic_mapping(source, request.target_input_schema)
        if candidate.score > 0.5:
            candidates.append(candidate)
    
    # Sort by score
    candidates.sort(key=lambda x: x.score, reverse=True)
    return candidates[:3]  # Return top 3

@router.post("/gat-mappings", response_model=List[GATRecipe])
async def gat_mappings(request: GATMappingRequest):
    """Get GAT-based mapping suggestions"""
    recipes = get_gat_recommendations(request.source_agent_id, request.target_agent_id)
    
    # Apply recipes and rank by confidence
    applied_recipes = []
    for recipe in recipes:
        # Check if recipe can be applied
        can_apply = True
        test_payload = {}
        
        for mapping in recipe.mappings:
            if mapping["transform"] == "reference":
                # Check if reference exists
                token = mapping["from"]
                # This would be resolved at runtime
                test_payload[mapping["to"]] = f"<{token}>"
            elif mapping["transform"] == "default":
                test_payload[mapping["to"]] = mapping.get("value", "")
            else:
                if mapping["from"] in request.source_sample_output:
                    test_payload[mapping["to"]] = request.source_sample_output[mapping["from"]]
                else:
                    can_apply = False
                    break
        
        if can_apply:
            applied_recipes.append(recipe)
    
    return applied_recipes

@router.post("/gemini-transform", response_model=GeminiTransformResponse)
async def gemini_transform(request: GeminiTransformRequest):
    """Transform using Gemini LLM (last resort)"""
    # Check idempotency
    if request.idempotency_key in idempotency_cache:
        return idempotency_cache[request.idempotency_key]
    
    # Mock Gemini API call (in production, use actual API)
    # System prompt as specified
    system_prompt = """You are a strict JSON transformer. Input:
- "source": a JSON object (combined outputs of upstream agents)
- "target_schema": a JSON Schema object describing required fields and types
- "examples": up to 3 examples of valid inputs for the target schema

Task:
- Produce exactly one JSON object that conforms to "target_schema".
- Use only information that can be derived from "source". If a required field cannot be derived, set its value to null.
- Do NOT invent facts or add extra fields outside the target schema.
- Output only the JSON object in the response body. No additional text, explanation, or markdown."""
    
    # Simulate transformation
    required_fields = request.target_input_schema.get('required', [])
    result = {}
    
    for field in required_fields:
        # Try to find matching field in source
        if field in request.source_combined_payload:
            result[field] = request.source_combined_payload[field]
        else:
            # Try to find in nested sources
            for key, value in request.source_combined_payload.items():
                if isinstance(value, dict) and field in value:
                    result[field] = value[field]
                    break
            else:
                result[field] = None
    
    # Validate against schema
    valid = all(field in result for field in required_fields)
    
    response = GeminiTransformResponse(
        valid=valid,
        payload=result if valid else None,
        compatibility_score=0.92 if valid else 0.0,
        tokens=150,  # Mock token count
        cost_cents=0.15,  # Mock cost
        errors=[] if valid else ["Missing required fields"]
    )
    
    idempotency_cache[request.idempotency_key] = response
    return response

@router.post("/save-transform")
async def save_transform(request: SaveTransformRequest):
    """Save accepted transform result"""
    transform_id = request.transform_id
    transform_storage[transform_id] = {
        "chain_id": request.chain_id,
        "transform_id": transform_id,
        "result": request.transform_result,
        "created_at": datetime.utcnow().isoformat()
    }
    return {"status": "saved", "transform_id": transform_id}

@router.get("/recommend-agents", response_model=List[AgentRecommendation])
async def recommend_agents(context_node_ids: List[str], top_k: int = 5):
    """Get recommended agents based on context"""
    # Mock recommendations based on common patterns
    recommendations = []
    
    if "summarizer" in [id.lower() for id in context_node_ids]:
        recommendations.append(AgentRecommendation(
            agent_id="sentiment",
            name="Sentiment Analyzer",
            compatibility_score=0.92,
            reasons=["Commonly used after summarization", "High historical success rate"]
        ))
    
    if "sentiment" in [id.lower() for id in context_node_ids]:
        recommendations.append(AgentRecommendation(
            agent_id="translator",
            name="Language Translator",
            compatibility_score=0.86,
            reasons=["Can translate sentiment-analyzed text", "Preserves emotional context"]
        ))
    
    # Add generic recommendations
    all_agents = [
        ("classifier", "Text Classifier", 0.75),
        ("entity_extractor", "Entity Extractor", 0.70),
        ("keyword_extractor", "Keyword Extractor", 0.68)
    ]
    
    for agent_id, name, score in all_agents:
        if len(recommendations) < top_k:
            recommendations.append(AgentRecommendation(
                agent_id=agent_id,
                name=name,
                compatibility_score=score,
                reasons=["General purpose agent", "Can process text data"]
            ))
    
    return recommendations[:top_k]
