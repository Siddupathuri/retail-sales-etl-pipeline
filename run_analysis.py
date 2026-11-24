"""Run every query in sql/analysis_queries.sql and print the results."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db import get_engine  # noqa: E402

QUERY_FILE = ROOT / "sql" / "analysis_queries.sql"


def split_queries(sql_text: str) -> list[str]:
    return [part.strip() for part in sql_text.split(";") if part.strip()]


def main() -> None:
    engine = get_engine()
    queries = split_queries(QUERY_FILE.read_text(encoding="utf-8"))
    with engine.connect() as connection:
        for index, query in enumerate(queries, start=1):
            # Each query starts with a "-- n. Title" comment line.
            match = re.search(r"^--\s*\d+\.\s*(.+)$", query, re.MULTILINE)
            title = match.group(1).strip() if match else f"Query {index}"
            result = pd.read_sql(query, connection)
            print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
            print(result.to_string(index=False))


if __name__ == "__main__":
    main()
