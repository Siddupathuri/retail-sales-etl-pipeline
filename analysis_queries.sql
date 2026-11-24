-- Reporting queries for the retail sales star schema.
-- They only join dimensions to the fact table, which is the point of the design:
-- reporting stays simple and fast, and dates are pre-parsed in dim_date.

-- 1. Monthly revenue trend
SELECT d.year,
       d.month,
       d.month_name,
       ROUND(SUM(f.line_total), 2) AS revenue,
       SUM(f.quantity)             AS units_sold,
       COUNT(DISTINCT f.order_id)  AS orders
FROM fact_sales f
JOIN dim_date d ON d.date_key = f.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;

-- 2. Top 10 products by revenue
SELECT p.product_name,
       p.category,
       ROUND(SUM(f.line_total), 2) AS revenue,
       SUM(f.quantity)             AS units_sold
FROM fact_sales f
JOIN dim_product p ON p.product_key = f.product_key
GROUP BY p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;

-- 3. Revenue by store and city
SELECT s.store_name,
       s.city,
       ROUND(SUM(f.line_total), 2) AS revenue,
       COUNT(DISTINCT f.order_id)  AS orders
FROM fact_sales f
JOIN dim_store s ON s.store_key = f.store_key
GROUP BY s.store_name, s.city
ORDER BY revenue DESC;

-- 4. Category mix as a share of total revenue (CTE + window function)
WITH category_revenue AS (
    SELECT p.category,
           SUM(f.line_total) AS revenue
    FROM fact_sales f
    JOIN dim_product p ON p.product_key = f.product_key
    GROUP BY p.category
)
SELECT category,
       ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS pct_of_total
FROM category_revenue
ORDER BY revenue DESC;

-- 5. Month-over-month growth (window function LAG)
WITH monthly AS (
    SELECT d.year,
           d.month,
           SUM(f.line_total) AS revenue
    FROM fact_sales f
    JOIN dim_date d ON d.date_key = f.date_key
    GROUP BY d.year, d.month
)
SELECT year,
       month,
       ROUND(revenue, 2) AS revenue,
       ROUND(revenue - LAG(revenue) OVER (ORDER BY year, month), 2) AS change_vs_prev_month
FROM monthly
ORDER BY year, month;

-- 6. Average order value per store
SELECT s.store_name,
       COUNT(DISTINCT f.order_id) AS orders,
       ROUND(SUM(f.line_total) / COUNT(DISTINCT f.order_id), 2) AS avg_order_value
FROM fact_sales f
JOIN dim_store s ON s.store_key = f.store_key
GROUP BY s.store_name
ORDER BY avg_order_value DESC;
