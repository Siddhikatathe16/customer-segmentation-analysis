import sqlite3
import pandas as pd
from pathlib import Path


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

excel_file = BASE_DIR / "data" / "raw" / "Online Retail.xlsx"

database_dir = BASE_DIR / "database"

database_dir.mkdir(exist_ok=True)

database_file = database_dir / "customer_segmentation.db"


# Load Excel
print("Loading dataset...")

df = pd.read_excel(excel_file)


# Basic cleaning
df = df.dropna(subset=["CustomerID"])

df = df[df["Quantity"] > 0]

df = df[df["UnitPrice"] > 0]


# Convert date
df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"]
)


# Create SQLite connection
conn = sqlite3.connect(database_file)


# Save dataframe to SQL table
df.to_sql(
    "retail",
    conn,
    if_exists="replace",
    index=False
)


conn.close()


print("Database created successfully!")

print(f"Location: {database_file}")
print(f"Rows: {len(df):,}")