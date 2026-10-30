"""Synthetic retail data + database layer (SQLite by default, PostgreSQL via DATABASE_URL)."""
import os
import numpy as np, pandas as pd
from sqlalchemy import create_engine, inspect

DB_URL = os.getenv("DATABASE_URL", "sqlite:///retailtwin.db")  # e.g. postgresql://user:pw@localhost/retailtwin
engine = create_engine(DB_URL)

# id, name, category, price (INR), base daily demand, stock on hand
PRODUCTS = [
    (1, "Fresh Apples", "Produce", 120, 40, 110), (2, "Tomatoes", "Produce", 40, 60, 620),
    (3, "Whole Wheat Bread", "Bakery", 45, 35, 200), (4, "Croissant", "Bakery", 60, 20, 280),
    (5, "Full Cream Milk", "Dairy", 66, 80, 240), (6, "Greek Yogurt", "Dairy", 90, 30, 360),
    (7, "Cola 1L", "Beverages", 55, 50, 420), (8, "Orange Juice", "Beverages", 110, 25, 240),
    (9, "Potato Chips", "Snacks", 30, 70, 420), (10, "Chocolate Bar", "Snacks", 50, 45, 240),
    (11, "Detergent 1kg", "Household", 210, 12, 420), (12, "Dish Soap", "Household", 95, 18, 45),
]

def generate(days=180, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize() - pd.Timedelta(days=1), periods=days)
    rows = []
    for pid, name, cat, price, base, _ in PRODUCTS:
        promo_days = set(rng.choice(days, size=days // 9, replace=False))
        for i, d in enumerate(dates):
            promo = 1 if i in promo_days else 0
            dow = 1.35 if d.dayofweek >= 5 else (0.9 if d.dayofweek in (1, 2) else 1.0)
            mu = base * dow * (1 + 0.002 * i) * (1.6 if promo else 1.0)
            rows.append((d.strftime("%Y-%m-%d"), pid, int(rng.poisson(mu)), promo))
    return pd.DataFrame(rows, columns=["date", "product_id", "units", "promo"])

def init_db():
    if inspect(engine).has_table("sales"):
        return
    pd.DataFrame(PRODUCTS, columns=["id", "name", "category", "price", "base", "stock"]).to_sql("products", engine, index=False)
    generate().to_sql("sales", engine, index=False)

def products():
    return pd.read_sql("select * from products", engine)

def sales():
    df = pd.read_sql("select * from sales", engine)
    df["date"] = pd.to_datetime(df["date"])
    return df
