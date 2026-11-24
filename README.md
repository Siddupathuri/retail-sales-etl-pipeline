# Retail Sales ETL Pipeline & Data Warehouse

An automated ETL pipeline that takes a messy retail sales export, cleans and validates it with Python + Pandas, and loads an analysis-ready **star schema** into PostgreSQL.

```
Raw CSV  ──▶  Extract  ──▶  Transform (Pandas)  ──▶  Validate  ──▶  Load  ──▶  SQL reporting
              pandas        clean types, dates,      reject bad      star schema
                            currency, duplicates     rows + log      (fact + dims)
```

## What the pipeline does

1. **Extract** – reads `data/raw/retail_sales_raw.csv` with every column as text, so nothing is silently changed.
2. **Transform** – standardises column names and text values, parses three different date formats, converts values like `"$1,299.00"` to numbers, normalises discounts (`"10%"` → `0.10`) and calculates `line_total`.
3. **Validate** – flags missing keys, invalid dates, non-positive quantities and out-of-range prices/discounts. Bad rows are written to `logs/rejected_records.csv` with a reason, and every run produces `logs/validation_report.txt`.
4. **Load** – creates the star schema and loads dimensions first, then the fact table.

## Star schema

```mermaid
erDiagram
    dim_date ||--o{ fact_sales : date_key
    dim_product ||--o{ fact_sales : product_key
    dim_store ||--o{ fact_sales : store_key

    dim_date {
        int date_key PK
        text full_date
        int month
        text month_name
        int quarter
        int year
    }
    dim_product {
        int product_key PK
        text product_id
        text product_name
        text category
    }
    dim_store {
        int store_key PK
        text store_id
        text store_name
        text city
    }
    fact_sales {
        text order_id PK
        int product_key FK
        int store_key FK
        int date_key FK
        int quantity
        numeric unit_price
        numeric discount
        numeric line_total
    }
```

Dimensions use **surrogate integer keys** (`product_key`, `store_key`, `date_key`) so the fact table holds compact foreign keys, and reporting never has to parse dates or match product names.

## Quick start

```bash
# 1. create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. generate a sample raw export (already included in data/raw)
python scripts/generate_sample_data.py

# 4. run the pipeline
python run_pipeline.py

# 5. run the reporting queries
python scripts/run_analysis.py
```

By default the warehouse is written to `data/warehouse.db` (SQLite) so you can try everything with **zero database setup**.

### Loading into PostgreSQL

```bash
createdb retail_dw
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/retail_dw"
python run_pipeline.py
```

The correct DDL (`sql/schema_postgres.sql`) is chosen automatically; SQLite users get `sql/schema_sqlite.sql`. See `.env.example` for the variable name.

## Repository layout

```
retail-sales-etl-pipeline/
├── run_pipeline.py              # orchestrates extract → transform → validate → load
├── db.py                        # engine + schema helpers (PostgreSQL or SQLite)
├── etl/
│   ├── extract.py
│   ├── transform.py             # cleaning + star schema builder
│   ├── validate.py              # quality rules, rejects, audit report
│   └── load.py
├── scripts/
│   ├── generate_sample_data.py  # creates the messy raw CSV
│   └── run_analysis.py          # runs every query in sql/analysis_queries.sql
├── sql/
│   ├── schema_postgres.sql
│   ├── schema_sqlite.sql
│   └── analysis_queries.sql     # joins, CTEs, window functions
└── data/raw/retail_sales_raw.csv
```

## Reporting queries included

- Monthly revenue trend
- Top 10 products by revenue
- Revenue by store and city
- Category mix as a % of total revenue (CTE + window function)
- Month-over-month revenue growth (`LAG`)
- Average order value per store

## Data quality checks

| Check | Action |
| --- | --- |
| Missing order / product / store / date | row rejected |
| Unparseable order date | row rejected |
| Quantity ≤ 0 or not a number | row rejected |
| Negative or missing unit price | row rejected |
| Discount outside 0–1 | row rejected |
| Duplicate `(order_id, product_id)` | duplicate dropped, counted in report |

## Notes

- The sample data is generated with a fixed random seed, so runs are reproducible.
- Logs are written to `logs/pipeline.log`; processed tables are also saved as CSV in `data/processed/`.
