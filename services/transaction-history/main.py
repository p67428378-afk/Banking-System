from flask import Flask, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import and_, cast, Date
from datetime import datetime, timedelta
from .database import SessionLocal, engine, Base # Updated import
from .models import Transaction, TransactionType # Updated import
from .config import Config # Updated import

app = Flask(__name__)
app.config.from_object(Config)

# Create database tables
Base.metadata.create_all(bind=engine)

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.route("/transactions/<uuid:account_id>", methods=["GET"])
def get_transactions(account_id):
    db: Session = next(get_db())
    
    # Default to last 12 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # Filters from query parameters
    req_start_date = request.args.get("start_date")
    req_end_date = request.args.get("end_date")
    transaction_type = request.args.get("type")
    min_amount = request.args.get("min_amount")
    max_amount = request.args.get("max_amount")

    # Apply date range filter
    if req_start_date:
        try:
            start_date = datetime.strptime(req_start_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD."}), 400
    if req_end_date:
        try:
            end_date = datetime.strptime(req_end_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD."}), 400

    if start_date > end_date:
        return jsonify({"error": "Start date cannot be after end date."}), 400
    
    # Ensure date range is within the last 12 months from today
    twelve_months_ago = datetime.now() - timedelta(days=365)
    if start_date < twelve_months_ago.replace(hour=0, minute=0, second=0, microsecond=0):
        return jsonify({"error": "Selected date range falls outside the last 12 months."}), 400

    transactions = db.query(Transaction).filter(Transaction.account_id == account_id)

    transactions = transactions.filter(cast(Transaction.transaction_date, Date) >= start_date.date())
    transactions = transactions.filter(cast(Transaction.transaction_date, Date) <= end_date.date())

    if transaction_type:
        try:
            transactions = transactions.filter(Transaction.transaction_type == TransactionType[transaction_type.upper()])
        except KeyError:
            return jsonify({"error": "Invalid transaction type. Use 'CREDIT' or 'DEBIT'."}), 400

    if min_amount:
        try:
            min_amount = float(min_amount)
            transactions = transactions.filter(Transaction.amount >= min_amount)
        except ValueError:
            return jsonify({"error": "Invalid min_amount format."}), 400

    if max_amount:
        try:
            max_amount = float(max_amount)
            transactions = transactions.filter(Transaction.amount <= max_amount)
        except ValueError:
            return jsonify({"error": "Invalid max_amount format."}), 400

    if min_amount and max_amount and min_amount > max_amount:
        return jsonify({"error": "Minimum amount cannot be greater than maximum amount."}), 400

    transactions = transactions.order_by(Transaction.transaction_date.desc()).all()

    if not transactions:
        return jsonify({"message": "No transactions found for the given criteria."}), 404

    return jsonify([
        {
            "transaction_id": str(t.transaction_id),
            "account_id": str(t.account_id),
            "transaction_date": t.transaction_date.isoformat(),
            "transaction_type": t.transaction_type.value,
            "amount": str(t.amount),
            "currency": t.currency,
            "description": t.description,
            "merchant_name": t.merchant_name,
            "balance_after_transaction": str(t.balance_after_transaction) if t.balance_after_transaction else None,
        }
        for t in transactions
    ]), 200

if __name__ == "__main__":
    app.run(debug=True)
