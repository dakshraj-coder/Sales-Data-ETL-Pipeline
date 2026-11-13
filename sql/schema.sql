-- schema.sql
-- Defines the database tables. "IF NOT EXISTS" means running this file again is safe:
-- existing tables (and their data) are left alone.

-- Dimension table: one row per customer
CREATE TABLE IF NOT EXISTS customers (
    customer_id    TEXT PRIMARY KEY,
    customer_name  TEXT NOT NULL,
    city           TEXT NOT NULL
);

-- Dimension table: one row per product
CREATE TABLE IF NOT EXISTS products (
    product_id     TEXT PRIMARY KEY,
    product_name   TEXT NOT NULL,
    category       TEXT NOT NULL
);

-- Fact table: one row per order line (what was sold, to whom, when, for how much)
-- The PRIMARY KEY on order_id is what stops the same order being inserted twice.
CREATE TABLE IF NOT EXISTS sales (
    order_id          TEXT PRIMARY KEY,
    order_date        TEXT NOT NULL,          -- stored as 'YYYY-MM-DD'
    order_month       TEXT NOT NULL,          -- stored as 'YYYY-MM'
    customer_id       TEXT NOT NULL,
    product_id        TEXT NOT NULL,
    quantity          INTEGER NOT NULL CHECK (quantity > 0),
    unit_price        REAL    NOT NULL CHECK (unit_price > 0),
    discount_percent  REAL    NOT NULL CHECK (discount_percent BETWEEN 0 AND 100),
    total_sales       REAL    NOT NULL,       -- quantity * unit_price (before discount)
    discount_amount   REAL    NOT NULL,
    revenue           REAL    NOT NULL,       -- total_sales - discount_amount
    payment_method    TEXT    NOT NULL,
    source_file       TEXT,                   -- which CSV the row came from
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
    FOREIGN KEY (product_id)  REFERENCES products (product_id)
);

-- Indexes make GROUP BY / JOIN queries faster on bigger data.
CREATE INDEX IF NOT EXISTS idx_sales_month    ON sales (order_month);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales (customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_product  ON sales (product_id);

-- A small audit table: one row each time the pipeline runs.
CREATE TABLE IF NOT EXISTS etl_runs (
    run_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp     TEXT NOT NULL,
    rows_extracted    INTEGER,
    rows_rejected     INTEGER,
    rows_clean        INTEGER,
    rows_inserted     INTEGER,
    rows_skipped      INTEGER
);
