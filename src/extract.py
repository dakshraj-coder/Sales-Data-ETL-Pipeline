"""
extract.py  --  step 1 of ETL: EXTRACT
--------------------------------------
Reads every CSV file in data/raw/ and combines them into one pandas DataFrame.
A DataFrame is like an Excel sheet inside Python: rows and columns.
"""

import logging
from pathlib import Path

import pandas as pd

from src.config import RAW_DIR, REQUIRED_COLUMNS

logger = logging.getLogger(__name__)


def find_csv_files(raw_dir=RAW_DIR):
    """Return a sorted list of all .csv files in the folder. Stop with an error if none."""
    files = sorted(Path(raw_dir).glob("*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No CSV files found in {raw_dir}. "
            "Run 'python src/generate_sample_data.py' or add your own CSV files."
        )
    return files


def read_one_csv(path):
    """
    Read a single CSV file.
    - dtype=str : read EVERYTHING as text. We convert types ourselves in transform.py,
                  so pandas does not guess wrongly (e.g. turning '001' into 1).
    - encoding='utf-8-sig' : also handles files saved by Excel with a hidden BOM character.
    """
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")

    # Tidy the header names: "Order Date " -> "order_date"
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"{Path(path).name} is missing required columns: {missing}")

    df["source_file"] = Path(path).name  # remember where each row came from
    logger.info("Read %-22s -> %4d rows, %2d columns", Path(path).name, df.shape[0], df.shape[1])
    return df


def extract_data(raw_dir=RAW_DIR):
    """Read all CSV files and stack them into one DataFrame."""
    files = find_csv_files(raw_dir)
    logger.info("Found %d CSV file(s) in %s", len(files), raw_dir)

    frames = [read_one_csv(f) for f in files]
    combined = pd.concat(frames, ignore_index=True)

    logger.info("Combined dataset: %d rows, %d columns", combined.shape[0], combined.shape[1])
    return combined


def profile_data(df):
    """Log how many values are missing in each column (a first look at data quality)."""
    logger.info("Missing values per column (before cleaning):")
    for col, count in df.isna().sum().items():
        if count > 0:
            logger.info("    %-18s %4d missing", col, count)
