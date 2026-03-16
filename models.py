import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base
import enum

class TransactionType(enum.Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id"), nullable=False)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    description = Column(String, nullable=False)
    merchant_name = Column(String, nullable=True)
    balance_after_transaction = Column(Numeric(10, 2), nullable=True)

    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, account_id={self.account_id}, amount={self.amount})>"
