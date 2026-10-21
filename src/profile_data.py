from pathlib import Path
import pandas as pd

DATA_FILE = Path("data/raw/messy_sales.csv")

df = pd.read_csv(DATA_FILE, dtype="string", low_memory=False)

print("=" * 65)
print("SALES DATA QUALITY PROFILE")
print("=" * 65)
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")
print(f"Exact duplicate rows: {df.duplicated().sum():,}")

print("\n--- MISSING VALUES ---")
missing = df.isna().sum()
missing = missing[missing > 0].sort_values(ascending=False)
print(missing.to_string() if not missing.empty else "None")

print("\n--- DATE QUALITY ---")
dates = pd.to_datetime(df["order_date"], errors="coerce")
print(f"Unparseable dates: {dates.isna().sum():,}")
print(f"Earliest valid date: {dates.min()}")
print(f"Latest valid date:   {dates.max()}")

print("\n--- NUMERIC QUALITY ---")
for column in ["quantity", "unit_price_kes", "discount_pct"]:
    values = pd.to_numeric(df[column], errors="coerce")
    print(f"\n{column}")
    print(f"  Missing or non-numeric: {values.isna().sum():,}")
    print(f"  Minimum valid value:   {values.min()}")
    print(f"  Maximum valid value:   {values.max()}")

    if column in ["quantity", "unit_price_kes"]:
        print(f"  Zero or negative:      {(values <= 0).sum():,}")

discount = pd.to_numeric(df["discount_pct"], errors="coerce")
print(f"\nDiscount outside 0-1: {((discount < 0) | (discount > 1)).sum():,}")

print("\n--- TEXT WHITESPACE ---")
text_columns = df.select_dtypes(include="string").columns
for column in text_columns:
    values = df[column].dropna()
    count = values.ne(values.str.strip()).sum()
    if count:
        print(f"{column}: {count:,} values with leading/trailing spaces")
print("Whitespace scan complete.")

print("\n--- CATEGORY VARIATIONS ---")
for column in ["customer_segment", "category", "payment_method",
               "sales_channel", "county"]:
    print(f"\n{column}:")
    print(df[column].value_counts(dropna=False).head(15).to_string())

print("\n--- IDENTIFIER CHECKS ---")
for column in ["order_id", "order_line_id", "customer_id", "product_id"]:
    print(
        f"{column}: unique={df[column].nunique(dropna=True):,}, "
        f"missing={df[column].isna().sum():,}"
    )

print("\nProfile complete. No raw data has been modified.")
