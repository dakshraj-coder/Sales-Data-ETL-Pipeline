-- analysis_queries.sql
-- Each query starts with a special comment line (name: followed by a query name).
-- analysis.py reads this file,
-- splits it at those lines and runs every query. You can also paste any single
-- query into a SQLite viewer (e.g. DB Browser for SQLite).

-- name: total_revenue
-- Q: What is the total revenue?
SELECT
    ROUND(SUM(revenue), 2) AS total_revenue,
    COUNT(*)               AS total_orders
FROM sales;

-- name: top_10_products
-- Q: What are the top 10 selling products? (ranked by units sold)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(s.quantity)           AS units_sold,
    ROUND(SUM(s.revenue), 2)  AS revenue
FROM sales AS s
JOIN products AS p ON p.product_id = s.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY units_sold DESC, revenue DESC
LIMIT 10;

-- name: revenue_by_category
-- Q: Which product category generates the highest revenue? (first row = highest)
SELECT
    p.category,
    SUM(s.quantity)           AS units_sold,
    ROUND(SUM(s.revenue), 2)  AS revenue
FROM sales AS s
JOIN products AS p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue DESC;

-- name: monthly_sales
-- Q: What are the monthly sales trends?
SELECT
    order_month,
    COUNT(*)                 AS orders,
    SUM(quantity)            AS units_sold,
    ROUND(SUM(revenue), 2)   AS revenue
FROM sales
GROUP BY order_month
ORDER BY order_month;

-- name: top_10_customers
-- Q: Who are the top customers? (ranked by revenue)
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    COUNT(*)                 AS orders,
    ROUND(SUM(s.revenue), 2) AS total_revenue
FROM sales AS s
JOIN customers AS c ON c.customer_id = s.customer_id
GROUP BY c.customer_id, c.customer_name, c.city
ORDER BY total_revenue DESC
LIMIT 10;

-- name: average_order_value
-- Q: What is the average order value? (total revenue / number of orders)
SELECT
    ROUND(SUM(revenue) * 1.0 / COUNT(DISTINCT order_id), 2) AS average_order_value
FROM sales;
