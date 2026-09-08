import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
db_file = BASE_DIR / "database" / "customer_segmentation.db"

conn = sqlite3.connect(db_file)

print("\n========== SQL ANALYSIS ==========\n")

# 1. Total Revenue
query = """
SELECT ROUND(SUM(Quantity * UnitPrice), 2) AS total_revenue
FROM retail;
"""

result = pd.read_sql_query(query, conn)
print("1. Total Revenue:")
print(result)


# 2. Total Customers
query = """
SELECT COUNT(DISTINCT CustomerID) AS total_customers
FROM retail;
"""

result = pd.read_sql_query(query, conn)
print("\n2. Total Customers:")
print(result)


# 3. Total Orders
query = """
SELECT COUNT(DISTINCT InvoiceNo) AS total_orders
FROM retail;
"""

result = pd.read_sql_query(query, conn)
print("\n3. Total Orders:")
print(result)


# 4. Average Order Value
query = """
SELECT ROUND(
    SUM(Quantity * UnitPrice) /
    COUNT(DISTINCT InvoiceNo), 2
) AS average_order_value
FROM retail;
"""

result = pd.read_sql_query(query, conn)
print("\n4. Average Order Value:")
print(result)


# 5. Revenue by Country
query = """
SELECT
    Country,
    ROUND(SUM(Quantity * UnitPrice), 2) AS revenue
FROM retail
GROUP BY Country
ORDER BY revenue DESC
LIMIT 10;
"""

result = pd.read_sql_query(query, conn)
print("\n5. Top 10 Countries by Revenue:")
print(result)


# 6. Top 10 Customers
query = """
SELECT
    CustomerID,
    ROUND(SUM(Quantity * UnitPrice), 2) AS total_spending
FROM retail
GROUP BY CustomerID
ORDER BY total_spending DESC
LIMIT 10;
"""

result = pd.read_sql_query(query, conn)
print("\n6. Top 10 Customers:")
print(result)


# 7. Monthly Revenue
query = """
SELECT
    strftime('%Y-%m', InvoiceDate) AS month,
    ROUND(SUM(Quantity * UnitPrice), 2) AS revenue
FROM retail
GROUP BY month
ORDER BY month;
"""

result = pd.read_sql_query(query, conn)
print("\n7. Monthly Revenue:")
print(result)


# 8. Top Products
query = """
SELECT
    Description,
    ROUND(SUM(Quantity * UnitPrice), 2) AS revenue
FROM retail
WHERE Description IS NOT NULL
GROUP BY Description
ORDER BY revenue DESC
LIMIT 10;
"""

result = pd.read_sql_query(query, conn)
print("\n8. Top 10 Products:")
print(result)


conn.close()

print("\n========== SQL ANALYSIS COMPLETED ==========")