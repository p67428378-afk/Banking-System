"""
Module: app
Purpose: Implements the Transaction History Service API.
Author: Gemini
Created: 2023-10-27
"""

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from src.models import SessionLocal, Transaction, TransactionType, init_db

app = Flask(__name__)

# Initialize the database (create tables if they don't exist)
init_db()

@app.route('/api/v1/transactions', methods=['GET'])
def get_transactions():
    """
    Retrieves and filters transaction history for a given account.

    Query Parameters:
        account_id (str): The ID of the customer account (required).
        start_date (str): Start date for filtering (YYYY-MM-DD).
        end_date (str): End date for filtering (YYYY-MM-DD).
        transaction_type (str): Filter by 'CREDIT' or 'DEBIT'.
        min_amount (float): Minimum transaction amount.
        max_amount (float): Maximum transaction amount.
        page (int): Page number for pagination (default: 1).
        per_page (int): Number of transactions per page (default: 10, max: 100).

    Returns:
        JSON: A list of filtered transactions and pagination metadata.
    """
    account_id = request.args.get('account_id')
    if not account_id:
        return jsonify({"error": "account_id is required"}), 400

    session = SessionLocal()
    try:
        query = session.query(Transaction).filter(Transaction.account_id == account_id)

        # Filter by last 12 months by default
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        query = query.filter(Transaction.transaction_date >= twelve_months_ago)

        # Date Range Filtering
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                if start_date < twelve_months_ago:
                    return jsonify({"error": "Start date cannot be older than 12 months ago."}), 400
                query = query.filter(Transaction.transaction_date >= start_date)
            except ValueError:
                return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD."}), 400

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(microseconds=1) # Include end of day
                query = query.filter(Transaction.transaction_date <= end_date)
            except ValueError:
                return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD."}), 400

        if start_date_str and end_date_str and start_date > end_date:
            return jsonify({"error": "Start date cannot be after end date."}), 400

        # Transaction Type Filtering
        transaction_type_str = request.args.get('transaction_type')
        if transaction_type_str:
            try:
                transaction_type = TransactionType[transaction_type_str.upper()]
                query = query.filter(Transaction.transaction_type == transaction_type)
            except KeyError:
                return jsonify({"error": "Invalid transaction_type. Must be 'CREDIT' or 'DEBIT'."}), 400

        # Amount Filtering
        min_amount_str = request.args.get('min_amount')
        max_amount_str = request.args.get('max_amount')

        if min_amount_str:
            try:
                min_amount = float(min_amount_str)
                query = query.filter(Transaction.amount >= min_amount)
            except ValueError:
                return jsonify({"error": "Invalid min_amount format. Must be a number."}), 400

        if max_amount_str:
            try:
                max_amount = float(max_amount_str)
                query = query.filter(Transaction.amount <= max_amount)
            except ValueError:
                return jsonify({"error": "Invalid max_amount format. Must be a number."}), 400

        if min_amount_str and max_amount_str and float(min_amount_str) > float(max_amount_str):
            return jsonify({"error": "Minimum amount cannot be greater than maximum amount."}), 400

        # Order by transaction date descending
        query = query.order_by(Transaction.transaction_date.desc())

        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        per_page = min(per_page, 100) # Cap per_page at 100

        total_transactions = query.count()
        transactions = query.offset((page - 1) * per_page).limit(per_page).all()

        if not transactions and (start_date_str or end_date_str or transaction_type_str or min_amount_str or max_amount_str):
            return jsonify({"message": "No transactions found matching the criteria."}), 200
        elif not transactions:
            return jsonify({"message": "No transactions found for this account within the last 12 months."}), 200

        return jsonify({
            "transactions": [t.to_dict() for t in transactions],
            "total_transactions": total_transactions,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_transactions + per_page - 1) // per_page
        })

    except Exception as e:
        app.logger.error(f"Error retrieving transactions: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
