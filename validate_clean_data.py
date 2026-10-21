
"""Validate cleaned sales data and report its quality and integrity."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "processed" / "clean_sales.csv"
REJECTED_FILE = ROOT / "data" / "processed" / "rejected_records.csv"
RAW_FILE = ROOT / "data" / "raw" / "messy_sales.csv"
REPORT_FILE = ROOT / "reports" / "data_quality_report.csv"

passed = 0
failed = 0


def check(condition, description):
    """Print a PASS or FAIL result for a validation check."""
    global passed, failed

    if bool(condition):
        print(f"PASS: {description}")
        passed += 1
    else:
        print(f"FAIL: {description}")
        failed += 1


def main():
    global passed, failed

    print("=" * 70)
    print("PANDAS DATA CLEANING PROJECT - VALIDATION")
    print("=" * 70)

    # Confirm required input and output files exist.
    missing_files = [
        path for path in (DATA_FILE, REJECTED_FILE, RAW_FILE, REPORT_FILE)
        if not path.exists()
    ]

    check(not missing_files, "Raw, clean, rejected and quality-report files exist")

    if missing_files:
        for path in missing_files:
            print(f"Missing file: {path}")
        print("Run the data generator and cleaner before validation.")
        return

    df = pd.read_csv(DATA_FILE, low_memory=False)
    rejected = pd.read_csv(REJECTED_FILE, low_memory=False)
    raw = pd.read_csv(RAW_FILE, dtype="string", low_memory=False)
    quality = pd.read_csv(REPORT_FILE, index_col=0)

    print(f"\nClean dataset: {DATA_FILE.relative_to(ROOT)}")
    print(f"Clean rows: {len(df):,}")
    print(f"Rejected rows: {len(rejected):,}")
    print(f"Raw rows: {len(raw):,}")

    # 1. Required columns.
    required_columns = [
        "order_id",
        "order_line_id",
        "order_date",
        "customer_id",
        "product_id",
        "product_name",
        "category",
        "quantity",
        "unit_price_kes",
        "discount_pct",
        "payment_method",
        "county",
        "net_sales_kes",
    ]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    check(not missing_columns, "All required columns exist")

    if missing_columns:
        print("Missing columns:", missing_columns)
        print("Cannot safely run the remaining checks.")
        return

    # 2. Reconcile the raw, deduplicated, clean and rejected row counts.
    duplicate_count = int(raw.duplicated().sum())
    deduplicated_rows = len(raw) - duplicate_count

    check(
        len(df) + len(rejected) == deduplicated_rows,
        "Clean and rejected rows reconcile to the deduplicated raw dataset",
    )

    check(
        duplicate_count == 60,
        "Raw dataset contains the 60 deliberately injected exact duplicates",
    )

    check(
        int(quality.loc["exact_duplicates_removed", "value"])
        == duplicate_count,
        "Quality report records the correct number of removed duplicates",
    )

    check(
        int(quality.loc["rows_after_deduplication", "value"])
        == deduplicated_rows,
        "Quality report records the correct post-deduplication row count",
    )

    check(
        int(quality.loc["clean_rows", "value"]) == len(df),
        "Quality report clean-row count matches the clean dataset",
    )

    check(
        int(quality.loc["invalid_rows_rejected", "value"]) == len(rejected),
        "Quality report rejected-row count matches the rejected dataset",
    )

    # 3. Exact duplicates and unique order-line identifiers.
    check(
        int(df.duplicated().sum()) == 0,
        "Clean dataset contains no exact duplicate records",
    )

    check(
        df["order_line_id"].notna().all(),
        "Every clean record has an order-line ID",
    )

    check(
        not df["order_line_id"].duplicated().any(),
        "Every clean order-line ID is unique",
    )

    # 4. Missing values.
    # Missing customer IDs are intentionally retained and not fabricated.
    non_customer_columns = [
        column for column in df.columns if column != "customer_id"
    ]

    missing_outside_customer = int(
        df[non_customer_columns].isna().sum().sum()
    )

    check(
        missing_outside_customer == 0,
        "No missing values outside customer_id",
    )

    missing_customer_ids = int(df["customer_id"].isna().sum())
    known_customer_rows = int(df["customer_id"].notna().sum())
    unique_customers = int(df["customer_id"].nunique())

    missing_customer_rate = (
        missing_customer_ids / len(df) * 100 if len(df) else 0
    )

    print(f"\nRows with missing customer IDs: {missing_customer_ids:,}")
    print(f"Rows with known customer IDs: {known_customer_rows:,}")
    print(f"Unique known customers: {unique_customers:,}")
    print(f"Missing customer ID rate: {missing_customer_rate:.2f}%")

    check(
        missing_customer_ids + known_customer_rows == len(df),
        "Known and missing customer IDs account for all clean rows",
    )

    # 5. Date validation.
    dates = pd.to_datetime(df["order_date"], errors="coerce")

    check(
        dates.notna().all(),
        "Every clean order date parses successfully",
    )

    check(
        dates.between(
            pd.Timestamp("2023-01-01"),
            pd.Timestamp("2025-12-31"),
        ).all(),
        "All clean order dates fall within 2023-2025",
    )

    # 6. Quantity validation.
    quantity = pd.to_numeric(df["quantity"], errors="coerce")

    valid_quantity = (
        quantity.notna()
        & quantity.gt(0)
        & quantity.mod(1).eq(0)
    )

    check(
        valid_quantity.all(),
        "All quantities are positive whole numbers",
    )

    # 7. Unit-price validation.
    price = pd.to_numeric(df["unit_price_kes"], errors="coerce")

    valid_price = (
        price.notna()
        & price.gt(0)
        & price.lt(1_000_000)
    )

    check(
        valid_price.all(),
        "All unit prices are positive and below KES 1,000,000",
    )

    # 8. Discount validation.
    discount = pd.to_numeric(df["discount_pct"], errors="coerce")

    valid_discount = (
        discount.notna()
        & discount.between(0, 1)
    )

    check(
        valid_discount.all(),
        "All discounts are numeric and between 0 and 1",
    )

    # 9. Net-sales validation.
    net_sales = pd.to_numeric(df["net_sales_kes"], errors="coerce")

    check(
        net_sales.notna().all(),
        "All net sales values are numeric",
    )

    check(
        net_sales.ge(0).all(),
        "All net sales values are nonnegative",
    )

    expected_net_sales = (
        quantity * price * (1 - discount)
    ).round(2)

    formula_matches = (
        (net_sales - expected_net_sales).abs() < 0.011
    )

    check(
        formula_matches.all(),
        "Net sales match quantity x price x (1 - discount)",
    )

    # 10. Required business fields.
    required_non_null = [
        "order_id",
        "order_line_id",
        "product_id",
        "product_name",
        "category",
        "payment_method",
        "county",
    ]

    check(
        df[required_non_null].notna().all().all(),
        "Required order, product, category, payment and county fields exist",
    )

    # 11. Verify the rejected dataset has documented rejection reasons.
    check(
        "rejection_reason" in rejected.columns,
        "Rejected records include a rejection_reason column",
    )

    if "rejection_reason" in rejected.columns:
        check(
            rejected["rejection_reason"].notna().all()
            and rejected["rejection_reason"].str.len().gt(0).all(),
            "Every rejected record has at least one documented reason",
        )

    # 12. Business summary.
    unique_orders = int(df["order_id"].nunique())
    unique_order_lines = int(df["order_line_id"].nunique())
    total_revenue = float(net_sales.sum())
    total_units = int(quantity.sum())
    average_order_value = (
        total_revenue / unique_orders if unique_orders else 0
    )

    print("\n" + "=" * 70)
    print("CLEAN DATASET SUMMARY")
    print("=" * 70)
    print(f"Clean rows: {len(df):,}")
    print(f"Rejected rows: {len(rejected):,}")
    print(f"Unique orders: {unique_orders:,}")
    print(f"Unique order-line IDs: {unique_order_lines:,}")
    print(f"Unique known customers: {unique_customers:,}")
    print(f"Rows with missing customer IDs: {missing_customer_ids:,}")
    print(f"Total units sold: {total_units:,}")
    print(f"Total net sales: KES {total_revenue:,.2f}")
    print(f"Average order value: KES {average_order_value:,.2f}")

    print("\nSALES ROWS BY CATEGORY")
    print(df["category"].value_counts().to_string())

    print("\nSALES ROWS BY PAYMENT METHOD")
    print(df["payment_method"].value_counts().to_string())

    print("\nSALES ROWS BY COUNTY")
    print(df["county"].value_counts().to_string())

    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\nSUCCESS: All validation checks passed.")
    else:
        print("\nACTION REQUIRED: Resolve the failed checks before proceeding.")


if __name__ == "__main__":
    main()
