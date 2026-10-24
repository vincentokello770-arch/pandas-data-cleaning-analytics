"""Load cleaned retail sales into a SQLite analytics database."""

from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CSV_FILE = ROOT / "data" / "processed" / "clean_sales.csv"
DB_DIR = ROOT / "data" / "analytics"
DB_FILE = DB_DIR / "sales_analytics.db"

def main():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {CSV_FILE}")

    DB_DIR.mkdir(parents=True, exist_ok=True)

    if DB_FILE.exists():
        raise FileExistsError(
            f"Database already exists: {DB_FILE}\n"
            "It was not overwritten. Rename or remove it deliberately "
            "if you want to rebuild it."
        )

    total_rows = 0

    with sqlite3.connect(DB_FILE) as connection:
        for chunk in pd.read_csv(CSV_FILE, chunksize=10000):
            chunk.to_sql(
                "sales",
                connection,
                if_exists="append",
                index=False,
            )
            total_rows += len(chunk)

        connection.execute(
            "CREATE INDEX idx_sales_date ON sales(order_date)"
        )
        connection.execute(
            "CREATE INDEX idx_sales_category ON sales(category)"
        )
        connection.execute(
            "CREATE INDEX idx_sales_county ON sales(county)"
        )

        result = connection.execute(
            "SELECT COUNT(*), ROUND(SUM(net_sales_kes), 2) FROM sales"
        ).fetchone()

    print("Database created successfully.")
    print(f"Database: {DB_FILE}")
    print(f"Imported rows: {total_rows:,}")
    print(f"Verified rows: {result[0]:,}")
    print(f"Total net sales (KES): {result[1]:,.2f}")

if __name__ == "__main__":
    main()
