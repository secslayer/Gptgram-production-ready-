from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

from app.database import get_db
from app.models import Agent, User
from app.models.agent import AgentType, AuthType, VerificationLevel, AgentStatus
from app.services.agent_caller import AgentCaller
from app.services.vector_store import VectorStore
from app.services.llm_gateway import LLMGateway
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/agents", tags=["agents"])

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    type: AgentType
    endpoint_url: str
    auth: dict
    price_cents: int = Field(ge=0, le=10000)
    input_schema: dict
    output_schema: dict
    sample_request: Optional[dict] = None
    sample_response: Optional[dict] = None
    rate_limit: int = Field(default=100, ge=1, le=1000)

class AgentResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    type: str
    endpoint_url: str
    price_cents: int
    verification_level: str
    status: str
    input_schema: dict
    output_schema: dict
    metrics: Optional[dict]
    owner_id: Optional[str]

class AgentVerifyResponse(BaseModel):
    agent_id: str
    verification_level: str
    tests: List[dict]
    recommendations: List[str]
    verification_report: dict

@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent with A2A compliance"""
    
    # Generate slug
    slug = agent_data.name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
    
    # Create A2A capability manifest
    capability_manifest = {
        "id": str(uuid.uuid4()),
        "name": agent_data.name,
        "version": "1.0.0",
        "input_schema": agent_data.input_schema,
        "output_schema": agent_data.output_schema,
        "auth": agent_data.auth,
        "examples": {
            "sample_request": agent_data.sample_request,
            "sample_response": agent_data.sample_response
        },
        "rate_limit": agent_data.rate_limit,
        "verification_policy": {
            "min_tests": 3,
            "timeout_ms": 30000
        }
    }
    
    # Create agent
    agent = Agent(
        owner_user_id=current_user.id,
        name=agent_data.name,
        slug=slug,
        description=agent_data.description,
        type=agent_data.type,
        endpoint_url=agent_data.endpoint_url,
        auth=agent_data.auth,
        price_cents=agent_data.price_cents,
        input_schema=agent_data.input_schema,
        output_schema=agent_data.output_schema,
        sample_request=agent_data.sample_request,
        sample_response=agent_data.sample_response,
        capability_manifest=capability_manifest,
        rate_limit=agent_data.rate_limit,
        status=AgentStatus.PENDING,
        verification_level=VerificationLevel.UNVERIFIED
    )
    
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    
    # Index in vector store
    vector_store = VectorStore()
    await vector_store.index_agent(
        str(agent.id),
        agent.name,
        agent.description or "",
        agent.input_schema,
        agent.output_schema,
        agent.sample_response or {},
        {
            "verification_level": str(agent.verification_level),
            "price_cents": agent.price_cents
        }
    )
    
    # Trigger async verification
    # TODO: Queue verification task
    
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        slug=agent.slug,
        description=agent.description,
        type=str(agent.type),
        endpoint_url=agent.endpoint_url,
        price_cents=agent.price_cents,
        verification_level=str(agent.verification_level),
        status=str(agent.status),
        input_schema=agent.input_schema,
        output_schema=agent.output_schema,
        metrics=agent.metrics_cache,
        owner_id=str(agent.owner_user_id) if agent.owner_user_id else None
    )

@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    verification_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List agents with optional search and filters"""
    
    if search:
        # Use vector search
        vector_store = VectorStore()
        search_results = await vector_store.search_agents(
            search,
            top_k=limit,
            filters={
                "min_verification_level": verification_level
            } if verification_level else None
        )
        
        # Get full agent data
        agent_ids = [r["agent_id"] for r in search_results]
        
        result = await db.execute(
            select(Agent).where(Agent.id.in_(agent_ids))
        )
        agents = result.scalars().all()
    else:
        # Regular list query
        query = select(Agent).where(Agent.status == AgentStatus.ACTIVE)
        
        if verification_level:
            query = query.where(Agent.verification_level == verification_level)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        agents = result.scalars().all()
    
    return [
        AgentResponse(
            id=str(agent.id),
            name=agent.name,
            slug=agent.slug,
            description=agent.description,
            type=str(agent.type),
            endpoint_url=agent.endpoint_url,
            price_cents=agent.price_cents,
            verification_level=str(agent.verification_level),
            status=str(agent.status),
            input_schema=agent.input_schema,
            output_schema=agent.output_schema,
            metrics=agent.metrics_cache,
            owner_id=str(agent.owner_user_id) if agent.owner_user_id else None
        )
        for agent in agents
    ]

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get agent details"""
    
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        slug=agent.slug,
        description=agent.description,
        type=str(agent.type),
        endpoint_url=agent.endpoint_url,
        price_cents=agent.price_cents,
        verification_level=str(agent.verification_level),
        status=str(agent.status),
        input_schema=agent.input_schema,
        output_schema=agent.output_schema,
        metrics=agent.metrics_cache,
        owner_id=str(agent.owner_user_id) if agent.owner_user_id else None
    )

@router.post("/{agent_id}/verify", response_model=AgentVerifyResponse)
async def verify_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Run verification tests on an agent"""
    
    # Get agent
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check ownership
    if agent.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Run verification
    agent_caller = AgentCaller()
    verification_result = await agent_caller.verify_agent(agent)
    
    # Update agent
    agent.verification_level = VerificationLevel(verification_result["verification_level"])
    agent.verification_report = verification_result
    agent.status = AgentStatus.ACTIVE if agent.verification_level != VerificationLevel.UNVERIFIED else AgentStatus.PENDING
    
    await db.commit()
    
    # Generate improvement recommendations if needed
    if agent.verification_level in [VerificationLevel.UNVERIFIED, VerificationLevel.L1]:
        llm_gateway = LLMGateway()
        fixes = await llm_gateway.generate_verification_fixes(
            verification_result["tests"],
            agent.output_schema
        )
        verification_result["recommendations"].extend(fixes)
    
    return AgentVerifyResponse(
        agent_id=str(agent.id),
        verification_level=str(agent.verification_level),
        tests=verification_result["tests"],
        recommendations=verification_result["recommendations"],
        verification_report=verification_result
    )

@router.post("/{agent_id}/test")
async def test_agent(
    agent_id: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test an agent with custom payload"""
    
    # Get agent
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Call agent
    agent_caller = AgentCaller()
    
    try:
        response = await agent_caller.call_agent(
            agent,
            payload,
            f"test_{agent_id}_{uuid.uuid4()}",
            f"test_{current_user.id}"
        )
        
        return {
            "status": "success",
            "response": response,
            "latency_ms": agent.metrics_cache.get("avg_latency_ms") if agent.metrics_cache else None
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/{agent_id}/well-known/a2a")
async def get_agent_a2a_manifest(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get A2A capability manifest for agent (A2A Discovery)"""
    
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Return A2A manifest
    return agent.capability_manifest or {
        "id": str(agent.id),
        "name": agent.name,
        "version": "1.0.0",
        "input_schema": agent.input_schema,
        "output_schema": agent.output_schema,
        "endpoint": agent.endpoint_url,
        "auth": {
            "type": agent.auth.get("type") if agent.auth else "none"
        },
        "rate_limit": agent.rate_limit,
        "price": {
            "amount": agent.price_cents,
            "currency": "USD_CENTS"
        }
    }
