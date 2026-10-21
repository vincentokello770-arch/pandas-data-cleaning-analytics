
"""Analyze cleaned Kenyan retail sales and export portfolio reports."""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. PROJECT PATHS AND CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = ROOT / "data" / "processed" / "clean_sales.csv"
REPORTS = ROOT / "reports"
CHARTS = REPORTS / "charts"

REPORTS.mkdir(parents=True, exist_ok=True)
CHARTS.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. LOAD AND CHECK THE DATA
# ============================================================

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Cleaned dataset not found: {DATA_FILE}\n"
        "Run src/clean_data.py first."
    )

df = pd.read_csv(DATA_FILE)

required_columns = [
    "order_id",
    "order_date",
    "customer_id",
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
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Required columns are missing: {missing_columns}"
    )

if df.empty:
    raise ValueError("The cleaned dataset contains no rows.")

df["order_date"] = pd.to_datetime(
    df["order_date"], errors="coerce"
)

numeric_columns = [
    "quantity",
    "unit_price_kes",
    "discount_pct",
    "net_sales_kes",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column], errors="coerce"
    )

if df["order_date"].isna().any():
    raise ValueError("Invalid dates found in the cleaned dataset.")

if df[numeric_columns].isna().any().any():
    raise ValueError("Missing or invalid numeric values found.")

if df["order_id"].isna().any():
    raise ValueError("Missing order IDs found.")

# Customer IDs may be missing by design.
# These records remain valid for sales analysis.

df["month"] = df["order_date"].dt.to_period("M").astype(str)

# Revenue before discounts.
df["gross_sales_kes"] = (
    df["quantity"] * df["unit_price_kes"]
)

# Amount deducted through discounts.
df["discount_amount_kes"] = (
    df["gross_sales_kes"] * df["discount_pct"]
)


# ============================================================
# 3. KEY PERFORMANCE INDICATORS (KPIs)
# ============================================================

total_rows = len(df)
unique_orders = int(df["order_id"].nunique())
unique_customers = int(df["customer_id"].nunique())
missing_customer_ids = int(df["customer_id"].isna().sum())

total_net_sales = float(df["net_sales_kes"].sum())
total_gross_sales = float(df["gross_sales_kes"].sum())
total_discounts = float(df["discount_amount_kes"].sum())
total_units = int(df["quantity"].sum())

average_line_value = float(df["net_sales_kes"].mean())

# Aggregate all lines belonging to each order before calculating AOV.
order_totals = (
    df.groupby("order_id", as_index=False)
    .agg(
        order_net_sales_kes=("net_sales_kes", "sum"),
        order_date=("order_date", "min"),
    )
)

average_order_value = (
    float(order_totals["order_net_sales_kes"].mean())
    if len(order_totals)
    else 0.0
)

kpis = pd.DataFrame([
    {
        "metric": "clean_sales_rows",
        "value": total_rows,
        "description": "Number of cleaned sales lines",
    },
    {
        "metric": "unique_orders",
        "value": unique_orders,
        "description": "Distinct order IDs",
    },
    {
        "metric": "unique_known_customers",
        "value": unique_customers,
        "description": "Distinct non-missing customer IDs",
    },
    {
        "metric": "missing_customer_id_rows",
        "value": missing_customer_ids,
        "description": "Sales lines without customer attribution",
    },
    {
        "metric": "missing_customer_id_pct",
        "value": round(missing_customer_ids / total_rows * 100, 2),
        "description": "Percentage of sales lines with unknown customers",
    },
    {
        "metric": "total_net_sales_kes",
        "value": round(total_net_sales, 2),
        "description": "Sales revenue after discounts",
    },
    {
        "metric": "total_gross_sales_kes",
        "value": round(total_gross_sales, 2),
        "description": "Sales value before discounts",
    },
    {
        "metric": "total_discount_amount_kes",
        "value": round(total_discounts, 2),
        "description": "Discount amount calculated from line values",
    },
    {
        "metric": "average_sales_line_value_kes",
        "value": round(average_line_value, 2),
        "description": "Mean net value of an individual sales line",
    },
    {
        "metric": "average_order_value_kes",
        "value": round(average_order_value, 2),
        "description": "Total net sales divided by distinct orders",
    },
    {
        "metric": "total_units_sold",
        "value": total_units,
        "description": "Total units sold across all sales lines",
    },
])

