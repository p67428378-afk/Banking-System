import pytest
from services.transaction_history.main import app, get_db # Updated import
from services.transaction_history.models import Base, Account, Transaction, TransactionType # Updated import
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def client():
    # Create the tables in the test database
    Base.metadata.create_all(bind=engine)
    with app.test_client() as client:
        yield client
    # Drop the tables after tests are done
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Override the get_db dependency to use the test session
    def override_get_db():
        try:
            yield session
        finally:
            session.close()
            connection.close()

    app.dependency_overrides[get_db] = override_get_db
    yield session
    session.close()
    transaction.rollback()
    connection.close()

def test_get_transactions_no_data(client, db_session):
    account_id = uuid.uuid4()
    response = client.get(f"/transactions/{account_id}")
    assert response.status_code == 404
    assert "No transactions found" in response.json["message"]

def test_get_transactions_success(client, db_session):
    # Create an account
    account = Account(account_number="1234567890", customer_id=uuid.uuid4(), balance=1000.00)
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # Add transactions for the account
    transaction1 = Transaction(
        account_id=account.account_id,
        transaction_date=datetime.now() - timedelta(days=30),
        transaction_type=TransactionType.DEBIT,
        amount=50.00,
        description="Groceries",
    )
    transaction2 = Transaction(
        account_id=account.account_id,
        transaction_date=datetime.now() - timedelta(days=60),
        transaction_type=TransactionType.CREDIT,
        amount=200.00,
        description="Salary",
    )
    db_session.add_all([transaction1, transaction2])
    db_session.commit()

    response = client.get(f"/transactions/{account.account_id}")
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]["description"] == "Groceries" # Ordered by date desc

def test_get_transactions_filter_type(client, db_session):
    # Create an account
    account = Account(account_number="1234567891", customer_id=uuid.uuid4(), balance=500.00)
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # Add transactions
    transaction1 = Transaction(
        account_id=account.account_id,
        transaction_date=datetime.now() - timedelta(days=10),
        transaction_type=TransactionType.DEBIT,
        amount=25.00,
        description="Coffee",
    )
    transaction2 = Transaction(
        account_id=account.account_id,
        transaction_date=datetime.now() - timedelta(days=20),
        transaction_type=TransactionType.CREDIT,
        amount=150.00,
        description="Refund",
    )
    db_session.add_all([transaction1, transaction2])
    db_session.commit()

    response = client.get(f"/transactions/{account.account_id}?type=CREDIT")
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["transaction_type"] == "CREDIT"

def test_get_transactions_filter_date_range(client, db_session):
    account = Account(account_number="1234567892", customer_id=uuid.uuid4(), balance=2000.00)
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # Transactions within and outside the range
    t1 = Transaction(account_id=account.account_id, transaction_date=datetime.now() - timedelta(days=50), transaction_type=TransactionType.DEBIT, amount=100.00, description="T1")
    t2 = Transaction(account_id=account.account_id, transaction_date=datetime.now() - timedelta(days=20), transaction_type=TransactionType.CREDIT, amount=500.00, description="T2")
    t3 = Transaction(account_id=account.account_id, transaction_date=datetime.now() - timedelta(days=80), transaction_type=TransactionType.DEBIT, amount=20.00, description="T3")
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    end_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    response = client.get(f"/transactions/{account.account_id}?start_date={start_date}&end_date={end_date}")
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]["description"] == "T2"
    assert response.json[1]["description"] == "T1"

def test_get_transactions_filter_amount_range(client, db_session):
    account = Account(account_number="1234567893", customer_id=uuid.uuid4(), balance=300.00)
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    t1 = Transaction(account_id=account.account_id, transaction_date=datetime.now() - timedelta(days=10), transaction_type=TransactionType.DEBIT, amount=30.00, description="Small")
    t2 = Transaction(account_id=account.account_id, transaction_date=datetime.now() - timedelta(days=15), transaction_type=TransactionType.CREDIT, amount=150.00, description="Medium")
    t3 = Transaction(account_id=account.account_id, transaction_date=datetime.now() - timedelta(days=20), transaction_type=TransactionType.DEBIT, amount=500.00, description="Large")
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    response = client.get(f"/transactions/{account.account_id}?min_amount=50&max_amount=200")
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["description"] == "Medium"

def test_get_transactions_invalid_date_format(client, db_session):
    account_id = uuid.uuid4()
    response = client.get(f"/transactions/{account_id}?start_date=2023/01/01")
    assert response.status_code == 400
    assert "Invalid start_date format" in response.json["error"]

def test_get_transactions_start_date_after_end_date(client, db_session):
    account_id = uuid.uuid4()
    response = client.get(f"/transactions/{account_id}?start_date=2023-01-01&end_date=2022-12-31")
    assert response.status_code == 400
    assert "Start date cannot be after end date" in response.json["error"]

def test_get_transactions_date_range_outside_12_months(client, db_session):
    account_id = uuid.uuid4()
    old_date = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
    response = client.get(f"/transactions/{account_id}?start_date={old_date}")
    assert response.status_code == 400
    assert "Selected date range falls outside the last 12 months" in response.json["error"]

def test_get_transactions_invalid_type(client, db_session):
    account_id = uuid.uuid4()
    response = client.get(f"/transactions/{account_id}?type=INVALID")
    assert response.status_code == 400
    assert "Invalid transaction type" in response.json["error"]

def test_get_transactions_invalid_amount_format(client, db_session):
    account_id = uuid.uuid4()
    response = client.get(f"/transactions/{account_id}?min_amount=abc")
    assert response.status_code == 400
    assert "Invalid min_amount format" in response.json["error"]

def test_get_transactions_min_amount_greater_than_max_amount(client, db_session):
    account_id = uuid.uuid4()
    response = client.get(f"/transactions/{account_id}?min_amount=100&max_amount=50")
    assert response.status_code == 400
    assert "Minimum amount cannot be greater than maximum amount" in response.json["error"]
