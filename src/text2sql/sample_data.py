"""Builds a small, reproducible e-commerce SQLite database for demos and tests."""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    signup_date TEXT NOT NULL
);
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL
);
"""

FIRST = ["Aarav", "Diya", "Rohan", "Ananya", "Kabir", "Isha", "Vihaan", "Meera", "Arjun", "Saanvi"]
LAST = ["Sharma", "Verma", "Gupta", "Singh", "Patel", "Reddy", "Nair", "Mehta", "Khan", "Joshi"]
CITIES = ["Delhi", "Mumbai", "Bengaluru", "Pune", "Chennai", "Kolkata", "Hyderabad"]
PRODUCTS = [
    ("Wireless Earbuds", "Electronics", 1999), ("Smart Watch", "Electronics", 3499),
    ("Power Bank", "Electronics", 1299), ("Bluetooth Speaker", "Electronics", 2199),
    ("Running Shoes", "Fashion", 2799), ("Denim Jacket", "Fashion", 2399),
    ("Backpack", "Fashion", 1499), ("Sunglasses", "Fashion", 999),
    ("Mixer Grinder", "Home", 3299), ("Air Fryer", "Home", 4999),
    ("Desk Lamp", "Home", 899), ("Cotton Bedsheet", "Home", 1199),
    ("Yoga Mat", "Fitness", 799), ("Dumbbell Set", "Fitness", 2599),
    ("Protein Powder", "Fitness", 2899), ("Skipping Rope", "Fitness", 299),
    ("Python Crash Course", "Books", 699), ("Data Science Handbook", "Books", 899),
    ("Atomic Habits", "Books", 499), ("SQL Cookbook", "Books", 799),
]
STATUSES = ["delivered"] * 7 + ["shipped", "cancelled", "returned"]


def build_database(path, seed: int = 42) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    rng = random.Random(seed)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)

    start = date(2025, 1, 1)
    customers = [
        (i, f"{rng.choice(FIRST)} {rng.choice(LAST)}", rng.choice(CITIES),
         (start + timedelta(days=rng.randint(0, 300))).isoformat())
        for i in range(1, 51)
    ]
    conn.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)
    conn.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?)",
        [(i, n, c, p) for i, (n, c, p) in enumerate(PRODUCTS, start=1)],
    )

    items, item_id = [], 1
    orders = []
    for order_id in range(1, 301):
        order_date = start + timedelta(days=rng.randint(0, 640))
        orders.append((order_id, rng.randint(1, 50), order_date.isoformat(), rng.choice(STATUSES)))
        for product_id in rng.sample(range(1, len(PRODUCTS) + 1), rng.randint(1, 4)):
            items.append((item_id, order_id, product_id, rng.randint(1, 3)))
            item_id += 1
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders)
    conn.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?)", items)

    conn.commit()
    conn.close()
    return path
