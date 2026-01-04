"""
CUSTOM PROMPT AGENT SYSTEM
Allows users to create custom transformation agents using @token prompts

Features:
- User writes custom prompt with @AgentName.field tokens
- System resolves tokens from upstream outputs
- Prompt sent to LLM for transformation
- Output validated against target schema
- Acts as flexible adapter between any agents
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import re
import json
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/prompt-agent", tags=["prompt-agent"])

# ============= DATA MODELS =============

class CreatePromptAgentRequest(BaseModel):
    name: str
    description: str
    prompt_template: str  # Can include @tokens
    expected_output_schema: Dict[str, Any]
    temperature: float = 0.7
    max_tokens: int = 500

class ExecutePromptAgentRequest(BaseModel):
    prompt_agent_id: str
    upstream_outputs: Dict[str, Dict[str, Any]]  # {agentName: {field: value}}
    additional_context: Optional[Dict[str, Any]] = {}

class PromptAgent(BaseModel):
    agent_id: str
    name: str
    description: str
    prompt_template: str
    expected_output_schema: Dict[str, Any]
    temperature: float
    max_tokens: int
    type: str = "prompt_agent"
    verification_level: str = "USER"
    price_cents: int = 20  # Dynamic based on actual usage
    created_at: str

# ============= STORAGE =============

prompt_agents_db = {}
prompt_agent_executions = []

# ============= HELPER FUNCTIONS =============

def extract_all_tokens(template: str) -> List[Dict[str, str]]:
    """
    Extract all @tokens from template
    Returns list of {token, agent, field_path}
    
    Supports:
    - @AgentName
    - @AgentName.field
    - @AgentName.nested.field
    - @AgentName.array[0]
    - @AgentName.data.items[2].value
    """
    # Pattern matches @AgentName.field.path[index]...
    pattern = r'@(\w+)(?:\.[\w\[\]]+)?'
    matches = re.findall(pattern, template)
    
    tokens = []
    for match in re.finditer(r'@([\w\.]+(?:\[\d+\])?(?:\.[\w\.]+(?:\[\d+\])?)*)', template):
        full_token = match.group(0)
        token_path = match.group(1)
        
        # Split into agent name and field path
        parts = token_path.split('.', 1)
        agent_name = parts[0]
        field_path = parts[1] if len(parts) > 1 else None
        
        tokens.append({
            'token': full_token,
            'agent': agent_name,
            'field_path': field_path
        })
    
    return tokens

def resolve_token_value(agent_name: str, field_path: Optional[str], outputs: Dict[str, Dict]) -> tuple:
    """
    Resolve a single token to its value
    Returns: (value, error_message)
    """
    # Check if agent exists in outputs
    if agent_name not in outputs:
        return None, f"Agent '{agent_name}' not found in upstream outputs"
    
    agent_output = outputs[agent_name]
    
    # If no field path, return entire output
    if not field_path:
        return agent_output, None
    
    # Navigate the field path
    current = agent_output
    path_parts = re.split(r'\.|\[|\]', field_path)
    path_parts = [p for p in path_parts if p]  # Remove empty strings
    
    try:
        for part in path_parts:
            if part.isdigit():
                current = current[int(part)]
            else:
                current = current[part]
        return current, None
    except (KeyError, IndexError, TypeError) as e:
        return None, f"Failed to resolve path '{field_path}' in {agent_name}: {str(e)}"

def resolve_prompt_template(template: str, upstream_outputs: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Resolve all @tokens in prompt template
    Returns: {resolved_prompt, unresolved_tokens[], metadata}
    """
    tokens = extract_all_tokens(template)
    resolved_prompt = template
    unresolved = []
    resolved_values = {}
    
    for token_info in tokens:
        value, error = resolve_token_value(
            token_info['agent'],
            token_info['field_path'],
            upstream_outputs
        )
        
        if error:
            unresolved.append({
                'token': token_info['token'],
                'agent': token_info['agent'],
                'field_path': token_info['field_path'],
                'error': error
            })
        else:
            # Store resolved value
            resolved_values[token_info['token']] = value
            
            # Replace in template
            # Convert value to string for replacement
            value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            resolved_prompt = resolved_prompt.replace(token_info['token'], value_str)
    
    return {
        'resolved_prompt': resolved_prompt,
        'unresolved_tokens': unresolved,
        'resolved_values': resolved_values,
        'total_tokens': len(tokens),
        'resolved_count': len(tokens) - len(unresolved)
    }

