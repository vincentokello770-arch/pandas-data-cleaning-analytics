"""Tests for the retail SQL analytics database."""

from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "data" / "processed" / "clean_sales.csv"
DB_FILE = ROOT / "data" / "analytics" / "sales_analytics.db"


def test_database_row_count_matches_csv():
    source = pd.read_csv(CSV_FILE)
    with sqlite3.connect(DB_FILE) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM sales"
        ).fetchone()[0]

    assert count == len(source)


def test_database_revenue_matches_csv():
    source = pd.read_csv(CSV_FILE)
    expected = round(source["net_sales_kes"].sum(), 2)

    with sqlite3.connect(DB_FILE) as connection:
        actual = connection.execute(
            "SELECT ROUND(SUM(net_sales_kes), 2) FROM sales"
        ).fetchone()[0]

    assert actual == expected


def test_no_missing_order_ids():
    with sqlite3.connect(DB_FILE) as connection:
        missing = connection.execute(
            "SELECT COUNT(*) FROM sales "
            "WHERE order_id IS NULL OR TRIM(order_id) = ''"
        ).fetchone()[0]

    assert missing == 0


def test_category_revenue_reconciles():
    with sqlite3.connect(DB_FILE) as connection:
        total = connection.execute(
            "SELECT ROUND(SUM(net_sales_kes), 2) FROM sales"
        ).fetchone()[0]

        category_total = connection.execute(
            """
            SELECT ROUND(SUM(category_revenue), 2)
            FROM (
                SELECT SUM(net_sales_kes) AS category_revenue
                FROM sales
                GROUP BY category
            )
            """
        ).fetchone()[0]

    assert category_total == total
