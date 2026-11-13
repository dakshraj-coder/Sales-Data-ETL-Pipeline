"""
generate_sample_data.py
-----------------------
Creates SYNTHETIC (made-up) sales CSV files in data/raw/ so you can run the project.

The data is intentionally a little messy (mixed date formats, duplicates, missing
values, invalid rows) so the cleaning step has real work to do.
All names, prices and orders are invented. Nothing here is real business data.

Run it with:   python src/generate_sample_data.py
The random seed is fixed, so everyone who runs it gets the SAME files.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RUPEE = "\u20b9"  # the rupee symbol

rng = random.Random(42)

PRODUCTS = [
    ("P001", "Wireless Mouse", "Electronics", 699),
    ("P002", "USB-C Cable", "Electronics", 349),
    ("P003", "Bluetooth Speaker", "Electronics", 1999),
    ("P004", "Power Bank 10000mAh", "Electronics", 1499),
    ("P005", "Wired Earphones", "Electronics", 899),
    ("P006", "Spiral Notebook A5", "Stationery", 120),
    ("P007", "Gel Pen Pack of 10", "Stationery", 150),
    ("P008", "Desk Organizer", "Stationery", 450),
    ("P009", "Highlighter Set", "Stationery", 220),
    ("P010", "Steel Water Bottle 1L", "Home & Kitchen", 599),
    ("P011", "Non-Stick Frying Pan", "Home & Kitchen", 1099),
    ("P012", "LED Desk Lamp", "Home & Kitchen", 899),
    ("P013", "Storage Box Set", "Home & Kitchen", 799),
    ("P014", "Yoga Mat", "Fitness", 799),
    ("P015", "Resistance Bands Set", "Fitness", 549),
    ("P016", "Skipping Rope", "Fitness", 249),
    ("P017", "Dumbbell Pair 5kg", "Fitness", 1299),
    ("P018", "Python Programming Handbook", "Books", 499),
    ("P019", "SQL Basics Guide", "Books", 399),
    ("P020", "Data Analysis Workbook", "Books", 449),
]

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Sai", "Arjun", "Rohan", "Karthik", "Ishaan",
               "Ananya", "Diya", "Priya", "Sneha", "Kavya", "Meera", "Nisha", "Pooja",
               "Rahul", "Neha", "Varun", "Sanjana"]
LAST_NAMES = ["Sharma", "Reddy", "Patel", "Iyer", "Nair", "Gupta", "Singh", "Das",
              "Mehta", "Rao", "Kumar", "Joshi"]
CITIES = ["Hyderabad", "Bengaluru", "Mumbai", "Delhi", "Chennai", "Pune",
          "Kolkata", "Ahmedabad", "Jaipur", "Kochi"]
PAYMENTS = ["UPI", "UPI", "UPI", "Credit Card", "Debit Card", "Cash on Delivery", "Net Banking"]

HEADER = ["order_id", "order_date", "customer_id", "customer_name", "city", "product_id",
          "product_name", "category", "quantity", "unit_price", "discount_percent",
          "payment_method"]

# Build 45 customers.
CUSTOMERS = []
for i in range(45):
    name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    CUSTOMERS.append((f"C{1001 + i}", name, rng.choice(CITIES)))


def format_date(d):
    """Write the date in one of three styles, to mimic messy real-world files."""
    r = rng.random()
    if r < 0.55:
        return d.strftime("%Y-%m-%d")
    if r < 0.85:
        return d.strftime("%d/%m/%Y")
    return d.strftime("%d %b %Y")


def format_price(price):
    r = rng.random()
    if r < 0.60:
        return str(price)
    if r < 0.80:
        return f"{price:.2f}"
    if r < 0.90:
        return f"{RUPEE}{price:,.2f}"
    return f"Rs. {price:,}"


def messy_text(text, kind):
    """Randomly add case/space problems to a text value."""
    r = rng.random()
    if r < 0.08:
        return text.upper()
    if r < 0.13:
        return text.lower()
    if r < 0.21:
        return f"  {text} "
    return text


def make_order(order_no, start, end):
    days = (end - start).days
    d = start + timedelta(days=rng.randint(0, days))
    cust_id, cust_name, city = rng.choice(CUSTOMERS)
    p_id, p_name, category, price = rng.choice(PRODUCTS)
    qty = rng.choices([1, 2, 3, 4, 5], weights=[50, 28, 12, 6, 4])[0]
    discount = rng.choice([0, 0, 0, 0, 5, 10, 15])

    row = {
        "order_id": f"ORD-{order_no}",
        "order_date": format_date(d),
        "customer_id": cust_id,
        "customer_name": messy_text(cust_name, "name"),
        "city": messy_text(city, "city"),
        "product_id": p_id,
        "product_name": p_name,
        "category": messy_text(category, "category"),
        "quantity": str(qty),
        "unit_price": format_price(price),
        "discount_percent": str(discount) if rng.random() > 0.06 else "",
        "payment_method": rng.choice(PAYMENTS),
    }
    # small random gaps in optional fields
    if rng.random() < 0.02:
        row["customer_name"] = ""
    if rng.random() < 0.03:
        row["city"] = ""
    if rng.random() < 0.10:
        row["payment_method"] = rng.choice(["upi", "credit card", "COD", "cash on delivery"])
    return row


def build_file_rows(first_order_no, count, start, end):
    return [make_order(first_order_no + i, start, end) for i in range(count)]


def add_invalid_records(rows):
    """Damage a few specific rows on purpose so the validation step can catch them."""
    picks = rng.sample(range(len(rows)), 22)
    for idx in picks[0:3]:
        rows[idx]["customer_id"] = ""            # missing customer id
    for idx in picks[3:6]:
        rows[idx]["quantity"] = "-2"             # negative quantity
    for idx in picks[6:8]:
        rows[idx]["unit_price"] = "abc"          # not a number
    for idx in picks[8:10]:
        rows[idx]["unit_price"] = "0"            # zero price
    rows[picks[10]]["order_date"] = "31/02/2024"       # date that does not exist
    rows[picks[11]]["order_date"] = "not available"    # not a date
    rows[picks[12]]["order_date"] = "2030-01-05"       # future date
    for idx in picks[13:15]:
        rows[idx]["discount_percent"] = "150"    # impossible discount
    for idx in picks[15:17]:
        rows[idx]["quantity"] = ""               # missing quantity
    rows[picks[17]]["product_id"] = ""           # missing product id
    rows[picks[18]]["quantity"] = "2.5"          # not a whole number
    return rows


def add_duplicates(rows, how_many):
    """Copy some rows so the same order appears twice (a common real-world problem)."""
    for idx in rng.sample(range(len(rows)), how_many):
        copy = dict(rows[idx])
        if rng.random() < 0.5:
            copy["customer_name"] = "  " + copy["customer_name"] + " "  # extra spaces
        rows.insert(rng.randint(0, len(rows)), copy)
    return rows


def write_csv(path, rows, header_style="plain"):
    header = HEADER
    if header_style == "title":
        header = [h.replace("_", " ").title() for h in HEADER]  # "Order Id", "Order Date", ...
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for r in rows:
            writer.writerow([r[h] for h in HEADER])


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    q1 = build_file_rows(240001, 230, date(2024, 1, 1), date(2024, 3, 31))
    q2 = build_file_rows(240301, 250, date(2024, 4, 1), date(2024, 6, 30))
    q3 = build_file_rows(240601, 240, date(2024, 7, 1), date(2024, 9, 30))

    q1 = add_duplicates(add_invalid_records(q1), 6)
    q2 = add_duplicates(add_invalid_records(q2), 6)
    q3 = add_duplicates(q3, 3)  # this file is mostly clean but has different header names

    write_csv(RAW_DIR / "sales_2024_q1.csv", q1)
    write_csv(RAW_DIR / "sales_2024_q2.csv", q2)
    write_csv(RAW_DIR / "sales_2024_q3.csv", q3, header_style="title")

    print(f"Created 3 CSV files in {RAW_DIR}")
    print(f"Rows: Q1={len(q1)}, Q2={len(q2)}, Q3={len(q3)}")


if __name__ == "__main__":
    main()
