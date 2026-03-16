"""
Module: models
Purpose: Defines the SQLAlchemy models for the banking system.
Author: Gemini
Created: 2023-10-27
"""

import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Numeric, Enum, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import enum

# Define the base for declarative models
Base = declarative_base()

class TransactionType(enum.Enum):
    """
    Enum for transaction types.
    """
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

class Transaction(Base):
    """
    Represents a financial transaction in the banking system.
    """
    __tablename__ = 'transactions'

    transaction_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String, nullable=False, index=True)  # Assuming account_id is a string for now
    transaction_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    description = Column(String, nullable=True)
    merchant_name = Column(String, nullable=True)
    balance_after_transaction = Column(Numeric(10, 2), nullable=True)

    def __repr__(self):
        return (f"<Transaction(transaction_id='{self.transaction_id}', account_id='{self.account_id}', "
                f"type='{self.transaction_type.value}', amount='{self.amount}', date='{self.transaction_date}')>")

    def to_dict(self):
        """
        Converts the Transaction object to a dictionary.
        """
        return {
            "transaction_id": str(self.transaction_id),
            "account_id": self.account_id,
            "transaction_date": self.transaction_date.isoformat(),
            "transaction_type": self.transaction_type.value,
            "amount": float(self.amount),
            "currency": self.currency,
            "description": self.description,
            "merchant_name": self.merchant_name,
            "balance_after_transaction": float(self.balance_after_transaction) if self.balance_after_transaction else None,
        }

# Example of how to set up the engine and session (for local testing/development)
# In a real application, this would be managed by a configuration system
DATABASE_URL = "sqlite:///./test.db"  # Use SQLite for local development

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initializes the database by creating all defined tables.
    """
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized and tables created.")
    # Example usage:
    # from sqlalchemy.orm import Session
    # with SessionLocal() as session:
    #     new_transaction = Transaction(
    #         account_id="user123",
    #         transaction_type=TransactionType.DEBIT,
    #         amount=50.00,
    #         description="Coffee purchase",
    #         merchant_name="Starbucks"
    #     )
    #     session.add(new_transaction)
    #     session.commit()
    #     print(f"Added transaction: {new_transaction}")
    #     transactions = session.query(Transaction).all()
    #     print("All transactions:")
    #     for t in transactions:
    #         print(t.to_dict())