kpis.to_csv(REPORTS / "sales_kpis.csv", index=False)


# ============================================================
# 4. MONTHLY SALES ANALYSIS
# ============================================================

monthly = (
    df.groupby("month", as_index=False)
    .agg(
        sales_lines=("order_id", "size"),
        unique_orders=("order_id", "nunique"),
        units_sold=("quantity", "sum"),
        net_sales_kes=("net_sales_kes", "sum"),
    )
    .sort_values("month")
)

monthly["net_sales_kes"] = monthly["net_sales_kes"].round(2)

monthly.to_csv(REPORTS / "monthly_sales.csv", index=False)


# ============================================================
# 5. PRODUCT CATEGORY ANALYSIS
# ============================================================

category = (
    df.groupby("category", dropna=False)
    .agg(
        sales_lines=("order_id", "size"),
        units_sold=("quantity", "sum"),
        net_sales_kes=("net_sales_kes", "sum"),
    )
    .reset_index()
    .sort_values("net_sales_kes", ascending=False)
)

category["revenue_share_pct"] = (
    category["net_sales_kes"] / total_net_sales * 100
).round(2)

category["net_sales_kes"] = category["net_sales_kes"].round(2)

category.to_csv(REPORTS / "sales_by_category.csv", index=False)


# ============================================================
# 6. COUNTY ANALYSIS
# ============================================================

county = (
    df.groupby("county", dropna=False)
    .agg(
        sales_lines=("order_id", "size"),
        unique_orders=("order_id", "nunique"),
        units_sold=("quantity", "sum"),
        net_sales_kes=("net_sales_kes", "sum"),
    )
    .reset_index()
    .sort_values("net_sales_kes", ascending=False)
)

county["revenue_share_pct"] = (
    county["net_sales_kes"] / total_net_sales * 100
).round(2)

county["net_sales_kes"] = county["net_sales_kes"].round(2)

county.to_csv(REPORTS / "sales_by_county.csv", index=False)


# ============================================================
# 7. PAYMENT METHOD ANALYSIS
# ============================================================

payment = (
    df.groupby("payment_method", dropna=False)
    .agg(
        sales_lines=("order_id", "size"),
        unique_orders=("order_id", "nunique"),
        net_sales_kes=("net_sales_kes", "sum"),
    )
    .reset_index()
    .sort_values("net_sales_kes", ascending=False)
)

payment["revenue_share_pct"] = (
    payment["net_sales_kes"] / total_net_sales * 100
).round(2)

payment["net_sales_kes"] = payment["net_sales_kes"].round(2)

payment.to_csv(
    REPORTS / "sales_by_payment_method.csv", index=False
)


# ============================================================
# 8. TOP 10 PRODUCTS
# ============================================================

products = (
    df.groupby("product_name", dropna=False)
    .agg(
        sales_lines=("order_id", "size"),
        units_sold=("quantity", "sum"),
        net_sales_kes=("net_sales_kes", "sum"),
    )
    .reset_index()
    .sort_values("net_sales_kes", ascending=False)
    .head(10)
)

products["net_sales_kes"] = products["net_sales_kes"].round(2)

products.to_csv(REPORTS / "top_10_products.csv", index=False)


# ============================================================
# 9. ORDER-LEVEL ANALYSIS
# ============================================================

order_totals["net_sales_kes"] = (
    order_totals["order_net_sales_kes"].round(2)
)

