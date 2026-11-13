# End-to-End Sales Data ETL Pipeline (Python + SQL)

A beginner-friendly Data Engineering project that **extracts** raw sales data from several CSV files, **cleans and transforms** it with Python (pandas), **loads** it into a SQLite database, and answers business questions with SQL.

> **Note on data:** the CSV files in `data/raw/` are **synthetic (made-up) sample data** created by `src/generate_sample_data.py`. They are deliberately messy so the cleaning logic has real work to do. Any numbers shown below come from that synthetic data and are not real business results.

## Features

- **Extract**: reads multiple CSV files, normalises column names, validates required columns, reports row and column counts
- **Clean**: strips whitespace, standardises text case, unifies payment-method spellings, parses mixed date formats, converts price text such as `Rs. 1,299.00` to numbers, removes duplicates, fills recoverable gaps, rejects invalid rows with a recorded reason
- **Transform**: calculates `total_sales`, `discount_amount`, `revenue`, `order_month`; builds product, category, monthly and customer summary tables
- **Load**: creates a relational SQLite schema (3 tables plus an audit table) and loads data **idempotently**: re-running does not insert duplicates
- **Analyse**: SQL queries for top products, total revenue, best category, monthly trend, top customers, average order value
- **Report**: Markdown summary report, three PNG charts, cleaned CSV exports, a CSV of rejected records
- **Operate**: one command to run everything, logging to console and file, error handling, `--reset` and path options

## Architecture

```
 data/raw/*.csv                      (3 messy CSV files)
        |
        v
 [ EXTRACT ]  src/extract.py         read files, tidy headers, combine, profile
        |
        v
 [  CLEAN  ]  src/transform.py       fix formats, remove duplicates, validate
        |                \
        |                 +--> data/processed/rejected_records.csv
        v
 [TRANSFORM]  src/transform.py       revenue, monthly/product/customer summaries
        |
        +--> data/processed/*.csv    cleaned data + summary tables
        v
 [  LOAD   ]  src/load.py            SQLite: customers, products, sales, etl_runs
        |
        v
 database/sales.db
        |
        v
 [ ANALYSE ]  src/analysis.py        runs sql/analysis_queries.sql
        |
        +--> reports/summary_report.md
        +--> reports/*.png (charts)
```

### Database design

```
customers (customer_id PK, customer_name, city)
products  (product_id PK, product_name, category)
sales     (order_id PK, order_date, order_month,
           customer_id FK -> customers, product_id FK -> products,
           quantity, unit_price, discount_percent,
           total_sales, discount_amount, revenue,
           payment_method, source_file)
etl_runs  (run_id PK, run_timestamp, rows_extracted, rows_rejected,
           rows_clean, rows_inserted, rows_skipped)
```

## Project structure

```
sales-data-etl/
    data/raw/                 input CSV files
    data/processed/           cleaned data and summary CSVs (generated)
    database/                 SQLite database file (generated)
    notebooks/                data exploration notebook
    src/
        config.py             paths and settings
        extract.py            read CSV files
        transform.py          clean + transform
        load.py               create tables and load data
        analysis.py           SQL analysis, charts, report
        utils.py              logging setup
        generate_sample_data.py   creates the synthetic sample data
    sql/schema.sql            table definitions
    sql/analysis_queries.sql  business questions as SQL
    reports/                  summary report and charts (generated)
    logs/                     pipeline log file (generated)
    main.py                   runs the whole pipeline
    requirements.txt
```

## Installation

Requires **Python 3.9 or newer**.

**Windows 11 (PowerShell)**
```powershell
git clone https://github.com/dakshraj-coder/sales-data-etl.git
cd sales-data-etl
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS (Terminal)**
```bash
git clone https://github.com/dakshraj-coder/sales-data-etl.git
cd sales-data-etl
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Automated tests

Run the beginner-friendly unit tests from the project root:

```bash
python -m unittest discover -s tests -v
```

The tests cover date parsing, currency-to-number conversion, revenue calculations,
and duplicate-safe database loading. The test database is created in a temporary
folder and does not overwrite your project database.

## Usage

```bash
python main.py            # run the full pipeline (use python3 on macOS)
python main.py --reset    # delete the database and rebuild from scratch
python main.py --raw-dir path/to/csvs --db-path path/to/file.db
python src/generate_sample_data.py   # regenerate the sample CSV files
```

To use your own data, put CSV files in `data/raw/` with these columns:
`order_id, order_date, customer_id, customer_name, city, product_id, product_name, category, quantity, unit_price, discount_percent, payment_method`.

## Data cleaning rules

| Problem | What the pipeline does |
|---|---|
| Extra spaces, mixed upper/lower case | Strips spaces and standardises case |
| `upi`, `UPI `, `COD`, `cash on delivery` | Mapped to one standard spelling |
| Dates as `2024-01-15`, `15/01/2024`, `15 Jan 2024` | Parsed to one format (day-first is assumed for `/` and `-`) |
| Prices such as `Rs. 1,299.00` | Converted to numbers |
| Exact duplicate rows, repeated `order_id` | Removed (first kept) |
| Missing name/city/product name/category | Filled from other rows with the same ID, else `Unknown` |
| Missing discount | Treated as 0% |
| Missing IDs, impossible dates, future dates, bad quantity/price/discount | Row rejected and saved to `rejected_records.csv` with a reason |

## SQL analysis

All queries are in [`sql/analysis_queries.sql`](sql/analysis_queries.sql): top 10 products, total revenue, revenue by category, monthly sales, top 10 customers, and average order value.

## Sample output (synthetic data)

Running `python main.py` on the included sample files produced:

- 735 rows extracted, 15 exact duplicates removed, 38 invalid rows rejected, 682 clean rows loaded
- Re-running the pipeline inserts 0 new rows (682 skipped as already present)

See `reports/summary_report.md` after running for the full results.

## Screenshots

Add your own screenshots here after running the project.

| Terminal output | Monthly revenue chart |
|---|---|
| `![Terminal](docs/terminal.png)` | `![Monthly revenue](reports/monthly_revenue.png)` |

## Limitations

- SQLite is used for easy setup; it is not meant for large multi-user workloads
- The load is append-only: an existing `order_id` is skipped, not updated (use `--reset` for a full rebuild)
- Date parsing assumes day-first formats
- The pipeline is run manually; there is no scheduler
- The sample dataset is small and synthetic

## Possible future improvements

- Add automated tests with `pytest`
- Load data in chunks for larger files
- Learn and add scheduling with Apache Airflow
- Learn and try PySpark for larger datasets
- Move the database to PostgreSQL or MySQL

## Author

dakshraj-coder
