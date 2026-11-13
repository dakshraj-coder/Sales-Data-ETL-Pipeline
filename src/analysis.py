"""
analysis.py  --  runs the SQL questions and builds the report + charts
-----------------------------------------------------------------------
Reads sql/analysis_queries.sql, runs each query on the SQLite database,
prints the results, saves charts (PNG) and a text report (Markdown).
"""

import logging
import re
import sqlite3
from datetime import datetime

import matplotlib

matplotlib.use("Agg")  # draw charts into files (no pop-up window needed)
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.config import DB_PATH, QUERIES_PATH, REPORTS_DIR  # noqa: E402

logger = logging.getLogger(__name__)


def read_queries(path=QUERIES_PATH):
    """
    Split the .sql file into separate queries.
    Each query begins with a line like:  -- name: top_10_products
    Returns a dictionary {query_name: sql_text}.
    """
    text = path.read_text(encoding="utf-8")
    # re.split with a capture group returns: [before, name1, sql1, name2, sql2, ...]
    parts = re.split(r"^-- name:\s*(\w+)\s*$", text, flags=re.MULTILINE)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def run_queries(db_path=DB_PATH, queries_path=QUERIES_PATH):
    """Run every query and return {query_name: DataFrame of results}."""
    results = {}
    conn = sqlite3.connect(db_path)
    try:
        for name, sql in read_queries(queries_path).items():
            results[name] = pd.read_sql_query(sql, conn)
            logger.info("Ran SQL query: %s (%d rows)", name, len(results[name]))
    finally:
        conn.close()
    return results


def print_results(results):
    """Show every query result in the terminal."""
    print("\n" + "=" * 70)
    print("SQL ANALYSIS RESULTS")
    print("=" * 70)
    for name, table in results.items():
        print(f"\n--- {name} ---")
        print(table.to_string(index=False))


def make_charts(results, out_dir=REPORTS_DIR):
    """Create three PNG charts in the reports/ folder."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Chart 1: monthly revenue (line)
    monthly = results["monthly_sales"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(monthly["order_month"], monthly["revenue"], marker="o")
    ax.set_title("Monthly Revenue")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (INR)")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_dir / "monthly_revenue.png", dpi=120)
    plt.close(fig)

    # Chart 2: top 10 products by units sold (horizontal bars)
    top = results["top_10_products"].sort_values("units_sold")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top["product_name"], top["units_sold"])
    ax.set_title("Top 10 Products by Units Sold")
    ax.set_xlabel("Units sold")
    fig.tight_layout()
    fig.savefig(out_dir / "top_products.png", dpi=120)
    plt.close(fig)

    # Chart 3: revenue by category (bars)
    cat = results["revenue_by_category"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(cat["category"], cat["revenue"])
    ax.set_title("Revenue by Category")
    ax.set_ylabel("Revenue (INR)")
    fig.tight_layout()
    fig.savefig(out_dir / "category_revenue.png", dpi=120)
    plt.close(fig)

    logger.info("Saved 3 charts to %s", out_dir)


def write_report(results, stats, out_dir=REPORTS_DIR):
    """Write reports/summary_report.md using the query results and pipeline statistics."""
    out_dir.mkdir(parents=True, exist_ok=True)

    revenue = results["total_revenue"].iloc[0]
    aov = results["average_order_value"].iloc[0, 0]
    best_category = results["revenue_by_category"].iloc[0]

    lines = [
        "# Sales ETL Summary Report",
        "",
        f"Generated on: {datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## Pipeline run",
        f"- Rows extracted from CSV files: {stats['rows_extracted']}",
        f"- Exact duplicates removed: {stats['exact_duplicates_removed']}",
        f"- Duplicate order IDs removed: {stats['duplicate_order_ids_removed']}",
        f"- Invalid rows rejected: {stats['rows_rejected']}",
        f"- Clean rows: {stats['rows_clean']}",
        f"- New rows inserted into the database: {stats['rows_inserted']}",
        f"- Rows skipped (already in the database): {stats['rows_skipped']}",
        "",
        "## Key results (from SQL queries)",
        f"- Total revenue: INR {revenue['total_revenue']:,.2f}",
        f"- Total orders: {int(revenue['total_orders'])}",
        f"- Average order value: INR {aov:,.2f}",
        f"- Highest-revenue category: {best_category['category']} "
        f"(INR {best_category['revenue']:,.2f})",
        "",
    ]

    sections = [
        ("Top 10 products by units sold", "top_10_products"),
        ("Revenue by category", "revenue_by_category"),
        ("Monthly sales", "monthly_sales"),
        ("Top 10 customers by revenue", "top_10_customers"),
    ]
    for title, key in sections:
        lines += [f"## {title}", "```", results[key].to_string(index=False), "```", ""]

    lines += ["Note: if the sample dataset is used, all figures come from synthetic data.", ""]

    report_path = out_dir / "summary_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Saved summary report to %s", report_path)


def run_analysis(stats, db_path=DB_PATH):
    """Run all queries, print them, then create charts and the report."""
    results = run_queries(db_path)
    print_results(results)
    make_charts(results)
    write_report(results, stats)
    return results
