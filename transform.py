"""Step 2 - transform: clean the raw text and build star-schema tables."""

from __future__ import annotations

import logging
import re

import pandas as pd

from etl.config import DATE_FORMATS

logger = logging.getLogger(__name__)


def parse_date(value: str):
    """Parse a date written in any of the formats the source system sends."""
    if value is None:
        return pd.NaT
    text = str(value).strip()
    if not text:
        return pd.NaT
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(text, format=fmt)
        except (ValueError, TypeError):
            continue
    # Last resort: let pandas guess (handles things like "5 Jan 2024").
    parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
    return parsed if not pd.isna(parsed) else pd.NaT


def parse_money(value) -> float:
    """Turn '$1,299.00', ' 1299 ' or '(12.50)' into a float."""
    if value is None:
        return float("nan")
    text = str(value).strip()
    if not text:
        return float("nan")
    negative = text.startswith("(") and text.endswith(")")
    cleaned = re.sub(r"[^0-9.\-]", "", text)
    if cleaned in {"", "-", ".", "-."}:
        return float("nan")
    try:
        number = float(cleaned)
    except ValueError:
        return float("nan")
    if negative:
        number = -abs(number)
    return number


def parse_discount(value) -> float:
    """'10%' -> 0.10, '0.1' -> 0.10, '' -> 0.0."""
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    if text.endswith("%"):
        number = parse_money(text[:-1])
        return 0.0 if pd.isna(number) else number / 100
    number = parse_money(text)
    return 0.0 if pd.isna(number) else number


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column names, text values and data types."""
    cleaned = df.copy()
    cleaned.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower()).strip("_")
        for col in cleaned.columns
    ]
    for column in cleaned.columns:
        if cleaned[column].dtype == object:
            cleaned[column] = cleaned[column].astype(str).str.strip()
            cleaned[column] = cleaned[column].replace({"": None, "nan": None, "NaN": None})

    expected = [
        "order_id",
        "order_date",
        "product_id",
        "product_name",
        "category",
        "store_id",
        "store_name",
        "city",
        "quantity",
        "unit_price",
        "discount",
    ]
    missing = [col for col in expected if col not in cleaned.columns]
    if missing:
        raise ValueError(
            f"Raw file is missing required columns: {missing}. Found: {list(cleaned.columns)}"
        )

    cleaned = cleaned[expected]
    cleaned["order_id"] = cleaned["order_id"].str.upper()
    cleaned["product_id"] = cleaned["product_id"].str.upper()
    cleaned["store_id"] = cleaned["store_id"].str.upper()
    cleaned["order_date"] = cleaned["order_date"].map(parse_date)
    cleaned["quantity"] = pd.to_numeric(cleaned["quantity"], errors="coerce")
    cleaned["unit_price"] = cleaned["unit_price"].map(parse_money)
    cleaned["discount"] = cleaned["discount"].map(parse_discount)

    # Title-case text fields so "WIRELESS MOUSE" and "Wireless Mouse" match.
    for column in ["product_name", "category", "store_name", "city"]:
        cleaned[column] = cleaned[column].str.title()

    cleaned["line_total"] = (
        cleaned["quantity"] * cleaned["unit_price"] * (1 - cleaned["discount"])
    ).round(2)
    logger.info("Cleaned %s rows", f"{len(cleaned):,}")
    return cleaned


def build_star_schema(valid: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Split clean rows into dimension tables and one fact table."""
    work = valid.copy().reset_index(drop=True)
    dates = work["order_date"].dt.normalize()
    work["date_key"] = dates.dt.strftime("%Y%m%d").astype("int64")

    dim_date = pd.DataFrame(
        {
            "date_key": work["date_key"],
            "full_date": dates.dt.strftime("%Y-%m-%d"),
            "day_of_month": dates.dt.day.astype("int64"),
            "month": dates.dt.month.astype("int64"),
            "month_name": dates.dt.strftime("%B"),
            "quarter": dates.dt.quarter.astype("int64"),
            "year": dates.dt.year.astype("int64"),
        }
    ).drop_duplicates(subset=["date_key"]).sort_values("date_key")

    dim_product = (
        work[["product_id", "product_name", "category"]]
        .drop_duplicates(subset=["product_id"])
        .sort_values("product_id")
        .reset_index(drop=True)
    )
    dim_product.insert(0, "product_key", range(1, len(dim_product) + 1))

    dim_store = (
        work[["store_id", "store_name", "city"]]
        .drop_duplicates(subset=["store_id"])
        .sort_values("store_id")
        .reset_index(drop=True)
    )
    dim_store.insert(0, "store_key", range(1, len(dim_store) + 1))

    fact = work.merge(dim_product[["product_key", "product_id"]], on="product_id", how="left")
    fact = fact.merge(dim_store[["store_key", "store_id"]], on="store_id", how="left")

    fact_sales = fact[
        ["order_id", "product_key", "store_key", "date_key", "quantity", "unit_price", "discount", "line_total"]
    ].copy()
    fact_sales["quantity"] = fact_sales["quantity"].astype("int64")

    tables = {
        "dim_date": dim_date,
        "dim_product": dim_product,
        "dim_store": dim_store,
        "fact_sales": fact_sales,
    }
    for name, table in tables.items():
        logger.info("Built %s with %s rows", name, f"{len(table):,}")
    return tables
