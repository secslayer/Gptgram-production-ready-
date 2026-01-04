from sqlalchemy import Column, String, Integer, Enum as SQLEnum, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class TransformMethod(str, enum.Enum):
    DETERMINISTIC = "deterministic"
    MAPPING_HINT = "mapping_hint"
    GAT = "gat"
    LLM = "llm"

class TransformRecord(BaseModel):
    __tablename__ = "transform_records"
    
    run_id = Column(UUID(as_uuid=True), ForeignKey("chain_runs.id"), nullable=False)
    from_node = Column(String, nullable=False)
    to_node = Column(String, nullable=False)
    method = Column(SQLEnum(TransformMethod), nullable=False)
    
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("mapping_hints.id"), nullable=True)
    prompt_id = Column(String)  # If LLM used
    
    tokens_used = Column(Integer, default=0)
    cost_cents = Column(Integer, default=0)
    validated = Column(Boolean, default=False)
    attempts = Column(Integer, default=1)
    
    # Transform details
    input_data = Column(JSON)
    output_data = Column(JSON)
    confidence = Column(JSON)  # 0.0 to 1.0
    
    # Relationships
    run = relationship("ChainRun", back_populates="transform_records")
    mapping_hint = relationship("MappingHint", back_populates="transform_records")

class MappingHint(BaseModel):
    __tablename__ = "mapping_hints"
    
    source_schema_fp = Column(String, nullable=False, index=True)
    target_schema_fp = Column(String, nullable=False, index=True)
    recipe = Column(JSON, nullable=False)  # Array of operations
    
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    
    # GAT-suggested metadata
    gat_confidence = Column(JSON)
    attention_trace = Column(JSON)
    
    # Relationships
    transform_records = relationship("TransformRecord", back_populates="mapping_hint")
