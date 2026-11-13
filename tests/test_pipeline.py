"""Beginner-friendly tests for the Sales ETL pipeline.

Run from the project root with: python -m unittest discover -s tests -v
"""
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.transform import parse_date, to_number, add_calculated_columns
from src.load import get_connection, create_tables, load_data
from src.config import SCHEMA_PATH


class TransformTests(unittest.TestCase):
    def test_parse_indian_date(self):
        self.assertEqual(parse_date("15/01/2024").strftime("%Y-%m-%d"), "2024-01-15")

    def test_parse_iso_date(self):
        self.assertEqual(parse_date("2024-02-20").strftime("%Y-%m-%d"), "2024-02-20")

    def test_invalid_date_returns_none(self):
        self.assertIsNone(parse_date("31/02/2024"))

    def test_currency_text_to_number(self):
        values = pd.Series(["Rs. 1,299.00", "₹699", "invalid"])
        converted = to_number(values)
        self.assertEqual(converted.iloc[0], 1299.00)
        self.assertEqual(converted.iloc[1], 699.00)
        self.assertTrue(pd.isna(converted.iloc[2]))

    def test_revenue_calculation(self):
        df = pd.DataFrame({
            "quantity": [2],
            "unit_price": [100.0],
            "discount_percent": [10.0],
            "order_date": pd.to_datetime(["2024-01-15"]),
        })
        result = add_calculated_columns(df)
        self.assertEqual(result.loc[0, "total_sales"], 200.0)
        self.assertEqual(result.loc[0, "discount_amount"], 20.0)
        self.assertEqual(result.loc[0, "revenue"], 180.0)
        self.assertEqual(result.loc[0, "order_month"], "2024-01")


class LoadTests(unittest.TestCase):
    def test_loading_same_order_twice_does_not_duplicate(self):
        sales = pd.DataFrame([{
            "order_id": "TEST-001",
            "order_date": "2024-01-15",
            "order_month": "2024-01",
            "customer_id": "C-001",
            "product_id": "P-001",
            "quantity": 2,
            "unit_price": 100.0,
            "discount_percent": 10.0,
            "total_sales": 200.0,
            "discount_amount": 20.0,
            "revenue": 180.0,
            "payment_method": "UPI",
            "source_file": "test.csv",
            "customer_name": "Test Customer",
            "city": "Hyderabad",
            "product_name": "Test Product",
            "category": "Testing",
        }])
        stats = {
            "rows_extracted": 1,
            "rows_rejected": 0,
            "rows_clean": 1,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            first = load_data(sales, stats.copy(), db_path=db_path)
            second = load_data(sales, stats.copy(), db_path=db_path)

            self.assertEqual(first["rows_inserted"], 1)
            self.assertEqual(second["rows_inserted"], 0)
            self.assertEqual(second["rows_skipped"], 1)

            conn = get_connection(db_path)
            try:
                count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
                self.assertEqual(count, 1)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
