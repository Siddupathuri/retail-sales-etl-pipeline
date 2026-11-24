-- Retail sales star schema (PostgreSQL)
-- fact_sales sits in the middle, surrounded by dim_date, dim_product, dim_store.

DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_store CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

CREATE TABLE dim_date (
    date_key      INTEGER PRIMARY KEY,
    full_date     VARCHAR(10) NOT NULL,
    day_of_month  SMALLINT    NOT NULL,
    month         SMALLINT    NOT NULL,
    month_name    VARCHAR(12) NOT NULL,
    quarter       SMALLINT    NOT NULL,
    year          SMALLINT    NOT NULL
);

CREATE TABLE dim_product (
    product_key  INTEGER PRIMARY KEY,
    product_id   VARCHAR(20)  NOT NULL UNIQUE,
    product_name VARCHAR(120) NOT NULL,
    category     VARCHAR(60)  NOT NULL
);

CREATE TABLE dim_store (
    store_key  INTEGER PRIMARY KEY,
    store_id   VARCHAR(20)  NOT NULL UNIQUE,
    store_name VARCHAR(120) NOT NULL,
    city       VARCHAR(80)  NOT NULL
);

CREATE TABLE fact_sales (
    order_id   VARCHAR(20)   NOT NULL,
    product_key INTEGER      NOT NULL REFERENCES dim_product (product_key),
    store_key   INTEGER      NOT NULL REFERENCES dim_store (store_key),
    date_key    INTEGER      NOT NULL REFERENCES dim_date (date_key),
    quantity    INTEGER      NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    discount    NUMERIC(4, 2)  NOT NULL DEFAULT 0 CHECK (discount BETWEEN 0 AND 1),
    line_total  NUMERIC(12, 2) NOT NULL,
    PRIMARY KEY (order_id, product_key)
);

CREATE INDEX idx_fact_sales_date ON fact_sales (date_key);
CREATE INDEX idx_fact_sales_product ON fact_sales (product_key);
