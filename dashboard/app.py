
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "processed" / "clean_sales.csv"

st.set_page_config(
    page_title="Kenyan Retail Sales Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Kenyan Retail Sales Intelligence")
st.caption(
    "Business intelligence dashboard for fictional Kenyan retail transactions. "
    "All revenue figures are in Kenyan shillings (KES)."
)


# --------------------------------------------------
# 2. LOAD AND VALIDATE DATA
# --------------------------------------------------

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path, parse_dates=["order_date"])

    required = {
        "order_id",
        "order_date",
        "product_name",
        "category",
        "quantity",
        "payment_method",
        "sales_channel",
        "county",
        "net_sales_kes",
    }

    missing = required.difference(data.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    data["quantity"] = pd.to_numeric(
        data["quantity"], errors="coerce"
    )
    data["net_sales_kes"] = pd.to_numeric(
        data["net_sales_kes"], errors="coerce"
    )

    data = data.dropna(
        subset=["order_date", "quantity", "net_sales_kes"]
    )

    return data


if not DATA_FILE.exists():
    st.error(f"Cleaned dataset not found: {DATA_FILE}")
    st.info(
        "Run the project's data generation and cleaning pipeline "
        "first. Refer to README.md for instructions."
    )
    st.stop()

try:
    df = load_data(str(DATA_FILE))
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

if df.empty:
    st.error("The cleaned dataset contains no usable records.")
    st.stop()


# --------------------------------------------------
# 3. INTERACTIVE FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

min_date = df["order_date"].min().date()
max_date = df["order_date"].max().date()

date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
    start_date = end_date = date_range[0]
else:
    start_date = end_date = date_range

if start_date > end_date:
    st.error("The start date must not be later than the end date.")
    st.stop()

filtered = df[
    df["order_date"].dt.date.between(start_date, end_date)
].copy()


def add_multiselect_filter(
    frame: pd.DataFrame,
    column: str,
    label: str,
) -> pd.DataFrame:
    options = sorted(
        frame[column].dropna().astype(str).unique()
    )

    selected = st.sidebar.multiselect(
        label,
        options,
        default=options,
    )

    return frame[
        frame[column].astype(str).isin(selected)
    ]


for column, label in [
    ("county", "County"),
    ("category", "Product category"),
    ("payment_method", "Payment method"),
    ("sales_channel", "Sales channel"),
]:
    filtered = add_multiselect_filter(
        filtered, column, label
    )


# --------------------------------------------------
# 4. EXECUTIVE OVERVIEW
# --------------------------------------------------

st.subheader("Executive Overview")

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

revenue = filtered["net_sales_kes"].sum()
orders = filtered["order_id"].nunique()
units = filtered["quantity"].sum()

average_order_value = (
    revenue / orders if orders else 0
)

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Net Sales",
    f"KES {revenue:,.2f}",
)

k2.metric(
    "Unique Orders",
    f"{orders:,}",
)

k3.metric(
    "Units Sold",
    f"{units:,.0f}",
)

k4.metric(
    "Average Order Value",
    f"KES {average_order_value:,.2f}",
)

st.caption(
    f"Showing {len(filtered):,} order-line records "
    f"from {start_date} to {end_date}."
)


# --------------------------------------------------
# 5. EXECUTIVE INSIGHTS
# --------------------------------------------------

st.subheader("Executive Insights")

category_insights = (
    filtered.groupby("category")["net_sales_kes"]
    .sum()
    .sort_values(ascending=False)
)

county_insights = (
    filtered.groupby("county")["net_sales_kes"]
    .sum()
    .sort_values(ascending=False)
)

product_insights = (
    filtered.groupby("product_name")["net_sales_kes"]
    .sum()
    .sort_values(ascending=False)
)

insight1, insight2, insight3 = st.columns(3)

with insight1:
    if not category_insights.empty:
        st.info(
            f"**Leading category**\n\n"
            f"{category_insights.index[0]}\n\n"
            f"KES {category_insights.iloc[0]:,.2f} in net sales"
        )

with insight2:
    if not county_insights.empty:
        st.info(
            f"**Leading county**\n\n"
            f"{county_insights.index[0]}\n\n"
            f"KES {county_insights.iloc[0]:,.2f} in net sales"
        )

with insight3:
    if not product_insights.empty:
        st.info(
            f"**Leading product**\n\n"
            f"{product_insights.index[0]}\n\n"
            f"KES {product_insights.iloc[0]:,.2f} in net sales"
        )


# --------------------------------------------------
# 6. MONTHLY SALES TRENDS
# --------------------------------------------------

st.subheader("Sales Trends")

trend_data = filtered.copy()

trend_data["month"] = (
    trend_data["order_date"]
    .dt.to_period("M")
    .dt.to_timestamp()
)

monthly = (
    trend_data.groupby("month")
    .agg(
        revenue=("net_sales_kes", "sum"),
        orders=("order_id", "nunique"),
    )
    .sort_index()
)

