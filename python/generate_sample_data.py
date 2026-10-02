"""Expand the delivery sample CSVs with deterministic, linked demo records."""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data" / "raw"
SEED_ROW_COUNTS = {
    "customers": 10,
    "products": 10,
    "orders": 10,
    "order_items": 10,
    "drivers": 5,
    "vehicles": 5,
    "deliveries": 10,
}
TARGET_COUNTS = {
    "customers": 250,
    "products": 35,
    "orders": 1000,
    "drivers": 30,
    "vehicles": 24,
}
AS_OF_DATE = date(2026, 10, 1)

FIRST_NAMES = [
    "Aisha", "Ayanda", "Bongani", "Brian", "David", "Dineo", "James", "Karabo",
    "Kabelo", "Keegan", "Lerato", "Lindiwe", "Lungile", "Mandla", "Michael", "Mpho",
    "Naledi", "Nandi", "Nomsa", "Peter", "Precious", "Refilwe", "Sibusiso", "Sipho",
    "Thabo", "Thandi", "Tshepo", "Zanele", "Zinhle", "Amara", "Daniel", "Fatima",
    "Khaya", "Leila", "Musa", "Neo", "Rethabile", "Samkelo", "Tumi", "Yusuf",
]
LAST_NAMES = [
    "Adams", "Baloyi", "Botha", "Cele", "Dlamini", "Du Preez", "Jacobs", "Khan",
    "Khumalo", "Maseko", "Mokoena", "Molefe", "Mthembu", "Naidoo", "Ndlovu", "Nkosi",
    "Pillay", "Radebe", "Sithole", "Smith", "Van Der Merwe", "Williams", "Zungu", "Zulu",
    "Abrahams", "Benjamin", "Coetzee", "Davids", "Gumede", "Hlongwane", "Mahlangu", "Mahlase",
    "Mkhize", "Modise", "Msimang", "Ntuli", "Petersen", "Phiri", "Ramaphosa", "Swanepoel",
]
CITIES = [
    "Johannesburg", "Pretoria", "Soweto", "Sandton", "Midrand", "Randburg", "Roodepoort",
    "Centurion", "Benoni", "Germiston", "Kempton Park", "Boksburg", "Alberton", "Fourways",
    "Durban", "Cape Town", "Bloemfontein", "Polokwane", "Nelspruit", "Vereeniging",
]
MOBILE_PREFIXES = ["60", "61", "63", "64", "65", "66", "67", "71", "72", "73", "74", "76", "78", "79", "82", "83"]
NEW_PRODUCTS = [
    ("USB-C Docking Station", "Electronics", "1899.00"),
    ("Wireless Headphones", "Electronics", "1299.00"),
    ("1080p Webcam", "Electronics", "899.00"),
    ("Portable SSD 1TB", "Electronics", "1799.00"),
    ("Bluetooth Speaker", "Electronics", "699.00"),
    ("Android Tablet", "Electronics", "5499.00"),
    ("Smartphone", "Electronics", "8999.00"),
    ("Laptop Stand", "Electronics", "599.00"),
    ("Surge Protector", "Electronics", "399.00"),
    ("Laser Printer Toner", "Electronics", "1199.00"),
    ("Standing Desk", "Furniture", "6499.00"),
    ("Ergonomic Chair", "Furniture", "4299.00"),
    ("Filing Cabinet", "Furniture", "1899.00"),
    ("Desk Lamp", "Furniture", "549.00"),
    ("Bookshelf", "Furniture", "2499.00"),
    ("A4 Copy Paper 5 Reams", "Stationery", "399.00"),
    ("Ballpoint Pens 12 Pack", "Stationery", "89.00"),
    ("Whiteboard Markers 4 Pack", "Stationery", "119.00"),
    ("Lever Arch Files 10 Pack", "Stationery", "249.00"),
    ("Sticky Notes Assorted", "Stationery", "69.00"),
    ("Laptop Backpack", "Accessories", "1099.00"),
    ("Wireless Presenter", "Accessories", "449.00"),
    ("Reusable Coffee Cup", "Accessories", "179.00"),
    ("HDMI Cable 2m", "Accessories", "149.00"),
    ("Desk Organizer", "Accessories", "329.00"),
]


def read_seed(data_dir: Path, table: str) -> pd.DataFrame:
    path = data_dir / f"{table}.csv"
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    seed_count = SEED_ROW_COUNTS[table]
    if len(frame) < seed_count:
        raise ValueError(f"{path.name} must contain its original {seed_count} seed rows")
    return frame.iloc[:seed_count].copy()


def next_id(frame: pd.DataFrame, id_column: str) -> int:
    return int(pd.to_numeric(frame[id_column]).max()) + 1


