from sqlalchemy import Column, String, Integer, Enum as SQLEnum, ForeignKey, JSON, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class ChainMode(str, enum.Enum):
    STRICT = "strict"
    BALANCED = "balanced"
    LENIENT = "lenient"

class MergeStrategy(str, enum.Enum):
    AUTHORITATIVE = "authoritative"
    CONCATENATE = "concatenate"
    SYNTHESIZE = "synthesize"

class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

class NodeStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMED_OUT = "timed_out"

class Chain(BaseModel):
    __tablename__ = "chains"
    
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    descriptor = Column(JSON, nullable=False)  # {nodes, edges, merge_strategy}
    mode = Column(SQLEnum(ChainMode), default=ChainMode.BALANCED)
    estimated_cost_cents = Column(Integer)
    
    # Relationships
    owner = relationship("User", back_populates="chains")
    runs = relationship("ChainRun", back_populates="chain")

class ChainRun(BaseModel):
    __tablename__ = "chain_runs"
    
    chain_id = Column(UUID(as_uuid=True), ForeignKey("chains.id"), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(RunStatus), default=RunStatus.PENDING)
    reserved_cents = Column(BigInteger, default=0)
    spent_cents = Column(BigInteger, default=0)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    trace_id = Column(String, unique=True, index=True)
    
    # Runtime options
    auto_apply_gat = Column(JSON, default=True)
    allow_llm = Column(JSON, default=False)
    budget_cents = Column(Integer)
    
    # Results
    final_output = Column(JSON)
    provenance_map = Column(JSON)  # Per-field provenance
    
    # Relationships
    chain = relationship("Chain", back_populates="runs")
    owner = relationship("User", back_populates="chain_runs")
    execution_logs = relationship("ExecutionLog", back_populates="run")
    transform_records = relationship("TransformRecord", back_populates="run")

class ExecutionLog(BaseModel):
    __tablename__ = "execution_logs"
    
    run_id = Column(UUID(as_uuid=True), ForeignKey("chain_runs.id"), nullable=False)
    step_index = Column(Integer, nullable=False)
    node_id = Column(String, nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    
    request_payload = Column(JSON)
    response_payload = Column(JSON)
    status = Column(SQLEnum(NodeStatus))
    duration_ms = Column(Integer)
    
    # Idempotency
    idempotency_key = Column(String, unique=True, index=True)
    
    # Relationships
    run = relationship("ChainRun", back_populates="execution_logs")
    agent = relationship("Agent", back_populates="execution_logs")
