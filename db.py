"""Database helpers.

By default the pipeline writes to a local SQLite file (zero setup, great for
trying the project). Set DATABASE_URL to load into PostgreSQL instead, e.g.

    DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/retail_dw
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parent
SQL_DIR = ROOT / "sql"


def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or os.getenv("DATABASE_URL", "").strip()
    if url:
        return create_engine(url, future=True)
    db_path = ROOT / "data" / "warehouse.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", future=True)


def schema_file_for(engine: Engine) -> Path:
    if engine.dialect.name == "postgresql":
        return SQL_DIR / "schema_postgres.sql"
    return SQL_DIR / "schema_sqlite.sql"


def run_sql_script(engine: Engine, script: str) -> None:
    """Execute a .sql file statement by statement (works on both backends)."""
    statements = [part.strip() for part in script.split(";") if part.strip()]
    with engine.begin() as connection:
        for statement in statements:
            # Skip pure comment blocks left between statements.
            if all(line.strip().startswith("--") or not line.strip() for line in statement.splitlines()):
                continue
            connection.execute(text(statement))


def reset_schema(engine: Engine) -> None:
    run_sql_script(engine, schema_file_for(engine).read_text(encoding="utf-8"))