# Include months without transactions so growth
# compares consecutive calendar months.
if not monthly.empty:
    full_month_range = pd.date_range(
        start=monthly.index.min(),
        end=monthly.index.max(),
        freq="MS",
    )

    monthly = monthly.reindex(
        full_month_range, fill_value=0
    )

    monthly.index.name = "month"
    monthly = monthly.reset_index()

    monthly["month_label"] = (
        monthly["month"].dt.strftime("%Y-%m")
    )

    monthly["revenue_growth_pct"] = (
        monthly["revenue"]
        .pct_change(fill_method=None)
        .mul(100)
    )

    # A zero-sales previous month makes percentage
    # growth mathematically undefined.
    monthly.loc[
        monthly["revenue"].shift(1).eq(0),
        "revenue_growth_pct",
    ] = float("nan")

    latest_month = monthly.iloc[-1]
    previous_month = (
        monthly.iloc[-2] if len(monthly) >= 2 else None
    )

    growth_col1, growth_col2 = st.columns(2)

    with growth_col1:
        if previous_month is not None:
            growth = latest_month["revenue_growth_pct"]

            if pd.notna(growth):
                st.metric(
                    label=(
                        f"Monthly Sales Growth "
                        f"({latest_month['month_label']})"
                    ),
                    value=f"{growth:+.2f}%",
                    delta=f"{growth:+.2f}% vs previous month",
                )
            else:
                st.metric(
                    label=(
                        f"Monthly Sales Growth "
                        f"({latest_month['month_label']})"
                    ),
                    value="N/A",
                    help=(
                        "Growth cannot be calculated when "
                        "the previous month's sales were zero."
                    ),
                )
        else:
            st.info(
                "Select a date range containing at least "
                "two months to calculate sales growth."
            )

    with growth_col2:
        if previous_month is not None:
            revenue_change = (
                latest_month["revenue"]
                - previous_month["revenue"]
            )

            st.metric(
                label="Change in Monthly Net Sales",
                value=f"KES {revenue_change:,.2f}",
                delta=(
                    f"{latest_month['month_label']} "
                    f"vs {previous_month['month_label']}"
                ),
            )

    left, right = st.columns(2)

    with left:
        fig = px.line(
            monthly,
            x="month_label",
            y="revenue",
            markers=True,
            title="Monthly Net Sales",
            labels={
                "month_label": "Month",
                "revenue": "Net Sales (KES)",
            },
        )

        fig.update_layout(
            hovermode="x unified",
            yaxis_tickformat=",.0f",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with right:
        fig = px.bar(
            monthly,
            x="month_label",
            y="orders",
            title="Unique Orders by Month",
            labels={
                "month_label": "Month",
                "orders": "Unique Orders",
            },
            text_auto=",.0f",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# --------------------------------------------------
# 7. PRODUCT PERFORMANCE
# --------------------------------------------------

st.subheader("Product Performance")

left, right = st.columns(2)

category_sales = (
    filtered.groupby("category", as_index=False)
    .agg(revenue=("net_sales_kes", "sum"))
    .sort_values("revenue", ascending=False)
)

with left:
    fig = px.bar(
        category_sales,
        x="category",
        y="revenue",
        title="Net Sales by Category",
        labels={
            "category": "Product Category",
            "revenue": "Net Sales (KES)",
        },
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

product_sales = (
    filtered.groupby("product_name", as_index=False)
    .agg(
        revenue=("net_sales_kes", "sum"),
        units=("quantity", "sum"),
    )
    .sort_values("revenue", ascending=False)
    .head(10)
    .sort_values("revenue")
)

with right:
    fig = px.bar(
        product_sales,
        x="revenue",
        y="product_name",
        orientation="h",
        title="Top 10 Products by Net Sales",
        labels={
            "product_name": "Product",
            "revenue": "Net Sales (KES)",
        },
        hover_data=["units"],
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# --------------------------------------------------
# 8. GEOGRAPHIC AND PAYMENT ANALYSIS
# --------------------------------------------------

st.subheader("Geographic and Payment Analysis")

left, right = st.columns(2)

county_sales = (
    filtered.groupby("county", as_index=False)
    .agg(revenue=("net_sales_kes", "sum"))
    .sort_values("revenue", ascending=False)
)

with left:
    fig = px.bar(
        county_sales.head(15).sort_values("revenue"),
        x="revenue",
        y="county",
        orientation="h",
        title="Top 15 Counties by Net Sales",
        labels={
            "county": "County",
            "revenue": "Net Sales (KES)",
        },
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

payment_sales = (
    filtered.groupby("payment_method", as_index=False)
    .agg(revenue=("net_sales_kes", "sum"))
    .sort_values("revenue", ascending=False)
)

with right:
    fig = px.pie(
        payment_sales,
        names="payment_method",
        values="revenue",
        title="Revenue Share by Payment Method",
        hole=0.4,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# --------------------------------------------------
# 9. FILTERED TRANSACTION DETAILS
# --------------------------------------------------

st.subheader("Filtered Transaction Details")

display_columns = [
    column
    for column in [
        "order_id",
        "order_line_id",
        "order_date",
        "product_name",
        "category",
        "quantity",
        "payment_method",
        "sales_channel",
        "county",
        "net_sales_kes",
    ]
    if column in filtered.columns
]

st.dataframe(
    filtered[display_columns].sort_values(
        "order_date",
        ascending=False,
    ),
    use_container_width=True,
    hide_index=True,
)

csv_data = filtered[display_columns].to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "Download filtered sales as CSV",
    data=csv_data,
    file_name="filtered_retail_sales.csv",
    mime="text/csv",
)


# --------------------------------------------------
# 10. FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Data source: locally generated fictional Kenyan retail data. "
    "All metrics, insights, and charts respond to the selected filters. "
    "Net sales represent the values recorded in the cleaned dataset."
)
