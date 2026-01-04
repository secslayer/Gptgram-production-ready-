from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

from app.database import get_db
from app.models import Chain, ChainRun, User, Agent
from app.models.chain import ChainMode, MergeStrategy, RunStatus
from app.services.dag_orchestrator import DAGOrchestrator
from app.services.transform_pipeline import TransformPipeline
from app.services.agent_caller import AgentCaller
from app.services.wallet_service import WalletService
from app.services.provenance_tracker import ProvenanceTracker
from app.services.gat_service import GATService
from app.services.llm_gateway import LLMGateway
from app.services.vector_store import VectorStore
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/chains", tags=["chains"])

class NodeDescriptor(BaseModel):
    node_id: str
    agent_id: str
    node_name: Optional[str] = None
    node_metadata: dict = {}

class EdgeDescriptor(BaseModel):
    from_node: str
    to_node: str
    mapping_hint_id: Optional[str] = None

class ChainDescriptor(BaseModel):
    nodes: List[NodeDescriptor]
    edges: List[EdgeDescriptor]
    merge_strategy: MergeStrategy = MergeStrategy.AUTHORITATIVE

class ChainCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    descriptor: ChainDescriptor
    mode: ChainMode = ChainMode.BALANCED

class ChainResponse(BaseModel):
    id: str
    name: str
    descriptor: dict
    mode: str
    estimated_cost_cents: int
    owner_id: str

class RunOptions(BaseModel):
    auto_apply_gat: bool = True
    allow_llm: bool = False
    budget_cents: Optional[int] = None

class RunResponse(BaseModel):
    run_id: str
    status: str
    reserved_cents: int
    trace_id: str

class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    started_at: Optional[str]
    finished_at: Optional[str]
    spent_cents: int
    final_output: Optional[dict]
    provenance_map: Optional[dict]

