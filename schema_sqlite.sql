-- Retail sales star schema (SQLite, used when DATABASE_URL is not set)

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_date (
    date_key     INTEGER PRIMARY KEY,
    full_date    TEXT    NOT NULL,
    day_of_month INTEGER NOT NULL,
    month        INTEGER NOT NULL,
    month_name   TEXT    NOT NULL,
    quarter      INTEGER NOT NULL,
    year         INTEGER NOT NULL
);

CREATE TABLE dim_product (
    product_key  INTEGER PRIMARY KEY,
    product_id   TEXT    NOT NULL UNIQUE,
    product_name TEXT    NOT NULL,
    category     TEXT    NOT NULL
);

CREATE TABLE dim_store (
    store_key  INTEGER PRIMARY KEY,
    store_id   TEXT    NOT NULL UNIQUE,
    store_name TEXT    NOT NULL,
    city       TEXT    NOT NULL
);

CREATE TABLE fact_sales (
    order_id    TEXT    NOT NULL,
    product_key INTEGER NOT NULL REFERENCES dim_product (product_key),
    store_key   INTEGER NOT NULL REFERENCES dim_store (store_key),
    date_key    INTEGER NOT NULL REFERENCES dim_date (date_key),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    unit_price  REAL    NOT NULL CHECK (unit_price >= 0),
    discount    REAL    NOT NULL DEFAULT 0 CHECK (discount BETWEEN 0 AND 1),
    line_total  REAL    NOT NULL,
    PRIMARY KEY (order_id, product_key)
);

CREATE INDEX idx_fact_sales_date ON fact_sales (date_key);
CREATE INDEX idx_fact_sales_product ON fact_sales (product_key);
