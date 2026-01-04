from sqlalchemy import Column, String, Integer, Enum as SQLEnum, ForeignKey, JSON, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class AgentType(str, enum.Enum):
    N8N = "n8n"
    CUSTOM = "custom"
    LOCAL_MOCK = "local_mock"

class AuthType(str, enum.Enum):
    HMAC = "hmac"
    JWT = "jwt"
    NONE = "none"

class VerificationLevel(str, enum.Enum):
    UNVERIFIED = "unverified"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"

class AgentStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"

class Agent(BaseModel):
    __tablename__ = "agents"
    
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    type = Column(SQLEnum(AgentType), nullable=False)
    endpoint_url = Column(String, nullable=False)
    
    # A2A Compliance Fields
    auth = Column(JSON, nullable=False)  # {type: enum, secret_name: str}
    price_cents = Column(Integer, default=0, nullable=False)
    input_schema = Column(JSON, nullable=False)  # JSON Schema
    output_schema = Column(JSON, nullable=False)  # JSON Schema
    sample_request = Column(JSON)
    sample_response = Column(JSON)
    
    # Verification & Status
    verification_level = Column(SQLEnum(VerificationLevel), default=VerificationLevel.UNVERIFIED)
    verification_report = Column(JSON)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.PENDING)
    
    # Metrics
    last_called_at = Column(DateTime(timezone=True))
    metrics_cache = Column(JSON, default=dict)  # {avg_latency_ms, success_rate, call_volume}
    
    # A2A Discovery
    capability_manifest = Column(JSON)  # Full A2A capability manifest
    rate_limit = Column(Integer, default=100)  # Requests per minute
    
    # Relationships
    owner = relationship("User", back_populates="agents")
    execution_logs = relationship("ExecutionLog", back_populates="agent")
