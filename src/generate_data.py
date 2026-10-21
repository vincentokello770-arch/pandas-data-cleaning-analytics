
"""Generate a fictional Kenyan retail dataset with deliberate data-quality defects."""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "raw" / "messy_sales.csv"

SEED = 20261021
N = 150_000
LINES_PER_ORDER = 2

random.seed(SEED)

products = [
    ("SKU1001", "Smartphone", "Electronics", 18000),
    ("SKU1002", "Laptop", "Electronics", 65000),
    ("SKU1003", "USB Cable", "Electronics", 450),
    ("SKU1004", "Headphones", "Electronics", 2800),
    ("SKU1005", "Power Bank", "Electronics", 2200),
    ("SKU1006", "LED TV", "Electronics", 42000),
    ("SKU2001", "Rice 2kg", "Groceries", 380),
    ("SKU2002", "Cooking Oil 1L", "Groceries", 320),
    ("SKU2003", "Maize Flour 2kg", "Groceries", 180),
    ("SKU2004", "Tea 500g", "Groceries", 450),
    ("SKU2005", "Sugar 2kg", "Groceries", 310),
    ("SKU3001", "Detergent", "Household", 520),
    ("SKU3002", "Cooking Pot", "Household", 1500),
    ("SKU3003", "Water Bottle", "Household", 650),
    ("SKU3004", "Bedsheet", "Household", 2200),
    ("SKU4001", "T-Shirt", "Clothing", 900),
    ("SKU4002", "Jeans", "Clothing", 2400),
    ("SKU4003", "Sneakers", "Clothing", 3800),
    ("SKU4004", "School Bag", "Clothing", 1800),
    ("SKU5001", "Office Chair", "Furniture", 8500),
    ("SKU5002", "Study Desk", "Furniture", 12500),
    ("SKU5003", "Bookshelf", "Furniture", 9200),
    ("SKU6001", "Football", "Sports", 1200),
    ("SKU6002", "Yoga Mat", "Sports", 1700),
    ("SKU6003", "Skipping Rope", "Sports", 350),
    ("SKU7001", "Printer Paper", "Stationery", 650),
    ("SKU7002", "Notebook Pack", "Stationery", 420),
    ("SKU7003", "Ballpoint Pens", "Stationery", 180),
]

counties = {
    "Nairobi": ["Nairobi", "Westlands", "Embakasi", "Kasarani"],
    "Mombasa": ["Mombasa", "Nyali", "Likoni"],
    "Kisumu": ["Kisumu", "Kondele"],
    "Nakuru": ["Nakuru", "Naivasha"],
    "Uasin Gishu": ["Eldoret", "Turbo"],
    "Kiambu": ["Thika", "Ruiru", "Kiambu"],
    "Machakos": ["Machakos", "Athi River"],
    "Kakamega": ["Kakamega", "Mumias"],
    "Meru": ["Meru", "Maua"],
    "Kisii": ["Kisii", "Ogembo"],
    "Migori": ["Migori", "Kehancha"],
    "Nyeri": ["Nyeri", "Karatina"],
}

methods = ["M-Pesa", "Cash", "Card", "Bank Transfer"]
segments = ["Retail", "Wholesale", "Small Business", "Corporate"]
channels = ["Store", "Online", "Phone Order"]

headers = [
    "order_id",
    "order_line_id",
    "order_date",
    "customer_id",
    "customer_segment",
    "product_id",
    "product_name",
    "category",
    "quantity",
    "unit_price_kes",
    "discount_pct",
    "payment_method",
    "sales_channel",
    "county",
    "town",
    "sales_rep",
]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
start = datetime(2023, 1, 1)

if N % LINES_PER_ORDER != 0:
    raise ValueError("N must be divisible by LINES_PER_ORDER.")

order_count = N // LINES_PER_ORDER

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers)

    for i in range(1, N + 1):
        # Group every two sales lines under one sequential order ID.
        order_no = ((i - 1) // LINES_PER_ORDER) + 1
        line_no = ((i - 1) % LINES_PER_ORDER) + 1
        order_id = f"ORD{order_no:06d}"
        order_line_id = f"{order_id}-L{line_no}"

        # Generate stable order-level attributes for both lines.
        order_rng = random.Random(SEED + order_no)

        county = order_rng.choice(list(counties))
        town = order_rng.choice(counties[county])
        order_date = start + timedelta(days=order_rng.randrange(1095))
        customer_id = f"CUST{order_rng.randint(1, 18000):05d}"
        customer_segment = order_rng.choice(segments)
        payment_method = order_rng.choice(methods)
        sales_channel = order_rng.choice(channels)
        sales_rep = f"REP{order_rng.randint(1, 120):03d}"

        # Generate the individual product line.
        product = random.choice(products)

        quantity = random.choices(
            [1, 2, 3, 4, 5, 6, 8, 10, 12, 20, 30],
            [30, 22, 15, 10, 8, 5, 3, 3, 2, 1, 1],
        )[0]

        unit_price = round(
            product[3] * random.uniform(0.88, 1.13), 2
        )

        discount_pct = random.choices(
            [0, 0.05, 0.10, 0.15, 0.20],
            [45, 20, 20, 10, 5],
        )[0]

        row = [
            order_id,
            order_line_id,
            order_date.strftime("%Y-%m-%d"),
            customer_id,
            customer_segment,
            product[0],
            product[1],
            product[2],
            quantity,
            unit_price,
            discount_pct,
            payment_method,
            sales_channel,
            county,
            town,
            sales_rep,
        ]

        # Intentionally introduce data-quality problems for cleaning practice.
        r = random.random()

        if r < 0.025:
            row[3] = "" if random.random() < 0.7 else "NULL"

        if r < 0.018:
            row[8] = "" if random.random() < 0.6 else "unknown"

        if r < 0.012:
            row[9] = "" if random.random() < 0.7 else "N/A"

        if r < 0.008:
            row[2] = random.choice(
                ["31/02/2024", "not-a-date", "2024-13-45"]
            )

        if r < 0.012:
            row[8] = random.choice([-5, -1, 0, "two", ""])

        if r < 0.007:
            row[9] = random.choice([-100, 0, 9999999, "free", ""])

        if r < 0.012:
            row[7] = random.choice(
                [
                    "electronics",
                    " ELECTRONICS ",
                    "Grocery",
                    "groceries",
                    "HOUSEHOLD",
                    "",
                ]
            )

        if r < 0.01:
            row[11] = random.choice(
                ["m-pesa", "M-PESA", " Mpesa ", "", "cash"]
            )

        if r < 0.009:
            row[13] = random.choice(
                ["nairobi", " NAIROBI ", "NAIROBI", "", "Nairobii"]
            )

        if r < 0.004:
            row[10] = random.choice([1.5, 1.25, -0.1, 1.5])

        # Add a deliberate exact duplicate every 2,500 source lines.
        if i % 2500 == 0:
            writer.writerow(row)

        writer.writerow(row)

print(f"Generated {N:,} source records across {order_count:,} orders.")
print(f"Additional deliberate duplicate rows: {N // 2500:,}")
print(f"Raw dataset: {OUTPUT}")