order_totals["order_date"] = (
    order_totals["order_date"].dt.strftime("%Y-%m-%d")
)

order_totals = order_totals.drop(
    columns=["order_net_sales_kes"]
)

order_totals.to_csv(
    REPORTS / "order_level_analysis.csv", index=False
)


# ============================================================
# 10. CHART 1: MONTHLY REVENUE TREND
# ============================================================

fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(
    monthly["month"],
    monthly["net_sales_kes"],
    marker="o",
    linewidth=2,
)

ax.set_title("Monthly Net Sales Trend")
ax.set_xlabel("Month")
ax.set_ylabel("Net sales (KES)")
ax.tick_params(axis="x", rotation=60)
ax.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(CHARTS / "monthly_sales_trend.png", dpi=160)
plt.close(fig)


# ============================================================
# 11. CHART 2: CATEGORY REVENUE
# ============================================================

category_chart = category.sort_values("net_sales_kes")

fig, ax = plt.subplots(figsize=(10, 6))

ax.barh(
    category_chart["category"].astype(str),
    category_chart["net_sales_kes"],
)

ax.set_title("Net Sales by Product Category")
ax.set_xlabel("Net sales (KES)")
ax.set_ylabel("Category")

fig.tight_layout()
fig.savefig(CHARTS / "sales_by_category.png", dpi=160)
plt.close(fig)


# ============================================================
# 12. CHART 3: TOP 10 COUNTIES
# ============================================================

county_chart = (
    county.head(10)
    .sort_values("net_sales_kes")
)

fig, ax = plt.subplots(figsize=(10, 6))

ax.barh(
    county_chart["county"].astype(str),
    county_chart["net_sales_kes"],
)

ax.set_title("Top 10 Counties by Net Sales")
ax.set_xlabel("Net sales (KES)")
ax.set_ylabel("County")

fig.tight_layout()
fig.savefig(CHARTS / "top_counties.png", dpi=160)
plt.close(fig)


# ============================================================
# 13. CHART 4: PAYMENT METHOD REVENUE
# ============================================================

payment_chart = payment.sort_values("net_sales_kes")

fig, ax = plt.subplots(figsize=(10, 5))

ax.barh(
    payment_chart["payment_method"].astype(str),
    payment_chart["net_sales_kes"],
)

ax.set_title("Net Sales by Payment Method")
ax.set_xlabel("Net sales (KES)")
ax.set_ylabel("Payment method")

fig.tight_layout()
fig.savefig(CHARTS / "sales_by_payment_method.png", dpi=160)
plt.close(fig)


# ============================================================
# 14. PRINT SUMMARY
# ============================================================

print("=" * 65)
print("KENYAN RETAIL SALES ANALYTICS")
print("=" * 65)

print(f"Clean sales rows: {total_rows:,}")
print(f"Unique orders: {unique_orders:,}")
print(f"Unique known customers: {unique_customers:,}")
print(f"Rows with missing customer IDs: {missing_customer_ids:,}")
print(f"Total units sold: {total_units:,}")
print(f"Gross sales: KES {total_gross_sales:,.2f}")
print(f"Discount amount: KES {total_discounts:,.2f}")
print(f"Net sales: KES {total_net_sales:,.2f}")
print(f"Average sales line value: KES {average_line_value:,.2f}")
print(f"Average order value: KES {average_order_value:,.2f}")

print("\nTOP 5 PRODUCT CATEGORIES")
print(category.head(5).to_string(index=False))

print("\nTOP 5 COUNTIES BY NET SALES")
print(county.head(5).to_string(index=False))

print("\nTOP 5 PRODUCTS BY NET SALES")
print(products.head(5).to_string(index=False))

print("\nSALES BY PAYMENT METHOD")
print(payment.to_string(index=False))

print("\nOUTPUT FILES")
print(f"Reports: {REPORTS}")
print(f"Charts: {CHARTS}")

print("\nAnalytics script completed successfully.")
