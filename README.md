# Banking System - Transaction History Service

## Project Overview

This project implements the Transaction History Service as part of a larger Banking System. The service allows bank customers to view their detailed transaction history, filter transactions by date range, type (credit/debit), and amount, and provides a placeholder for downloading statements as PDF.

## Architecture Notes

The Transaction History Service is designed as a microservice, adhering to the principles outlined in the High-Level Design (HLD) document for Jira issue SCRUM-54. It interacts with a relational database to retrieve transaction data and exposes a RESTful API for frontend consumption.

**Key Components:**

*   **Flask Application (`app.py`):** Handles API requests for transaction history, applies filtering and pagination logic, and interacts with the database.
*   **SQLAlchemy Models (`models.py`):** Defines the `Transaction` data model and handles database interactions.
*   **PDF Generation Service Placeholder (`pdf_service.py`):** A separate Flask application that will eventually handle PDF statement generation. Currently, it returns a placeholder response.

## Setup Instructions

To set up and run the Transaction History Service locally, follow these steps:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/p67428378-afk/Banking-System.git
    cd Banking-System
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the database:**

    The `models.py` script will create a SQLite database file (`test.db`) in the project root if it doesn't exist. You can run it directly:

    ```bash
    python src/models.py
    ```

5.  **Run the Transaction History Service:**

    ```bash
    export FLASK_APP=src/app.py
    flask run --port 5000
    ```

    The API will be available at `http://127.0.0.1:5000`.

6.  **Run the PDF Generation Service (Placeholder):**

    ```bash
    export FLASK_APP=src/pdf_service.py
    flask run --port 5001
    ```

    The PDF service placeholder will be available at `http://127.0.0.1:5001`.

## Usage Examples

### Get All Transactions for an Account (last 12 months)

```bash
curl "http://127.0.0.1:5000/api/v1/transactions?account_id=user123"
```

### Filter by Date Range

```bash
curl "http://127.0.0.1:5000/api/v1/transactions?account_id=user123&start_date=2023-01-01&end_date=2023-03-31"
```

### Filter by Transaction Type

```bash
curl "http://127.0.0.1:5000/api/v1/transactions?account_id=user123&transaction_type=DEBIT"
```

### Filter by Amount Range

```bash
curl "http://127.0.0.1:5000/api/v1/transactions?account_id=user123&min_amount=50.00&max_amount=200.00"
```

### Combined Filters and Pagination

```bash
curl "http://127.0.0.1:5000/api/v1/transactions?account_id=user123&start_date=2023-01-01&transaction_type=CREDIT&min_amount=10.00&page=2&per_page=5"
```

### Download PDF Statement (Placeholder)

```bash
curl "http://127.0.0.1:5001/api/v1/transactions/pdf?account_id=user123"
```

## Database Schema

The `Transaction` table has the following structure:

*   `transaction_id` (Primary Key, UUID)
*   `account_id` (Foreign Key, String)
*   `transaction_date` (Timestamp with timezone)
*   `transaction_type` (Enum: 'CREDIT', 'DEBIT')
*   `amount` (Decimal)
*   `currency` (String, e.g., 'USD', 'EUR')
*   `description` (String, optional)
*   `merchant_name` (String, optional)
*   `balance_after_transaction` (Decimal, optional)

## Testing

To run tests, ensure you have `pytest` installed (included in `requirements.txt`).

```bash
pytest
```

(Note: Specific test files will be added in a separate commit.)
