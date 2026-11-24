"""Step 4 - load: create the warehouse tables and load the star schema."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy.engine import Engine

from db import reset_schema
from etl.config import TABLES

logger = logging.getLogger(__name__)


def load_tables(tables: dict[str, pd.DataFrame], engine: Engine) -> None:
    """Recreate the schema, then insert dimensions before the fact table."""
    reset_schema(engine)

    with engine.begin() as connection:
        for name in TABLES:
            frame = tables[name].copy()
            # Keep dates as ISO text so the same queries work on SQLite and PostgreSQL.
            for column in frame.columns:
                if pd.api.types.is_datetime64_any_dtype(frame[column]):
                    frame[column] = frame[column].dt.strftime("%Y-%m-%d")
            frame.to_sql(name, connection, if_exists="append", index=False)
            logger.info("Loaded %s rows into %s", f"{len(frame):,}", name)


def write_processed_outputs(tables: dict[str, pd.DataFrame], output_dir: Path) -> None:
    """Also save each warehouse table as CSV, handy for review without a DB."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)
    logger.info("Saved warehouse tables as CSV files in %s", output_dir)