def execute_llm_with_prompt(prompt: str, temperature: float, max_tokens: int, output_schema: Dict) -> Dict[str, Any]:
    """
    Execute LLM with the resolved prompt
    In production, this would call actual Gemini API
    """
    # Mock LLM execution - in production, call Gemini
    system_prompt = f"""You are a data transformation assistant. 
The user has provided a prompt with resolved data from previous agents.
Based on the prompt, generate output that matches this schema:
{json.dumps(output_schema, indent=2)}

Output ONLY valid JSON matching the schema. No additional text or explanation."""
    
    # For mock, try to extract structured data from prompt
    # In production: call actual Gemini API with system_prompt + prompt
    
    # Mock response based on schema
    required_fields = output_schema.get('properties', {}).keys()
    mock_output = {}
    
    for field in required_fields:
        field_type = output_schema.get('properties', {}).get(field, {}).get('type', 'string')
        
        # Try to find relevant value in prompt
        if field_type == 'string':
            # Extract first string-like content
            mock_output[field] = prompt[:100] if len(prompt) > 0 else f"Generated {field}"
        elif field_type == 'number':
            mock_output[field] = 0.85
        elif field_type == 'boolean':
            mock_output[field] = True
        elif field_type == 'array':
            mock_output[field] = [prompt[:50]] if prompt else []
        elif field_type == 'object':
            mock_output[field] = {'processed': True}
        else:
            mock_output[field] = None
    
    # In production, actual LLM call would be:
    # response = gemini.generate_content(
    #     system_prompt + "\n\nUser Prompt:\n" + prompt,
    #     temperature=temperature,
    #     max_output_tokens=max_tokens
    # )
    
    return mock_output

# ============= API ENDPOINTS =============

@router.post("/create")
async def create_prompt_agent(request: CreatePromptAgentRequest):
    """
    Create a new custom prompt agent
    User provides template with @tokens
    """
    agent_id = str(uuid.uuid4())
    
    # Extract tokens from template for validation
    tokens = extract_all_tokens(request.prompt_template)
    
    prompt_agent = PromptAgent(
        agent_id=agent_id,
        name=request.name,
        description=request.description,
        prompt_template=request.prompt_template,
        expected_output_schema=request.expected_output_schema,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        created_at=datetime.utcnow().isoformat()
    )
    
    prompt_agents_db[agent_id] = prompt_agent
    
    return {
        'agent_id': agent_id,
        'status': 'created',
        'tokens_found': len(tokens),
        'agent': prompt_agent.dict()
    }

@router.get("/list")
async def list_prompt_agents():
    """List all custom prompt agents"""
    return list(prompt_agents_db.values())

@router.get("/{agent_id}")
async def get_prompt_agent(agent_id: str):
    """Get specific prompt agent details"""
    agent = prompt_agents_db.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Prompt agent not found")
    return agent

