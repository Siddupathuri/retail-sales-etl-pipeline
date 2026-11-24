"""Shared paths and settings for the retail ETL pipeline."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "retail_sales_raw.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
LOG_DIR = ROOT / "logs"
SQL_DIR = ROOT / "sql"

# The order the warehouse tables are created and loaded in.
TABLES = ["dim_date", "dim_product", "dim_store", "fact_sales"]

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%b %d, %Y", "%d %b %Y")
