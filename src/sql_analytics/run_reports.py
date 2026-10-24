"""Execute SQL business reports against the retail database."""

from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[2]
DB_FILE = ROOT / "data" / "analytics" / "sales_analytics.db"
SQL_FILE = ROOT / "sql" / "business_reports.sql"

def main():
    sql_text = SQL_FILE.read_text(encoding="utf-8-sig")
    queries = [q.strip() for q in sql_text.split(";") if q.strip()]

    with sqlite3.connect(DB_FILE) as connection:
        for number, query in enumerate(queries, start=1):
            cursor = connection.execute(query)
            columns = [item[0] for item in cursor.description]
            rows = cursor.fetchall()

            print(f"\n{'=' * 60}")
            print(f"BUSINESS REPORT {number}")
            print("=" * 60)
            print(" | ".join(columns))

            for row in rows:
                print(" | ".join(str(value) for value in row))

if __name__ == "__main__":
    main()
