"""
main.py  --  runs the COMPLETE ETL pipeline
-------------------------------------------
    python main.py                 # normal run
    python main.py --reset         # delete the database first and rebuild from scratch
    python main.py --raw-dir path  # read CSV files from another folder

Pipeline:  Extract (CSV) -> Clean -> Transform -> Load (SQLite) -> SQL analysis -> Report
"""

import argparse
import logging
import sys
import time

from src.analysis import run_analysis
from src.config import DB_PATH, RAW_DIR
from src.extract import extract_data, profile_data
from src.load import load_data
from src.transform import clean_data, save_processed_data, transform_data
from src.utils import setup_logging

logger = logging.getLogger("main")


def parse_args():
    parser = argparse.ArgumentParser(description="Sales data ETL pipeline")
    parser.add_argument("--raw-dir", default=str(RAW_DIR), help="folder containing raw CSV files")
    parser.add_argument("--db-path", default=str(DB_PATH), help="path of the SQLite database file")
    parser.add_argument("--reset", action="store_true",
                        help="delete the existing database before loading")
    return parser.parse_args()


def run_pipeline(raw_dir, db_path, reset=False):
    start = time.time()
    logger.info("=== ETL pipeline started ===")

    if reset and db_path.exists():
        db_path.unlink()
        logger.info("Existing database deleted (--reset)")

    # 1. EXTRACT
    logger.info("--- Step 1: Extract ---")
    raw_df = extract_data(raw_dir)
    profile_data(raw_df)

    # 2. CLEAN + TRANSFORM
    logger.info("--- Step 2: Clean ---")
    clean_df, rejected_df, stats = clean_data(raw_df)

    logger.info("--- Step 3: Transform ---")
    sales_df, summaries = transform_data(clean_df)
    save_processed_data(sales_df, rejected_df, summaries)

    # 3. LOAD
    logger.info("--- Step 4: Load ---")
    stats = load_data(sales_df, stats, db_path=db_path)

    # 4. ANALYSE + REPORT
    logger.info("--- Step 5: SQL analysis and report ---")
    run_analysis(stats, db_path=db_path)

    logger.info("=== ETL pipeline finished successfully in %.1f seconds ===", time.time() - start)


def main():
    from pathlib import Path

    args = parse_args()
    setup_logging()
    try:
        run_pipeline(Path(args.raw_dir), Path(args.db_path), reset=args.reset)
    except FileNotFoundError as error:
        logger.error("File problem: %s", error)
        sys.exit(1)
    except ValueError as error:
        logger.error("Data problem: %s", error)
        sys.exit(1)
    except Exception:
        logger.exception("Pipeline failed with an unexpected error")
        sys.exit(1)


if __name__ == "__main__":
    main()
