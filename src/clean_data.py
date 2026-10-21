
"""Clean fictional retail sales data and report auditable data-quality results."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "messy_sales.csv"
OUT = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

OUT.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)


def clean_sales(df: pd.DataFrame):
    """Return cleaned rows, rejected rows, and data-quality statistics."""

    initial_rows = len(df)
    df = df.copy()

    # Standardize column names.
    df.columns = df.columns.str.strip().str.lower()

    # Remove exact duplicates before modifying values.
    before_dedup = len(df)
    df = df.drop_duplicates().copy()
    exact_duplicates_removed = before_dedup - len(df)

    # Standardize text and convert common null markers to missing values.
    for col in df.columns:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace("", pd.NA)
        df[col] = df[col].replace(
            to_replace=r"(?i)^(NULL|N/A|UNKNOWN)$",
            value=pd.NA,
            regex=True,
        )

    # Normalize product categories.
    category_map = {
        "electronics": "Electronics",
        "grocery": "Groceries",
        "groceries": "Groceries",
        "household": "Household",
        "clothing": "Clothing",
        "furniture": "Furniture",
        "sports": "Sports",
        "stationery": "Stationery",
    }

    df["category"] = (
        df["category"].str.lower().map(category_map).fillna(df["category"])
    )

    # Normalize payment methods.
    payment_map = {
        "m-pesa": "M-Pesa",
        "mpesa": "M-Pesa",
        "cash": "Cash",
        "card": "Card",
        "bank transfer": "Bank Transfer",
    }

    df["payment_method"] = (
        df["payment_method"].str.lower().map(payment_map).fillna(
            df["payment_method"]
        )
    )

    # Normalize county names and correct a known spelling error.
    df["county"] = (
        df["county"].str.title().replace({"Nairobii": "Nairobi"})
    )

    # Parse mixed date formats explicitly. Valid ISO dates must not be
    # rejected because pandas inferred a different format from other rows.
    df["order_date"] = pd.to_datetime(
        df["order_date"],
        errors="coerce",
        format="mixed",
    )

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price_kes"] = pd.to_numeric(
        df["unit_price_kes"], errors="coerce"
    )
    df["discount_pct"] = pd.to_numeric(
        df["discount_pct"], errors="coerce"
    )

    # Validate dates, quantities, prices, discounts, and required fields.
    valid_date = (
        df["order_date"]
        .between(pd.Timestamp("2023-01-01"), pd.Timestamp("2025-12-31"))
        .fillna(False)
    )

    valid_quantity = (
        df["quantity"].gt(0) & df["quantity"].mod(1).eq(0)
    ).fillna(False)

    valid_price = (
        df["unit_price_kes"].gt(0)
        & df["unit_price_kes"].lt(1_000_000)
    ).fillna(False)

    valid_discount = (
        df["discount_pct"].between(0, 1)
    ).fillna(False)

    required = (
        df["order_id"].notna()
        & df["order_line_id"].notna()
        & df["product_id"].notna()
        & df["product_name"].notna()
    ).fillna(False)

    rule_failures = {
        "invalid_date": int((~valid_date).sum()),
        "invalid_quantity": int((~valid_quantity).sum()),
        "invalid_price": int((~valid_price).sum()),
        "invalid_discount": int((~valid_discount).sum()),
        "missing_required_field": int((~required).sum()),
    }

    valid = (
        valid_date
        & valid_quantity
        & valid_price
        & valid_discount
        & required
    ).fillna(False)

    rejected = df.loc[~valid].copy()

    # Preserve every applicable rejection reason for auditability.
    reason_masks = {
        "invalid_date": ~valid_date,
        "invalid_quantity": ~valid_quantity,
        "invalid_price": ~valid_price,
        "invalid_discount": ~valid_discount,
        "missing_required_field": ~required,
    }

    rejected["rejection_reason"] = ""

    for reason, mask in reason_masks.items():
        rejected.loc[mask.loc[rejected.index], "rejection_reason"] += (
            reason + ";"
        )

    clean = df.loc[valid].copy()

    clean["quantity"] = clean["quantity"].astype("int64")
    clean["unit_price_kes"] = clean["unit_price_kes"].round(2)

    # Customer IDs remain nullable; identities are never invented.
    # Invalid or missing discounts cannot enter the cleaned dataset.
    clean["discount_pct"] = clean["discount_pct"].fillna(0)

    # Fill non-critical descriptive fields with explicit labels.
    fill_values = {
        "customer_segment": "Unknown",
        "county": "Unknown",
        "town": "Unknown",
        "payment_method": "Unknown",
        "sales_channel": "Unknown",
        "sales_rep": "Unknown",
        "category": "Unclassified",
    }

    for col, value in fill_values.items():
        clean[col] = clean[col].fillna(value)

    # Calculate net sales after validation.
    clean["net_sales_kes"] = (
        clean["quantity"]
        * clean["unit_price_kes"]
        * (1 - clean["discount_pct"])
    ).round(2)

    clean["order_date"] = clean["order_date"].dt.strftime("%Y-%m-%d")

    stats = {
        "input_rows": initial_rows,
        "exact_duplicates_removed": exact_duplicates_removed,
        "rows_after_deduplication": len(df),
        "invalid_rows_rejected": len(rejected),
        "clean_rows": len(clean),
        "retention_rate_pct": (
            round(len(clean) / len(df) * 100, 2) if len(df) else 0
        ),
        "raw_missing_cells_after_deduplication": int(
            df.isna().sum().sum()
        ),
        "clean_missing_cells": int(clean.isna().sum().sum()),
        **rule_failures,
    }

    return clean, rejected, stats


if __name__ == "__main__":
    raw = pd.read_csv(RAW, dtype="string", low_memory=False)

    clean, rejected, stats = clean_sales(raw)

    clean_path = OUT / "clean_sales.csv"
    rejected_path = OUT / "rejected_records.csv"
    report_path = REPORTS / "data_quality_report.csv"

    clean.to_csv(clean_path, index=False)
    rejected.to_csv(rejected_path, index=False)

    pd.Series(stats, name="value").to_csv(report_path, header=True)

    print("=== DATA QUALITY SUMMARY ===")
    print(pd.Series(stats).to_string())

    print("\n=== OUTPUT FILES ===")
    print(f"Clean data:       {clean_path}")
    print(f"Rejected records: {rejected_path}")
    print(f"Quality report:   {report_path}")

    print("\nNote: rule-failure counts can overlap.")
    print("A single rejected row may fail multiple validation rules.")
