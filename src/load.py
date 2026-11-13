"""
load.py  --  step 3 of ETL: LOAD
--------------------------------
Creates the SQLite database and inserts the clean data into it.
Running the pipeline twice does NOT create duplicate rows (see load_sales).
"""

import logging
import sqlite3

import pandas as pd
from datetime import datetime
from pathlib import Path

from src.config import DB_PATH, SCHEMA_PATH

logger = logging.getLogger(__name__)


def get_connection(db_path=DB_PATH):
    """Open (or create) the SQLite database file."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")  # make SQLite enforce FOREIGN KEY rules
    return conn


def create_tables(conn, schema_path=SCHEMA_PATH):
    """Run sql/schema.sql to create the tables (safe to run many times)."""
    conn.executescript(Path(schema_path).read_text(encoding="utf-8"))
    logger.info("Database tables are ready")


def _rows(df, columns):
    """Turn selected DataFrame columns into a list of tuples that SQLite can insert."""
    # Convert NumPy / pandas scalar values to native Python types.
    # sqlite3 can otherwise bind NumPy integers as binary blobs, which can
    # make CHECK constraints fail even when the displayed value looks valid.
    rows = []
    for row in df[columns].itertuples(index=False, name=None):
        values = []
        for value in row:
            if value is None:
                values.append(None)
            elif value is pd.NA:
                values.append(None)
            elif hasattr(value, "item"):
                values.append(value.item())
            else:
                values.append(value)
        rows.append(tuple(values))
    return rows


def count_rows(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def load_customers(conn, sales_df):
    """
    Insert one row per customer. If the customer already exists, UPDATE the name/city
    ("upsert" = update + insert). So re-running keeps customer details current.
    """
    customers = sales_df.drop_duplicates(subset="customer_id", keep="last")
    conn.executemany(
        """
        INSERT INTO customers (customer_id, customer_name, city)
        VALUES (?, ?, ?)
        ON CONFLICT(customer_id) DO UPDATE SET
            customer_name = excluded.customer_name,
            city          = excluded.city
        """,
        _rows(customers, ["customer_id", "customer_name", "city"]),
    )
    return len(customers)


def load_products(conn, sales_df):
    """Same upsert idea for products."""
    products = sales_df.drop_duplicates(subset="product_id", keep="last")
    conn.executemany(
        """
        INSERT INTO products (product_id, product_name, category)
        VALUES (?, ?, ?)
        ON CONFLICT(product_id) DO UPDATE SET
            product_name = excluded.product_name,
            category     = excluded.category
        """,
        _rows(products, ["product_id", "product_name", "category"]),
    )
    return len(products)


def load_sales(conn, sales_df):
    """
    Insert sales rows. 'INSERT OR IGNORE' skips any row whose order_id (the PRIMARY KEY)
    is already in the table. This is how we avoid duplicates when the pipeline re-runs.
    Returns (rows_inserted, rows_skipped).
    """
    columns = ["order_id", "order_date", "order_month", "customer_id", "product_id",
               "quantity", "unit_price", "discount_percent", "total_sales",
               "discount_amount", "revenue", "payment_method", "source_file"]
    placeholders = ", ".join("?" for _ in columns)

    before = count_rows(conn, "sales")
    conn.executemany(
        f"INSERT OR IGNORE INTO sales ({', '.join(columns)}) VALUES ({placeholders})",
        _rows(sales_df, columns),
    )
    after = count_rows(conn, "sales")

    inserted = after - before
    skipped = len(sales_df) - inserted
    return inserted, skipped


def record_run(conn, stats):
    """Save one line in etl_runs describing this pipeline run."""
    conn.execute(
        """
        INSERT INTO etl_runs (run_timestamp, rows_extracted, rows_rejected, rows_clean,
                              rows_inserted, rows_skipped)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (datetime.now().isoformat(timespec="seconds"), stats["rows_extracted"],
         stats["rows_rejected"], stats["rows_clean"], stats["rows_inserted"],
         stats["rows_skipped"]),
    )


def load_data(sales_df, stats, db_path=DB_PATH, schema_path=SCHEMA_PATH):
    """
    Create the tables and load everything inside ONE transaction:
    if anything fails halfway, all changes are rolled back (nothing half-loaded).
    """
    conn = get_connection(db_path)
    try:
        create_tables(conn, schema_path)
        with conn:  # 'with conn' = commit if OK, rollback if an error happens
            n_customers = load_customers(conn, sales_df)
            n_products = load_products(conn, sales_df)
            inserted, skipped = load_sales(conn, sales_df)
            stats["rows_inserted"] = inserted
            stats["rows_skipped"] = skipped
            record_run(conn, stats)

        logger.info("Loaded: %d customers, %d products processed", n_customers, n_products)
        logger.info("Loaded sales: %d new rows inserted, %d already existed (skipped)",
                    inserted, skipped)
        logger.info("Rows now in sales table: %d", count_rows(conn, "sales"))
    finally:
        conn.close()
    return stats
