from sqlalchemy import Column, String, BigInteger, Enum as SQLEnum, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class TransactionType(str, enum.Enum):
    TOPUP = "topup"
    HOLD = "hold"
    SETTLE = "settle"
    REFUND = "refund"
    PAYOUT = "payout"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class Wallet(BaseModel):
    __tablename__ = "wallets"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    balance_cents = Column(BigInteger, default=0, nullable=False)
    reserved_cents = Column(BigInteger, default=0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="wallet")
    transactions = relationship("Transaction", back_populates="wallet")

class Transaction(BaseModel):
    __tablename__ = "transactions"
    
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    external_id = Column(String, unique=True, index=True)
    transaction_metadata = Column(JSON, default=dict)  # Additional transaction informations
    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")
