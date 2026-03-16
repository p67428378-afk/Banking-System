"""
Module: test_app
Purpose: Unit tests for the Transaction History Service API.
Author: Gemini
Created: 2023-10-27
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app import app
from src.models import Base, Transaction, TransactionType

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Provides a transactional test session for the database.
    """
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Seed data
    seed_data(session)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """
    Provides a test client for the Flask application.
    """
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URL"] = SQLALCHEMY_DATABASE_URL # Override for testing

    # Override the session in the app to use the test session
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    # This part is a bit tricky with Flask and SQLAlchemy outside of a framework like FastAPI
    # For simplicity in this test, we'll ensure the app uses the test_db_session directly
    # by patching or ensuring the SessionLocal in app.py points to TestingSessionLocal
    # For this example, we'll assume app.py's SessionLocal is correctly configured
    # or we'll mock it if necessary. For now, we rely on init_db() and the fixture.

    with app.test_client() as client:
        yield client

def seed_data(session):
    """
    Seeds the database with dummy transaction data.
    """
    # Transactions for user123
    session.add_all([
        Transaction(
            account_id="user123",
            transaction_date=datetime.utcnow() - timedelta(days=5),
            transaction_type=TransactionType.DEBIT,
            amount=25.50,
            currency="USD",
            description="Coffee Shop",
            merchant_name="Starbucks"
        ),
        Transaction(
            account_id="user123",
            transaction_date=datetime.utcnow() - timedelta(days=15),
            transaction_type=TransactionType.CREDIT,
            amount=100.00,
            currency="USD",
            description="Salary Deposit",
            merchant_name="Employer"
        ),
        Transaction(
            account_id="user123",
            transaction_date=datetime.utcnow() - timedelta(days=30),
            transaction_type=TransactionType.DEBIT,
            amount=75.00,
            currency="USD",
            description="Groceries",
            merchant_name="Whole Foods"
        ),
        Transaction(
            account_id="user123",
            transaction_date=datetime.utcnow() - timedelta(days=400),
            transaction_type=TransactionType.CREDIT,
            amount=200.00,
            currency="USD",
            description="Old Transaction",
            merchant_name="Old Employer"
        ), # This should be outside 12 months filter
        Transaction(
            account_id="user123",
            transaction_date=datetime.utcnow() - timedelta(days=2),
            transaction_type=TransactionType.DEBIT,
            amount=150.00,
            currency="USD",
            description="Electronics",
            merchant_name="Best Buy"
        ),
        Transaction(
            account_id="user123",
            transaction_date=datetime.utcnow() - timedelta(days=10),
            transaction_type=TransactionType.CREDIT,
            amount=500.00,
            currency="USD",
            description="Bonus",
            merchant_name="Employer"
        ),
    ])

    # Transactions for user456
    session.add_all([
        Transaction(
            account_id="user456",
            transaction_date=datetime.utcnow() - timedelta(days=10),
            transaction_type=TransactionType.DEBIT,
            amount=30.00,
            currency="USD",
            description="Lunch",
            merchant_name="Local Cafe"
        )
    ])
    session.commit()

# Test cases for /api/v1/transactions

def test_get_transactions_no_account_id(client):
    response = client.get('/api/v1/transactions')
    assert response.status_code == 400
    assert "account_id is required" in response.json["error"]

def test_get_transactions_no_transactions_found(client, db_session):
    # Clear existing data for a specific account to test this scenario
    session = db_session
    session.query(Transaction).filter(Transaction.account_id == "user789").delete()
    session.commit()

    response = client.get('/api/v1/transactions?account_id=user789')
    assert response.status_code == 200
    assert "No transactions found for this account within the last 12 months." in response.json["message"]

def test_get_transactions_success(client, db_session):
    response = client.get('/api/v1/transactions?account_id=user123')
    assert response.status_code == 200
    assert len(response.json["transactions"]) == 5 # 1 transaction is older than 12 months
    assert response.json["total_transactions"] == 5

def test_get_transactions_filter_by_date_range(client, db_session):
    # Transactions from seed_data:
    # -5 days (Debit 25.50)
    # -15 days (Credit 100.00)
    # -30 days (Debit 75.00)
    # -2 days (Debit 150.00)
    # -10 days (Credit 500.00)

    # Filter for last 10 days
    start_date = (datetime.utcnow() - timedelta(days=10)).strftime('%Y-%m-%d')
    end_date = datetime.utcnow().strftime('%Y-%m-%d')
    response = client.get(f'/api/v1/transactions?account_id=user123&start_date={start_date}&end_date={end_date}')
    assert response.status_code == 200
    # Expected: -5 days, -2 days, -10 days (3 transactions)
    assert len(response.json["transactions"]) == 3
    assert response.json["total_transactions"] == 3

def test_get_transactions_filter_by_transaction_type(client, db_session):
    response = client.get('/api/v1/transactions?account_id=user123&transaction_type=CREDIT')
    assert response.status_code == 200
    # Expected: -15 days (100.00), -10 days (500.00) (2 transactions)
    assert len(response.json["transactions"]) == 2
    assert response.json["total_transactions"] == 2

def test_get_transactions_filter_by_amount_range(client, db_session):
    response = client.get('/api/v1/transactions?account_id=user123&min_amount=50&max_amount=100')
    assert response.status_code == 200
    # Expected: -15 days (100.00), -30 days (75.00) (2 transactions)
    assert len(response.json["transactions"]) == 2
    assert response.json["total_transactions"] == 2

def test_get_transactions_pagination(client, db_session):
    response = client.get('/api/v1/transactions?account_id=user123&page=1&per_page=2')
    assert response.status_code == 200
    assert len(response.json["transactions"]) == 2
    assert response.json["total_transactions"] == 5
    assert response.json["page"] == 1
    assert response.json["per_page"] == 2
    assert response.json["total_pages"] == 3

    response = client.get('/api/v1/transactions?account_id=user123&page=3&per_page=2')
    assert response.status_code == 200
    assert len(response.json["transactions"]) == 1 # Last page has 1 transaction

def test_get_transactions_invalid_date_range(client):
    response = client.get('/api/v1/transactions?account_id=user123&start_date=2024-01-01&end_date=2023-01-01')
    assert response.status_code == 400
    assert "Start date cannot be after end date." in response.json["error"]

def test_get_transactions_invalid_amount_range(client):
    response = client.get('/api/v1/transactions?account_id=user123&min_amount=100&max_amount=50')
    assert response.status_code == 400
    assert "Minimum amount cannot be greater than maximum amount." in response.json["error"]

def test_get_transactions_start_date_too_old(client):
    start_date = (datetime.utcnow() - timedelta(days=400)).strftime('%Y-%m-%d')
    response = client.get(f'/api/v1/transactions?account_id=user123&start_date={start_date}')
    assert response.status_code == 400
    assert "Start date cannot be older than 12 months ago." in response.json["error"]

# Test cases for /api/v1/transactions/pdf (placeholder)

def test_generate_pdf_no_account_id(client):
    response = client.get('/api/v1/transactions/pdf')
    assert response.status_code == 400
    assert "account_id is required" in response.json["error"]

def test_generate_pdf_placeholder_response(client):
    response = client.get('/api/v1/transactions/pdf?account_id=user123')
    assert response.status_code == 501
    assert "PDF generation is not yet implemented." in response.json["message"]
