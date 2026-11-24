"""Step 1 - extract: read the raw retail CSV exactly as it arrives."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

from etl.config import RAW_CSV

logger = logging.getLogger(__name__)


def extract_raw(path: Path = RAW_CSV) -> pd.DataFrame:
    """Read the raw file with every column as text.

    Reading everything as text keeps the raw values untouched; cleaning and
    type casting happen in the transform step so problems are visible instead
    of silently becoming NaN.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Raw file not found: {path}\n"
            "Run `python scripts/generate_sample_data.py` first."
        )

    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    # Drop an unnamed index column if a spreadsheet export added one.
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    logger.info("Extracted %s rows and %s columns from %s", f"{len(df):,}", len(df.columns), path.name)
    if df.empty:
        logger.warning("The raw file has no data rows")
        sys.exit(1)
    return df
