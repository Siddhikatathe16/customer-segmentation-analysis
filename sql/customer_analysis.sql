-- =====================================================
-- CUSTOMER SEGMENTATION & MARKETING ANALYTICS
-- SQL ANALYSIS
-- =====================================================


-- 1. Total Revenue
SELECT
    ROUND(SUM(Quantity * UnitPrice), 2) AS total_revenue
FROM retail;


-- 2. Total Customers
SELECT
    COUNT(DISTINCT CustomerID) AS total_customers
FROM retail
WHERE CustomerID IS NOT NULL;


-- 3. Total Orders
SELECT
    COUNT(DISTINCT InvoiceNo) AS total_orders
FROM retail;


-- 4. Average Order Value
SELECT
    ROUND(
        SUM(Quantity * UnitPrice)
        / COUNT(DISTINCT InvoiceNo),
        2
    ) AS average_order_value
FROM retail;


-- 5. Revenue by Country
SELECT
    Country,
    ROUND(SUM(Quantity * UnitPrice), 2) AS revenue
FROM retail
GROUP BY Country
ORDER BY revenue DESC;


-- 6. Top 10 Products by Revenue
SELECT
    Description,
    ROUND(SUM(Quantity * UnitPrice), 2) AS revenue
FROM retail
WHERE Description IS NOT NULL
GROUP BY Description
ORDER BY revenue DESC
LIMIT 10;


-- 7. Top 10 Customers by Spending
SELECT
    CustomerID,
    ROUND(SUM(Quantity * UnitPrice), 2) AS total_spending
FROM retail
WHERE CustomerID IS NOT NULL
GROUP BY CustomerID
ORDER BY total_spending DESC
LIMIT 10;


-- 8. Orders per Customer
SELECT
    CustomerID,
    COUNT(DISTINCT InvoiceNo) AS total_orders
FROM retail
WHERE CustomerID IS NOT NULL
GROUP BY CustomerID
ORDER BY total_orders DESC
LIMIT 10;


-- 9. Monthly Revenue
SELECT
    strftime('%Y-%m', InvoiceDate) AS month,
    ROUND(SUM(Quantity * UnitPrice), 2) AS revenue
FROM retail
GROUP BY month
ORDER BY month;


-- 10. Monthly Orders
SELECT
    strftime('%Y-%m', InvoiceDate) AS month,
    COUNT(DISTINCT InvoiceNo) AS orders
FROM retail
GROUP BY month
ORDER BY month;


-- 11. Average Spending per Customer
SELECT
    ROUND(
        SUM(Quantity * UnitPrice)
        / COUNT(DISTINCT CustomerID),
        2
    ) AS average_customer_spending
FROM retail
WHERE CustomerID IS NOT NULL;


-- 12. Customers with More Than 5 Orders
SELECT
    CustomerID,
    COUNT(DISTINCT InvoiceNo) AS order_count
FROM retail
WHERE CustomerID IS NOT NULL
GROUP BY CustomerID
HAVING order_count > 5
ORDER BY order_count DESC;


-- 13. High-Value Customers
SELECT
    CustomerID,
    ROUND(SUM(Quantity * UnitPrice), 2) AS total_spending
FROM retail
WHERE CustomerID IS NOT NULL
GROUP BY CustomerID
HAVING total_spending > 5000
ORDER BY total_spending DESC;


-- 14. Country-wise Customers
SELECT
    Country,
    COUNT(DISTINCT CustomerID) AS customers
FROM retail
WHERE CustomerID IS NOT NULL
GROUP BY Country
ORDER BY customers DESC;


-- 15. Cancelled Transactions
SELECT
    COUNT(*) AS cancelled_transactions
FROM retail
WHERE InvoiceNo LIKE 'C%';