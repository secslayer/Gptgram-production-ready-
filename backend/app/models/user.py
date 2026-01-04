from sqlalchemy import Column, String, Enum as SQLEnum, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class UserRole(str, enum.Enum):
    USER = "user"
    CREATOR = "creator"
    ADMIN = "admin"

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    last_login_at = Column(DateTime(timezone=True))
    profile = Column(JSON, default=dict)
    
    # Relationships
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    agents = relationship("Agent", back_populates="owner")
    chains = relationship("Chain", back_populates="owner")
    chain_runs = relationship("ChainRun", back_populates="owner")