@router.post("/", response_model=ChainResponse)
async def create_chain(
    chain_data: ChainCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chain/DAG"""
    
    # Validate agents exist
    agent_ids = [node.agent_id for node in chain_data.descriptor.nodes]
    result = await db.execute(
        select(Agent).where(Agent.id.in_(agent_ids))
    )
    agents = {str(a.id): a for a in result.scalars().all()}
    
    missing_agents = set(agent_ids) - set(agents.keys())
    if missing_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Agents not found: {missing_agents}"
        )
    
    # Calculate estimated cost
    estimated_cost = sum(agents[aid].price_cents for aid in agent_ids)
    
    # Add buffer for potential transforms
    estimated_cost = int(estimated_cost * 1.2)
    
    # Create chain
    chain = Chain(
        owner_user_id=current_user.id,
        name=chain_data.name,
        descriptor=chain_data.descriptor.dict(),
        mode=chain_data.mode,
        estimated_cost_cents=estimated_cost
    )
    
    db.add(chain)
    await db.commit()
    await db.refresh(chain)
    
    return ChainResponse(
        id=str(chain.id),
        name=chain.name,
        descriptor=chain.descriptor,
        mode=str(chain.mode.value),
        estimated_cost_cents=chain.estimated_cost_cents,
        owner_id=str(chain.owner_user_id)
    )

@router.get("/", response_model=List[ChainResponse])
async def list_chains(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's chains"""
    
    result = await db.execute(
        select(Chain)
        .where(Chain.owner_user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    chains = result.scalars().all()
    
    return [
        ChainResponse(
            id=str(chain.id),
            name=chain.name,
            descriptor=chain.descriptor,
            mode=str(chain.mode.value),
            estimated_cost_cents=chain.estimated_cost_cents,
            owner_id=str(chain.owner_user_id)
        )
        for chain in chains
    ]

@router.get("/{chain_id}", response_model=ChainResponse)
async def get_chain(
    chain_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chain details"""
    
    result = await db.execute(
        select(Chain).where(
            Chain.id == chain_id,
            Chain.owner_user_id == current_user.id
        )
    )
    chain = result.scalar_one_or_none()
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    return ChainResponse(
        id=str(chain.id),
        name=chain.name,
        descriptor=chain.descriptor,
        mode=str(chain.mode.value),
        estimated_cost_cents=chain.estimated_cost_cents,
        owner_id=str(chain.owner_user_id)
    )

@router.post("/{chain_id}/run", response_model=RunResponse)
async def run_chain(
    chain_id: str,
    run_options: RunOptions,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a chain"""
    
    # Get chain
    result = await db.execute(
        select(Chain).where(
            Chain.id == chain_id,
            Chain.owner_user_id == current_user.id
        )
    )
    chain = result.scalar_one_or_none()
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    # Check wallet balance
    wallet_service = WalletService(db)
    balance_info = await wallet_service.get_balance(current_user.id)
    
    required_amount = run_options.budget_cents or chain.estimated_cost_cents
    if balance_info["available_cents"] < required_amount:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient funds. Required: {required_amount}, Available: {balance_info['available_cents']}"
        )
    
    # Create run record
    trace_id = f"trace_{uuid.uuid4()}"
    chain_run = ChainRun(
        chain_id=chain.id,
        owner_user_id=current_user.id,
        status=RunStatus.PENDING,
        trace_id=trace_id,
        auto_apply_gat=run_options.auto_apply_gat,
        allow_llm=run_options.allow_llm,
        budget_cents=run_options.budget_cents
    )
    
    db.add(chain_run)
    await db.commit()
    await db.refresh(chain_run)
    
    # Start execution in background
    background_tasks.add_task(
        execute_chain_async,
        str(chain_run.id),
        chain.descriptor,
        db
    )
    
    return RunResponse(
        run_id=str(chain_run.id),
        status=str(chain_run.status.value),
        reserved_cents=0,  # Will be updated by executor
        trace_id=trace_id
    )

@router.get("/{chain_id}/runs", response_model=List[RunStatusResponse])
async def list_chain_runs(
    chain_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List runs for a chain"""
    
    result = await db.execute(
        select(ChainRun)
        .where(
            ChainRun.chain_id == chain_id,
            ChainRun.owner_user_id == current_user.id
        )
        .order_by(ChainRun.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    runs = result.scalars().all()
    
    return [
        RunStatusResponse(
            run_id=str(run.id),
            status=str(run.status.value),
            started_at=run.started_at.isoformat() if run.started_at else None,
            finished_at=run.finished_at.isoformat() if run.finished_at else None,
            spent_cents=run.spent_cents,
            final_output=run.final_output,
            provenance_map=run.provenance_map
        )
        for run in runs
    ]

@router.get("/runs/{run_id}", response_model=RunStatusResponse)
async def get_run_status(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get run status and results"""
    
    result = await db.execute(
        select(ChainRun).where(
            ChainRun.id == run_id,
            ChainRun.owner_user_id == current_user.id
        )
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return RunStatusResponse(
        run_id=str(run.id),
        status=str(run.status.value),
        started_at=run.started_at.isoformat() if run.started_at else None,
        finished_at=run.finished_at.isoformat() if run.finished_at else None,
        spent_cents=run.spent_cents,
        final_output=run.final_output,
        provenance_map=run.provenance_map
    )

@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running chain"""
    
    result = await db.execute(
        select(ChainRun).where(
            ChainRun.id == run_id,
            ChainRun.owner_user_id == current_user.id
        )
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.status not in [RunStatus.PENDING, RunStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel run with status {run.status}"
        )
    
    # Update status
    run.status = RunStatus.CANCELLED
    run.finished_at = datetime.utcnow()
    
    # Refund reserved funds
    wallet_service = WalletService(db)
    await wallet_service.refund_all(str(run.id))
    
    await db.commit()
    
    return {"message": "Run cancelled"}

@router.get("/{chain_id}/compatibility")
async def check_chain_compatibility(
    chain_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check compatibility scores for all edges in a chain"""
    
    # Get chain
    result = await db.execute(
        select(Chain).where(
            Chain.id == chain_id,
            Chain.owner_user_id == current_user.id
        )
    )
    chain = result.scalar_one_or_none()
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    # Get agents
    agent_ids = [node["agent_id"] for node in chain.descriptor.get("nodes", [])]
    result = await db.execute(
        select(Agent).where(Agent.id.in_(agent_ids))
    )
    agents = {str(a.id): a for a in result.scalars().all()}
    
    # Calculate compatibility for each edge
    vector_store = VectorStore()
    compatibility_results = []
    
    for edge in chain.descriptor.get("edges", []):
        from_agent = agents.get(
            next(n["agent_id"] for n in chain.descriptor["nodes"] if n["node_id"] == edge["from_node"])
        )
        to_agent = agents.get(
            next(n["agent_id"] for n in chain.descriptor["nodes"] if n["node_id"] == edge["to_node"])
        )
        
        if from_agent and to_agent:
            score = await vector_store.calculate_compatibility_score(
                from_agent.output_schema,
                to_agent.input_schema,
                from_agent.sample_response,
                to_agent.sample_request
            )
            
            compatibility_results.append({
                "from_node": edge["from_node"],
                "to_node": edge["to_node"],
                "score": score,
                "status": "compatible" if score > 0.7 else "needs_mapping" if score > 0.4 else "incompatible"
            })
    
    return {
        "chain_id": chain_id,
        "edges": compatibility_results,
        "overall_compatibility": sum(e["score"] for e in compatibility_results) / len(compatibility_results) if compatibility_results else 0
    }

async def execute_chain_async(
    run_id: str,
    chain_descriptor: dict,
    db: AsyncSession
):
    """Execute chain asynchronously"""
    
    try:
        # Get run
        result = await db.execute(
            select(ChainRun).where(ChainRun.id == run_id)
        )
        chain_run = result.scalar_one_or_none()
        
        if not chain_run:
            return
        
        # Initialize services
        transform_pipeline = TransformPipeline(
            db,
            GATService(db, VectorStore()),
            LLMGateway()
        )
        
        orchestrator = DAGOrchestrator(
            db,
            transform_pipeline,
            AgentCaller(),
            WalletService(db),
            ProvenanceTracker()
        )
        
        # Execute
        await orchestrator.execute_chain(chain_run, chain_descriptor)
        
    except Exception as e:
        logger.error(f"Chain execution failed: {str(e)}")
        
        # Update run status
        chain_run.status = RunStatus.FAILED
        chain_run.finished_at = datetime.utcnow()
        await db.commit()
