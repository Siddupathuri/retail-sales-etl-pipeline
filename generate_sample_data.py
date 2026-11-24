"""Generate a realistic (and deliberately messy) raw retail sales dataset.

The result mimics what you get from a store system export: duplicate rows,
missing values, currency symbols, mixed date formats and bad quantities.

Run from the project root:
    python scripts/generate_sample_data.py
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

PRODUCTS = [
    ("P001", "Wireless Mouse", "Electronics", 24.99),
    ("P002", "Mechanical Keyboard", "Electronics", 89.50),
    ("P003", "27-inch Monitor", "Electronics", 249.00),
    ("P004", "USB-C Hub", "Electronics", 39.95),
    ("P005", "Bluetooth Speaker", "Electronics", 59.00),
    ("P006", "Noise Cancelling Headphones", "Electronics", 199.00),
    ("P007", "Running Shoes", "Apparel", 74.99),
    ("P008", "Cotton T-Shirt", "Apparel", 19.99),
    ("P009", "Denim Jeans", "Apparel", 49.50),
    ("P010", "Rain Jacket", "Apparel", 119.00),
    ("P011", "Wool Socks (3 pack)", "Apparel", 14.25),
    ("P012", "Coffee Maker", "Home", 99.00),
    ("P013", "Non-stick Frying Pan", "Home", 34.50),
    ("P014", "Bed Linen Set", "Home", 64.00),
    ("P015", "Desk Lamp", "Home", 29.99),
    ("P016", "Yoga Mat", "Sports", 27.00),
    ("P017", "Dumbbell Set", "Sports", 149.00),
    ("P018", "Water Bottle (1L)", "Sports", 12.99),
    ("P019", "Office Chair", "Furniture", 179.00),
    ("P020", "Bookshelf", "Furniture", 129.50),
]

STORES = [
    ("S01", "Hyderabad Central", "Hyderabad"),
    ("S02", "Vijayawada Mall", "Vijayawada"),
    ("S03", "Guntur City Store", "Guntur"),
    ("S04", "Visakhapatnam Bay", "Visakhapatnam"),
    ("S05", "Bengaluru Tech Park", "Bengaluru"),
    ("S06", "Online Store", "Online"),
]

HEADER = [
    "order_id",
    "order_date",
    "product_id",
    "product_name",
    "category",
    "store_id",
    "store_name",
    "city",
    "quantity",
    "unit_price",
    "discount",
]


def messy_date(d: date) -> str:
    """Return the same date in one of several formats, like a real export."""
    choice = random.random()
    if choice < 0.55:
        return d.isoformat()
    if choice < 0.8:
        return d.strftime("%d/%m/%Y")
    if choice < 0.93:
        return d.strftime("%d-%m-%Y")
    return d.strftime("%b %d, %Y")


def messy_price(value: float) -> str:
    choice = random.random()
    if choice < 0.15:
        return f"${value:,.2f}"
    if choice < 0.25:
        return f"{value:,.2f}"
    return f"{value:.2f}"


def build_rows(total_orders: int = 900) -> list[list[str]]:
    random.seed(42)
    start = date(2024, 1, 1)
    rows: list[list[str]] = []

    for order_no in range(1, total_orders + 1):
        order_id = f"ORD{order_no:05d}"
        order_day = start + timedelta(days=random.randint(0, 364))
        store = random.choice(STORES)
        # Most orders have 1-3 line items
        for line in range(1, random.randint(1, 3) + 1):
            product = random.choice(PRODUCTS)
            quantity = random.choices([1, 1, 1, 2, 2, 3, 4], k=1)[0]
            discount_rate = random.choice([0, 0, 0, 0, 0.05, 0.10, 0.15])
            rows.append(
                [
                    order_id,
                    messy_date(order_day),
                    product[0],
                    product[1],
                    product[2],
                    store[0],
                    store[1],
                    store[2],
                    str(quantity),
                    messy_price(product[3]),
                    f"{discount_rate:.2f}",
                ]
            )

    # ---- inject realistic data-quality problems ----
    # 1. Duplicate rows (same order + product exported twice)
    for _ in range(35):
        rows.append(list(random.choice(rows)))

    # 2. Missing values
    for idx in random.sample(range(len(rows)), 30):
        column = random.choice([2, 6, 8, 9])
        rows[idx][column] = ""

    # 3. Invalid quantities (returns / data entry errors)
    for idx in random.sample(range(len(rows)), 10):
        rows[idx][8] = random.choice(["0", "-1", "abc"])

    # 4. Empty / whitespace strings and inconsistent casing
    for idx in random.sample(range(len(rows)), 25):
        rows[idx][1] = f"  {rows[idx][1]}  "
    for idx in random.sample(range(len(rows)), 15):
        rows[idx][3] = rows[idx][3].upper()

    random.shuffle(rows)
    return rows


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output = RAW_DIR / "retail_sales_raw.csv"
    rows = build_rows()
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)
    print(f"Wrote {len(rows):,} raw rows to {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
