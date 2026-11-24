"""Run the whole retail sales ETL pipeline.

    python run_pipeline.py                 # extract, clean, validate, load
    python run_pipeline.py --generate-sample
    python run_pipeline.py --skip-load     # stop after validation
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from etl.config import LOG_DIR, PROCESSED_DIR, RAW_CSV
from etl.extract import extract_raw
from etl.load import load_tables, write_processed_outputs
from etl.transform import build_star_schema, clean
from etl.validate import validate

ROOT = Path(__file__).resolve().parent


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Retail sales ETL pipeline")
    parser.add_argument(
        "--generate-sample",
        action="store_true",
        help="create a fresh sample raw CSV before running",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="run extraction, cleaning and validation but do not touch the database",
    )
    parser.add_argument("--database-url", help="override DATABASE_URL for this run")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger("pipeline")
    logger.info("Starting retail sales ETL pipeline")

    if args.generate_sample or not RAW_CSV.exists():
        from scripts.generate_sample_data import main as generate_sample

        logger.info("Generating sample raw data")
        generate_sample()

    raw = extract_raw(RAW_CSV)
    cleaned = clean(raw)
    valid, _rejected, report = validate(cleaned)
    tables = build_star_schema(valid)

    write_processed_outputs(tables, PROCESSED_DIR)

    if args.skip_load:
        logger.info("Skipping database load (--skip-load). Validation report: %s", report)
    else:
        from db import get_engine

        engine = get_engine(args.database_url)
        load_tables(tables, engine)
        logger.info("Loaded warehouse into %s", engine.url.render_as_string(hide_password=True))
        logger.info("Next: python scripts/run_analysis.py")

    logger.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()
