"""
Run History API
Tracks and stores chain execution history
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/runs", tags=["runs"])

# Data models
class RunCreate(BaseModel):
    chain_id: str
    status: str = "running"
    nodes: List[str]
    outputs: Dict[str, Any] = {}

class RunUpdate(BaseModel):
    status: Optional[str] = None
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class Run(BaseModel):
    run_id: str
    chain_id: str
    status: str
    nodes: List[str]
    outputs: Dict[str, Any]
    total_cost: int = 0
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None

# Storage
runs_db = []

# Endpoints
@router.post("/create")
async def create_run(run_data: RunCreate):
    """Create a new run"""
    run = Run(
        run_id=str(uuid.uuid4()),
        chain_id=run_data.chain_id,
        status=run_data.status,
        nodes=run_data.nodes,
        outputs=run_data.outputs,
        started_at=datetime.now(timezone.utc).isoformat()
    )
    runs_db.append(run.dict())
    return run

@router.get("/")
async def get_runs(limit: int = 20):
    """Get run history"""
    return sorted(runs_db, key=lambda x: x.get("started_at", ""), reverse=True)[:limit]

@router.get("/{run_id}")
async def get_run(run_id: str):
    """Get specific run"""
    for run in runs_db:
        if run["run_id"] == run_id:
            return run
    raise HTTPException(status_code=404, detail="Run not found")

@router.put("/{run_id}")
async def update_run(run_id: str, update: RunUpdate):
    """Update run status"""
    for i, run in enumerate(runs_db):
        if run["run_id"] == run_id:
            if update.status:
                run["status"] = update.status
            if update.outputs:
                run["outputs"] = update.outputs
            if update.error:
                run["error"] = update.error
            if update.status == "completed":
                run["completed_at"] = datetime.now(timezone.utc).isoformat()
                # Calculate total cost from outputs
                total_cost = 0
                if update.outputs:
                    for output in update.outputs.values():
                        if isinstance(output, dict):
                            total_cost += output.get('price_cents', 0)
                run["total_cost"] = total_cost
            runs_db[i] = run
            return run
    raise HTTPException(status_code=404, detail="Run not found")
