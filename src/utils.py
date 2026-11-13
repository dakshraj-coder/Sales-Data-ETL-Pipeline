"""
utils.py
--------
Small helper code shared by the whole project. Right now: logging setup.

Logging = writing messages about what the program is doing.
We send every message to TWO places: the terminal and logs/etl_pipeline.log.
"""

import logging

from src.config import LOGS_DIR


def setup_logging():
    """Configure logging once, at the start of the program."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    handlers = [
        logging.StreamHandler(),  # prints to the terminal
        logging.FileHandler(LOGS_DIR / "etl_pipeline.log", encoding="utf-8"),  # saves to a file
    ]
    # force=True makes sure we replace any logging setup that already exists.
    logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers, force=True)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)  # hide chatty library messages
