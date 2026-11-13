"""
transform.py  --  step 2 of ETL: TRANSFORM
------------------------------------------
Two jobs:
  1. CLEAN the raw data (fix formats, remove duplicates, reject invalid rows)
  2. TRANSFORM the clean data (calculate sales/revenue, build summary tables)
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import DATE_FORMATS, PAYMENT_METHOD_MAP, PROCESSED_DIR

logger = logging.getLogger(__name__)

TEXT_COLUMNS = [
    "order_id", "order_date", "customer_id", "customer_name", "city", "product_id",
    "product_name", "category", "quantity", "unit_price", "discount_percent",
    "payment_method",
]


# ----------------------------------------------------------------------------
# Small helper functions
# ----------------------------------------------------------------------------
def parse_date(value):
    """
    Turn a date written as text into a real date.
    Tries each format in DATE_FORMATS. Returns None if nothing works
    (for example '31/02/2024' or 'not available').
    """
    if pd.isna(value):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def to_number(series):
    """
    Turn text like 'Rs. 1,299.00' or '\u20b9699' into the number 1299.0 / 699.0.
    Anything that cannot become a number turns into NaN (= 'missing').
    """
    cleaned = series.astype("string").str.strip()
    cleaned = cleaned.str.replace(r"(?i)rs\.?|inr|₹", "", regex=True)
    cleaned = cleaned.str.replace(",", "", regex=False)
    only_digits = cleaned.str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(only_digits, errors="coerce")


# ----------------------------------------------------------------------------
# CLEANING
# ----------------------------------------------------------------------------
def standardize_text(df):
    """Fix spaces and upper/lower case so the same thing is always written the same way."""
    df = df.copy()

    for col in TEXT_COLUMNS:
        cleaned = df[col].str.strip().str.replace(r"\s+", " ", regex=True)
        df[col] = cleaned.mask(cleaned == "")  # empty text -> missing

    df["customer_name"] = df["customer_name"].str.title()
    df["city"] = df["city"].str.title()
    df["category"] = df["category"].str.title()
    for col in ["order_id", "customer_id", "product_id"]:
        df[col] = df[col].str.upper()

    # 'upi', 'UPI ' -> 'UPI' ; 'cod' -> 'Cash on Delivery'
    lowered = df["payment_method"].str.lower()
    df["payment_method"] = lowered.map(PAYMENT_METHOD_MAP).fillna(df["payment_method"].str.title())
    return df


def fill_from_same_id(df):
    """
    If a customer's name/city is missing in one row but known in another row with the same
    customer_id, copy it over. Same idea for product name/category.
    """
    df = df.copy()
    for key, cols in [("customer_id", ["customer_name", "city"]),
                      ("product_id", ["product_name", "category"])]:
        for col in cols:
            known_value = df.groupby(key)[col].transform("first")
            df[col] = df[col].fillna(known_value)
    return df


def clean_data(raw_df):
    """
    Clean the raw DataFrame.
    Returns: (clean_df, rejected_df, stats)
      clean_df    - rows that passed every check
      rejected_df - rows that failed, with a 'reject_reason' column explaining why
      stats       - a dictionary of counts, used for logging and the report
    """
    stats = {"rows_extracted": len(raw_df)}

    # 1) Standardise text, then fill gaps that can be recovered from other rows.
    text_df = fill_from_same_id(standardize_text(raw_df))

    # 2) Remove duplicates. First: rows identical in every column (ignoring source_file).
    compare_cols = [c for c in text_df.columns if c != "source_file"]
    exact_dupes = text_df.duplicated(subset=compare_cols, keep="first")
    text_df = text_df.loc[~exact_dupes]
    stats["exact_duplicates_removed"] = int(exact_dupes.sum())
    #    Second: same order_id appearing twice with different details -> keep the first.
    id_dupes = text_df["order_id"].notna() & text_df.duplicated(subset=["order_id"], keep="first")
    text_df = text_df.loc[~id_dupes]
    stats["duplicate_order_ids_removed"] = int(id_dupes.sum())

    # 3) Convert text to proper data types (dates and numbers).
    typed = text_df.copy()
    typed["order_date"] = pd.to_datetime(text_df["order_date"].map(parse_date), errors="coerce")
    typed["quantity"] = to_number(text_df["quantity"])
    typed["unit_price"] = to_number(text_df["unit_price"])
    discount = to_number(text_df["discount_percent"])
    typed["discount_percent"] = discount.mask(text_df["discount_percent"].isna(), 0)  # none given = 0%

    # 4) Validation rules. Each rule is a True/False value per row; True = row is bad.
    today = pd.Timestamp.today().normalize()
    rules = {
        "missing order_id": typed["order_id"].isna(),
        "missing customer_id": typed["customer_id"].isna(),
        "missing product_id": typed["product_id"].isna(),
        "invalid or missing order_date": typed["order_date"].isna(),
        "order_date is in the future": typed["order_date"] > today,
        "invalid quantity": typed["quantity"].isna() | (typed["quantity"] <= 0) | (typed["quantity"] % 1 != 0),
        "invalid unit_price": typed["unit_price"].isna() | (typed["unit_price"] <= 0),
        "invalid discount_percent": typed["discount_percent"].isna()
                                    | (typed["discount_percent"] < 0)
                                    | (typed["discount_percent"] > 100),
    }

    reasons = pd.Series("", index=typed.index)
    for message, is_bad in rules.items():
        reasons.loc[is_bad] = reasons.loc[is_bad] + message + "; "
    is_rejected = reasons != ""

    # 5) Split into clean and rejected rows.
    rejected_df = text_df.loc[is_rejected].copy()          # keep the ORIGINAL text for debugging
    rejected_df["reject_reason"] = reasons.loc[is_rejected].str.rstrip("; ")

    clean_df = typed.loc[~is_rejected].copy()
    clean_df["quantity"] = clean_df["quantity"].astype(int)

    # 6) Fill remaining optional gaps with a clear default label.
    clean_df["customer_name"] = clean_df["customer_name"].fillna("Unknown")
    clean_df["city"] = clean_df["city"].fillna("Unknown")
    clean_df["product_name"] = clean_df["product_name"].fillna("Unknown Product")
    clean_df["category"] = clean_df["category"].fillna("Uncategorized")
    clean_df["payment_method"] = clean_df["payment_method"].fillna("Unknown")

    stats["rows_rejected"] = len(rejected_df)
    stats["rows_clean"] = len(clean_df)

    logger.info("Cleaning: %d exact duplicates removed, %d duplicate order_ids removed",
                stats["exact_duplicates_removed"], stats["duplicate_order_ids_removed"])
    logger.info("Cleaning: %d rows rejected as invalid, %d rows are clean",
                stats["rows_rejected"], stats["rows_clean"])
    if len(rejected_df):
        for reason, count in rejected_df["reject_reason"].value_counts().items():
            logger.info("    rejected (%d): %s", count, reason)

    return clean_df.reset_index(drop=True), rejected_df.reset_index(drop=True), stats


# ----------------------------------------------------------------------------
# TRANSFORMATION
# ----------------------------------------------------------------------------
def add_calculated_columns(df):
    """
    total_sales     = quantity x unit_price            (before discount)
    discount_amount = total_sales x discount% / 100
    revenue         = total_sales - discount_amount    (what the customer actually pays)
    """
    df = df.copy()
    df["total_sales"] = (df["quantity"] * df["unit_price"]).round(2)
    df["discount_amount"] = (df["total_sales"] * df["discount_percent"] / 100).round(2)
    df["revenue"] = (df["total_sales"] - df["discount_amount"]).round(2)
    df["order_month"] = df["order_date"].dt.strftime("%Y-%m")
    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")  # store dates as plain text
    return df


def build_summaries(df):
    """Create the summary tables. Returns a dictionary {name: DataFrame}."""
    product_summary = (
        df.groupby("product_id")
        .agg(product_name=("product_name", "first"),
             category=("category", "first"),
             units_sold=("quantity", "sum"),
             total_sales=("total_sales", "sum"),
             revenue=("revenue", "sum"))
        .round(2)
        .reset_index()
        .sort_values("revenue", ascending=False)
    )

    category_summary = (
        df.groupby("category")
        .agg(units_sold=("quantity", "sum"),
             total_sales=("total_sales", "sum"),
             revenue=("revenue", "sum"))
        .round(2)
        .reset_index()
        .sort_values("revenue", ascending=False)
    )

    monthly_sales = (
        df.groupby("order_month")
        .agg(orders=("order_id", "nunique"),
             units_sold=("quantity", "sum"),
             revenue=("revenue", "sum"))
        .round(2)
        .reset_index()
        .sort_values("order_month")
    )

    customer_summary = (
        df.groupby("customer_id")
        .agg(customer_name=("customer_name", "first"),
             city=("city", "first"),
             total_orders=("order_id", "nunique"),
             total_units=("quantity", "sum"),
             total_revenue=("revenue", "sum"),
             first_order_date=("order_date", "min"),
             last_order_date=("order_date", "max"))
        .reset_index()
    )
    customer_summary["avg_order_value"] = (
        customer_summary["total_revenue"] / customer_summary["total_orders"]
    )
    customer_summary = (
        customer_summary.round(2).sort_values("total_revenue", ascending=False)
    )

    return {
        "product_summary": product_summary,
        "category_summary": category_summary,
        "monthly_sales": monthly_sales,
        "customer_summary": customer_summary,
    }


def transform_data(clean_df):
    """Add calculated columns and build all summary tables."""
    sales_df = add_calculated_columns(clean_df)
    summaries = build_summaries(sales_df)
    logger.info("Transformation: calculated total_sales, discount_amount, revenue, order_month")
    logger.info("Transformation: built %d summary tables (%s)",
                len(summaries), ", ".join(summaries))
    return sales_df, summaries


def save_processed_data(sales_df, rejected_df, summaries, out_dir=PROCESSED_DIR):
    """Write every result to a CSV file in data/processed/."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sales_df.to_csv(out_dir / "cleaned_sales.csv", index=False)
    rejected_df.to_csv(out_dir / "rejected_records.csv", index=False)
    for name, table in summaries.items():
        table.to_csv(out_dir / f"{name}.csv", index=False)

    logger.info("Saved %d CSV files to %s", 2 + len(summaries), out_dir)
