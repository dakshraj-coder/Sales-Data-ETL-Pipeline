"""
config.py
---------
One place for all settings (folder paths, required columns, date formats).
If you ever need to change a path, you change it here only.
"""

from pathlib import Path

# BASE_DIR = the main project folder (sales-data-etl/).
# __file__ is this file (src/config.py). .parent = src/, .parent.parent = project folder.
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_PATH = BASE_DIR / "database" / "sales.db"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"
QUERIES_PATH = BASE_DIR / "sql" / "analysis_queries.sql"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Every raw CSV file must contain these columns (after we tidy the header names).
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "customer_id",
    "customer_name",
    "city",
    "product_id",
    "product_name",
    "category",
    "quantity",
    "unit_price",
    "discount_percent",
    "payment_method",
]

# Date formats we accept in the raw files. We assume day comes before month
# (DD/MM/YYYY), which is the normal convention in India.
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y"]

# Different spellings of the same payment method -> one standard spelling.
PAYMENT_METHOD_MAP = {
    "upi": "UPI",
    "credit card": "Credit Card",
    "debit card": "Debit Card",
    "net banking": "Net Banking",
    "cash on delivery": "Cash on Delivery",
    "cod": "Cash on Delivery",
}