def make_name(identifier: int) -> str:
    index = identifier - 1
    first = FIRST_NAMES[(index // len(LAST_NAMES)) % len(FIRST_NAMES)]
    last = LAST_NAMES[index % len(LAST_NAMES)]
    return f"{first} {last}"


def make_phone(identifier: int, rng: random.Random) -> str:
    prefix = rng.choice(MOBILE_PREFIXES)
    subscriber = (identifier * 7919) % 10_000_000
    return f"0{prefix}{subscriber:07d}"


def make_registration(identifier: int) -> str:
    letters = "".join(chr(65 + (identifier // (26 ** place)) % 26) for place in (2, 1, 0))
    number = 100 + (identifier * 37) % 900
    return f"{letters} {number:03d} GP"


def choose_order_status(order_date: date, rng: random.Random) -> str:
    age_days = (AS_OF_DATE - order_date).days
    if age_days > 30:
        choices, weights = ["Delivered", "In Transit", "Processing", "Cancelled"], [0.94, 0.02, 0.01, 0.03]
    elif age_days > 7:
        choices, weights = ["Delivered", "In Transit", "Processing", "Cancelled"], [0.82, 0.10, 0.04, 0.04]
    else:
        choices, weights = ["Delivered", "In Transit", "Processing", "Cancelled"], [0.28, 0.24, 0.43, 0.05]
    return rng.choices(choices, weights=weights, k=1)[0]


def generate_sample_data(data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, int]:
    """Preserve the original seed rows and regenerate the larger sample consistently."""
    rng = random.Random(20261001)
    data_dir.mkdir(parents=True, exist_ok=True)
    seeds = {table: read_seed(data_dir, table) for table in SEED_ROW_COUNTS}

    customers = seeds["customers"]
    new_customers = []
    for customer_id in range(next_id(customers, "customer_id"), TARGET_COUNTS["customers"] + 1):
        name = make_name(customer_id)
        email_name = name.lower().replace(" ", ".").replace("'", "")
        new_customers.append([
            str(customer_id), name, f"{email_name}.{customer_id}@example.com",
            make_phone(customer_id, rng), rng.choice(CITIES),
        ])
    customers = pd.concat([customers, pd.DataFrame(new_customers, columns=customers.columns)], ignore_index=True)

    products = seeds["products"]
    new_products = []
    for product_id, (name, category, price) in enumerate(NEW_PRODUCTS, start=next_id(products, "product_id")):
        new_products.append([str(product_id), name, category, price])
    products = pd.concat([products, pd.DataFrame(new_products, columns=products.columns)], ignore_index=True)

    drivers = seeds["drivers"]
    new_drivers = []
    for driver_id in range(next_id(drivers, "driver_id"), TARGET_COUNTS["drivers"] + 1):
        new_drivers.append([
            str(driver_id), make_name(driver_id + 250), make_phone(driver_id + 250, rng)
        ])
    drivers = pd.concat([drivers, pd.DataFrame(new_drivers, columns=drivers.columns)], ignore_index=True)

    vehicles = seeds["vehicles"]
    vehicle_types = ["Van", "Truck", "Motorcycle", "Panel Van", "Refrigerated Truck"]
    new_vehicles = []
    for vehicle_id in range(next_id(vehicles, "vehicle_id"), TARGET_COUNTS["vehicles"] + 1):
        new_vehicles.append([
            str(vehicle_id), make_registration(vehicle_id), rng.choice(vehicle_types)
        ])
    vehicles = pd.concat([vehicles, pd.DataFrame(new_vehicles, columns=vehicles.columns)], ignore_index=True)

    prices = {
        int(row.product_id): Decimal(row.price)
        for row in products.itertuples(index=False)
    }
    customer_ids = [int(value) for value in customers["customer_id"]]
    product_ids = list(prices)
    driver_ids = [int(value) for value in drivers["driver_id"]]
    vehicle_ids = [int(value) for value in vehicles["vehicle_id"]]

    orders = seeds["orders"]
    order_items = seeds["order_items"]
    deliveries = seeds["deliveries"]
    new_orders = []
    new_order_items = []
    new_deliveries = []
    order_id = next_id(orders, "order_id")
    order_item_id = next_id(order_items, "order_item_id")
    delivery_id = next_id(deliveries, "delivery_id")
    period_days = (AS_OF_DATE - date(2025, 10, 1)).days

    for current_order_id in range(order_id, TARGET_COUNTS["orders"] + 1):
        order_date = AS_OF_DATE - timedelta(days=rng.randint(0, period_days))
        status = choose_order_status(order_date, rng)
        item_count = rng.choices([1, 2, 3, 4], weights=[0.20, 0.43, 0.27, 0.10], k=1)[0]
        selected_products = rng.sample(product_ids, item_count)
        total_amount = Decimal("0.00")

        for product_id in selected_products:
            quantity = rng.choices([1, 2, 3], weights=[0.78, 0.19, 0.03], k=1)[0]
            total_amount += prices[product_id] * quantity
            new_order_items.append([
                str(order_item_id), str(current_order_id), str(product_id), str(quantity)
            ])
            order_item_id += 1

        new_orders.append([
            str(current_order_id), str(rng.choice(customer_ids)), order_date.isoformat(),
            status, f"{total_amount:.2f}",
        ])

        if status != "Cancelled":
            if status == "Processing":
                delivery_date = ""
            else:
                transit_days = rng.randint(1, 4)
                delivery_date = min(order_date + timedelta(days=transit_days), AS_OF_DATE).isoformat()
            new_deliveries.append([
                str(delivery_id), str(current_order_id), str(rng.choice(driver_ids)),
                str(rng.choice(vehicle_ids)), delivery_date, status,
            ])
            delivery_id += 1

    orders = pd.concat([orders, pd.DataFrame(new_orders, columns=orders.columns)], ignore_index=True)
    order_items = pd.concat(
        [order_items, pd.DataFrame(new_order_items, columns=order_items.columns)], ignore_index=True
    )
    deliveries = pd.concat(
        [deliveries, pd.DataFrame(new_deliveries, columns=deliveries.columns)], ignore_index=True
    )

    tables = {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items,
        "drivers": drivers,
        "vehicles": vehicles,
        "deliveries": deliveries,
    }
    for table, frame in tables.items():
        frame.to_csv(data_dir / f"{table}.csv", index=False)
    return {table: len(frame) for table, frame in tables.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()
    counts = generate_sample_data(args.data_dir)
    print("Generated sample data: " + ", ".join(f"{table}={count}" for table, count in counts.items()))


if __name__ == "__main__":
    main()