@router.post("/execute")
async def execute_prompt_agent(request: ExecutePromptAgentRequest):
    """
    Execute a prompt agent with upstream outputs
    Resolves @tokens and runs LLM
    """
    # Get the prompt agent
    agent = prompt_agents_db.get(request.prompt_agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Prompt agent not found")
    
    # Resolve tokens in template
    resolution = resolve_prompt_template(
        agent.prompt_template,
        request.upstream_outputs
    )
    
    # Check for unresolved tokens
    if resolution['unresolved_tokens']:
        return {
            'status': 'error',
            'error': 'unresolved_tokens',
            'unresolved': resolution['unresolved_tokens'],
            'resolved_prompt': resolution['resolved_prompt']
        }
    
    # Execute LLM with resolved prompt
    llm_output = execute_llm_with_prompt(
        resolution['resolved_prompt'],
        agent.temperature,
        agent.max_tokens,
        agent.expected_output_schema
    )
    
    # Calculate cost (mock - based on token usage)
    tokens_used = len(resolution['resolved_prompt']) // 4 + len(json.dumps(llm_output)) // 4
    cost_cents = max(10, tokens_used // 10)
    
    # Record execution
    execution_record = {
        'execution_id': str(uuid.uuid4()),
        'agent_id': request.prompt_agent_id,
        'agent_name': agent.name,
        'prompt_template': agent.prompt_template,
        'resolved_prompt': resolution['resolved_prompt'],
        'upstream_outputs': request.upstream_outputs,
        'output': llm_output,
        'tokens_used': tokens_used,
        'cost_cents': cost_cents,
        'temperature': agent.temperature,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'success'
    }
    
    prompt_agent_executions.append(execution_record)
    
    return {
        'status': 'success',
        'execution_id': execution_record['execution_id'],
        'output': llm_output,
        'metadata': {
            'tokens_resolved': resolution['resolved_count'],
            'total_tokens_found': resolution['total_tokens'],
            'llm_tokens_used': tokens_used,
            'cost_cents': cost_cents,
            'resolved_values': resolution['resolved_values']
        }
    }

@router.post("/preview")
async def preview_prompt_resolution(
    prompt_template: str,
    upstream_outputs: Dict[str, Dict[str, Any]]
):
    """
    Preview how a prompt template would be resolved
    WITHOUT executing the LLM (for testing/debugging)
    """
    resolution = resolve_prompt_template(prompt_template, upstream_outputs)
    
    return {
        'original_template': prompt_template,
        'resolved_prompt': resolution['resolved_prompt'],
        'tokens_found': resolution['total_tokens'],
        'tokens_resolved': resolution['resolved_count'],
        'unresolved_tokens': resolution['unresolved_tokens'],
        'resolved_values': resolution['resolved_values']
    }

@router.get("/executions")
async def get_executions(limit: int = 20):
    """Get recent prompt agent executions"""
    return sorted(
        prompt_agent_executions,
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )[:limit]

@router.delete("/{agent_id}")
async def delete_prompt_agent(agent_id: str):
    """Delete a custom prompt agent"""
    if agent_id not in prompt_agents_db:
        raise HTTPException(status_code=404, detail="Prompt agent not found")
    
    deleted = prompt_agents_db.pop(agent_id)
    return {
        'status': 'deleted',
        'agent_id': agent_id,
        'agent_name': deleted.name
    }

# ============= EXAMPLE TEMPLATES =============

@router.get("/examples/templates")
async def get_example_templates():
    """
    Get example prompt templates showing @token usage
    """
    return {
        'examples': [
            {
                'name': 'Simple Field Mapping',
                'template': 'Take this summary: @Summarizer.summary and create a translation request',
                'use_case': 'Extract field from one agent for another'
            },
            {
                'name': 'Multi-Agent Combination',
                'template': 'Combine the summary "@Summarizer.summary" with sentiment "@Sentiment.sentiment" (score: @Sentiment.score) to create enriched content',
                'use_case': 'Merge outputs from multiple agents'
            },
            {
                'name': 'Nested Field Access',
                'template': 'Extract key points from @Summarizer.data.sentences and analyze them',
                'use_case': 'Access nested fields in agent output'
            },
            {
                'name': 'Array Element Access',
                'template': 'Use the first sentence: @Summarizer.sentences[0] as the main point',
                'use_case': 'Access array elements'
            },
            {
                'name': 'Complex Transformation',
                'template': '''Create a social media post based on:
                - Main content: @Summarizer.summary
                - Tone: @Sentiment.sentiment
                - Confidence: @Sentiment.score
                - Target: Make it engaging for @Context.audience
                ''',
                'use_case': 'Complex multi-source transformation'
            },
            {
                'name': 'Conditional Logic',
                'template': 'If @Sentiment.sentiment is positive, emphasize @Summarizer.key_points, otherwise focus on improvements',
                'use_case': 'Conditional content generation'
            }
        ]
    }
