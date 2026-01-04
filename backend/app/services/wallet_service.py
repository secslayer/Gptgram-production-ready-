from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models import Wallet, Transaction, User
from app.models.wallet import TransactionType, TransactionStatus
from app.core.logging import logger

class WalletService:
    """Handles wallet operations with idempotent transactions"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.platform_fee_percent = 20  # 20% platform fee

    async def create_wallet(self, user_id: str) -> Wallet:
        """Create a new wallet for user"""
        
        wallet = Wallet(
            user_id=user_id,
            balance_cents=0,
            reserved_cents=0,
            currency="USD"
        )
        self.db.add(wallet)
        await self.db.commit()
        
        return wallet

    async def get_wallet(self, user_id: str) -> Wallet:
        """Get user's wallet"""
        
        result = await self.db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            wallet = await self.create_wallet(user_id)
        
        return wallet

    async def create_hold(
        self,
        user_id: str,
        amount_cents: int,
        external_id: str
    ) -> str:
        """Create a hold on wallet funds (idempotent)"""
        
        # Check for existing transaction
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.external_id == external_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info(f"Hold already exists: {external_id}")
            return external_id
        
        # Get wallet
        wallet = await self.get_wallet(user_id)
        
        # Check sufficient balance
        available = wallet.balance_cents - wallet.reserved_cents
        if available < amount_cents:
            raise ValueError(f"Insufficient funds. Available: {available}, Required: {amount_cents}")
        
        # Create hold transaction
        transaction = Transaction(
            wallet_id=wallet.id,
            type=TransactionType.HOLD,
            amount_cents=amount_cents,
            status=TransactionStatus.COMPLETED,
            external_id=external_id,
            transaction_metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        self.db.add(transaction)
        
        # Update reserved amount
        wallet.reserved_cents += amount_cents
        
        await self.db.commit()
        
        logger.info(f"Created hold: {external_id} for {amount_cents} cents")
        return external_id

    async def settle_node_payment(
        self,
        run_id: str,
        node_id: str,
        amount_cents: int
    ) -> str:
        """Settle payment for a successful node execution"""
        
        external_id = f"settle_{run_id}_{node_id}"
        
        # Check for existing settlement
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.external_id == external_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info(f"Settlement already exists: {external_id}")
            return external_id
        
        # Get run owner's wallet
        from app.models import ChainRun
        run_result = await self.db.execute(
            select(ChainRun).where(ChainRun.id == run_id)
        )
        chain_run = run_result.scalar_one_or_none()
        
        if not chain_run:
            raise ValueError(f"Chain run {run_id} not found")
        
        wallet = await self.get_wallet(chain_run.owner_user_id)
        
        # Calculate platform fee
        platform_fee = int(amount_cents * self.platform_fee_percent / 100)
        agent_payment = amount_cents - platform_fee
        
        # Create settlement transaction
        transaction = Transaction(
            wallet_id=wallet.id,
            type=TransactionType.SETTLE,
            amount_cents=amount_cents,
            status=TransactionStatus.COMPLETED,
            external_id=external_id,
            transaction_metadata={
                "node_id": node_id,
                "platform_fee": platform_fee,
                "agent_payment": agent_payment
            }
        )
        self.db.add(transaction)
        
        # Update reserved amount
        wallet.reserved_cents = max(0, wallet.reserved_cents - amount_cents)
        
        # TODO: Credit agent owner's wallet with agent_payment
        
        await self.db.commit()
        
        logger.info(f"Settled payment: {external_id} for {amount_cents} cents")
        return external_id

    async def refund_node_payment(
        self,
        run_id: str,
        node_id: str
    ) -> str:
        """Refund reserved amount for failed node"""
        
        external_id = f"refund_{run_id}_{node_id}"
        
        # Check for existing refund
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.external_id == external_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info(f"Refund already exists: {external_id}")
            return external_id
        
        # Get run and estimate node cost
        from app.models import ChainRun, Agent
        run_result = await self.db.execute(
            select(ChainRun).where(ChainRun.id == run_id)
        )
        chain_run = run_result.scalar_one_or_none()
        
        if not chain_run:
            raise ValueError(f"Chain run {run_id} not found")
        
        # For simplicity, refund a fixed amount
        # In production, track exact reserved amount per node
        refund_amount = 50  # cents
        
        wallet = await self.get_wallet(chain_run.owner_user_id)
        
        # Create refund transaction
        transaction = Transaction(
            wallet_id=wallet.id,
            type=TransactionType.REFUND,
            amount_cents=refund_amount,
            status=TransactionStatus.COMPLETED,
            external_id=external_id,
            transaction_metadata={
                "node_id": node_id,
                "reason": "node_failed"
            }
        )
        self.db.add(transaction)
        
        # Update reserved amount
        wallet.reserved_cents = max(0, wallet.reserved_cents - refund_amount)
        wallet.balance_cents += refund_amount
        
        await self.db.commit()
        
        logger.info(f"Refunded: {external_id} for {refund_amount} cents")
        return external_id

    async def refund_unused(
        self,
        run_id: str,
        amount_cents: int
    ) -> str:
        """Refund unused reserved funds after run completion"""
        
        external_id = f"refund_unused_{run_id}"
        
        # Check for existing refund
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.external_id == external_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return external_id
        
        # Get run owner's wallet
        from app.models import ChainRun
        run_result = await self.db.execute(
            select(ChainRun).where(ChainRun.id == run_id)
        )
        chain_run = run_result.scalar_one_or_none()
        
        if not chain_run:
            raise ValueError(f"Chain run {run_id} not found")
        
        wallet = await self.get_wallet(chain_run.owner_user_id)
        
        # Create refund transaction
        transaction = Transaction(
            wallet_id=wallet.id,
            type=TransactionType.REFUND,
            amount_cents=amount_cents,
            status=TransactionStatus.COMPLETED,
            external_id=external_id,
            transaction_metadata={
                "reason": "unused_budget"
            }
        )
        self.db.add(transaction)
        
        # Update amounts
        wallet.reserved_cents = max(0, wallet.reserved_cents - amount_cents)
        
        await self.db.commit()
        
        logger.info(f"Refunded unused: {external_id} for {amount_cents} cents")
        return external_id

    async def refund_all(self, run_id: str):
        """Refund all reserved funds for a failed run"""
        
        external_id = f"refund_all_{run_id}"
        
        # Check for existing refund
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.external_id == external_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return
        
        # Get run and wallet
        from app.models import ChainRun
        run_result = await self.db.execute(
            select(ChainRun).where(ChainRun.id == run_id)
        )
        chain_run = run_result.scalar_one_or_none()
        
        if not chain_run:
            return
        
        wallet = await self.get_wallet(chain_run.owner_user_id)
        
        # Refund full reserved amount
        refund_amount = chain_run.reserved_cents
        
        if refund_amount > 0:
            transaction = Transaction(
                wallet_id=wallet.id,
                type=TransactionType.REFUND,
                amount_cents=refund_amount,
                status=TransactionStatus.COMPLETED,
                external_id=external_id,
                transaction_metadata={
                    "reason": "run_failed"
                }
            )
            self.db.add(transaction)
            
            wallet.reserved_cents = max(0, wallet.reserved_cents - refund_amount)
            
            await self.db.commit()
            
            logger.info(f"Refunded all: {external_id} for {refund_amount} cents")

    async def topup_wallet(
        self,
        user_id: str,
        amount_cents: int,
        stripe_event_id: str
    ) -> str:
        """Top up wallet from Stripe payment (idempotent)"""
        
        # Check for existing transaction
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.external_id == stripe_event_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info(f"Topup already processed: {stripe_event_id}")
            return stripe_event_id
        
        # Get wallet
        wallet = await self.get_wallet(user_id)
        
        # Create topup transaction
        transaction = Transaction(
            wallet_id=wallet.id,
            type=TransactionType.TOPUP,
            amount_cents=amount_cents,
            status=TransactionStatus.COMPLETED,
            external_id=stripe_event_id,
            transaction_metadata={
                "payment_method": "stripe",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        self.db.add(transaction)
        
        # Update balance
        wallet.balance_cents += amount_cents
        
        await self.db.commit()
        
        logger.info(f"Wallet topped up: {stripe_event_id} for {amount_cents} cents")
        return stripe_event_id

    async def get_balance(self, user_id: str) -> dict:
        """Get wallet balance and reserved amounts"""
        
        wallet = await self.get_wallet(user_id)
        
        return {
            "balance_cents": wallet.balance_cents,
            "reserved_cents": wallet.reserved_cents,
            "available_cents": wallet.balance_cents - wallet.reserved_cents,
            "currency": wallet.currency
        }

    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """Get transaction history for user"""
        
        wallet = await self.get_wallet(user_id)
        
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.wallet_id == wallet.id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        transactions = result.scalars().all()
        
        return [
            {
                "id": str(t.id),
                "type": str(t.type.value),
                "amount_cents": t.amount_cents,
                "status": str(t.status.value),
                "created_at": t.created_at.isoformat(),
                "metadata": t.transaction_metadata
            }
            for t in transactions
        ]
