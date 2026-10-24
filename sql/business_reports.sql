-- 1. Top 10 product categories by net sales
SELECT category,
       ROUND(SUM(net_sales_kes), 2) AS revenue_kes
FROM sales
GROUP BY category
ORDER BY revenue_kes DESC
LIMIT 10;

-- 2. Top 10 counties by net sales
SELECT county,
       ROUND(SUM(net_sales_kes), 2) AS revenue_kes
FROM sales
GROUP BY county
ORDER BY revenue_kes DESC
LIMIT 10;

-- 3. Revenue by sales channel
SELECT sales_channel,
       COUNT(*) AS sales_lines,
       ROUND(SUM(net_sales_kes), 2) AS revenue_kes
FROM sales
GROUP BY sales_channel
ORDER BY revenue_kes DESC;

-- 4. Monthly revenue trend
SELECT SUBSTR(order_date, 1, 7) AS sales_month,
       ROUND(SUM(net_sales_kes), 2) AS revenue_kes
FROM sales
GROUP BY sales_month
ORDER BY sales_month;

-- 5. Payment method performance
SELECT payment_method,
       COUNT(*) AS sales_lines,
       ROUND(SUM(net_sales_kes), 2) AS revenue_kes
FROM sales
GROUP BY payment_method
ORDER BY revenue_kes DESC;
