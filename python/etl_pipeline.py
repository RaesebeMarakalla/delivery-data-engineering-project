
"""Clean CSV source data and load it into the delivery MySQL database."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "data" / "raw"
DEFAULT_PROCESSED_DIR = ROOT / "data" / "processed"

TABLE_CONFIG: dict[str, dict[str, Any]] = {
    "customers": {
        "columns": ["customer_id", "name", "email", "phone", "city"],
        "primary_key": "customer_id",
        "required": ["customer_id", "name", "email"],
        "date_columns": [],
        "numeric_columns": ["customer_id"],
    },
    "products": {
        "columns": ["product_id", "product_name", "category", "price"],
        "primary_key": "product_id",
        "required": ["product_id", "product_name", "price"],
        "date_columns": [],
        "numeric_columns": ["product_id", "price"],
    },
    "orders": {
        "columns": ["order_id", "customer_id", "order_date", "status", "total_amount"],
        "primary_key": "order_id",
        "required": ["order_id", "customer_id", "order_date", "status", "total_amount"],
        "date_columns": ["order_date"],
        "numeric_columns": ["order_id", "customer_id", "total_amount"],
    },
    "drivers": {
        "columns": ["driver_id", "name", "phone"],
        "primary_key": "driver_id",
        "required": ["driver_id", "name", "phone"],
        "date_columns": [],
        "numeric_columns": ["driver_id"],
    },
    "vehicles": {
        "columns": ["vehicle_id", "registration_number", "vehicle_type"],
        "primary_key": "vehicle_id",
        "required": ["vehicle_id", "registration_number", "vehicle_type"],
        "date_columns": [],
        "numeric_columns": ["vehicle_id"],
    },
    "order_items": {
        "columns": ["order_item_id", "order_id", "product_id", "quantity"],
        "primary_key": "order_item_id",
        "required": ["order_item_id", "order_id", "product_id", "quantity"],
        "date_columns": [],
        "numeric_columns": ["order_item_id", "order_id", "product_id", "quantity"],
    },
    "deliveries": {
        "columns": ["delivery_id", "order_id", "driver_id", "vehicle_id", "delivery_date", "status"],
        "primary_key": "delivery_id",
        "required": ["delivery_id", "order_id", "driver_id", "vehicle_id", "status"],
        "date_columns": ["delivery_date"],
        "numeric_columns": ["delivery_id", "order_id", "driver_id", "vehicle_id"],
    },
}

LOAD_ORDER = ["customers", "products", "orders", "drivers", "vehicles", "order_items", "deliveries"]


def clean_table(table_name: str, source_dir: Path) -> pd.DataFrame:
    """Read and standardize one source CSV according to its target schema."""
    config = TABLE_CONFIG[table_name]
    path = source_dir / f"{table_name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing source file: {path}")

    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    frame.columns = [column.strip().lower() for column in frame.columns]
    missing_columns = set(config["columns"]) - set(frame.columns)
    if missing_columns:
        raise ValueError(f"{path.name} is missing columns: {sorted(missing_columns)}")

    frame = frame[config["columns"]].copy()
    for column in frame.columns:
        frame[column] = frame[column].astype("string").str.strip()
        frame[column] = frame[column].replace({"": pd.NA, "nan": pd.NA, "none": pd.NA})

    for column in config["numeric_columns"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in config["date_columns"]:
        frame[column] = pd.to_datetime(frame[column], errors="coerce").dt.date

    if "email" in frame:
        frame["email"] = frame["email"].str.lower()
    if "status" in frame:
        frame["status"] = frame["status"].str.title()
    if "registration_number" in frame:
        frame["registration_number"] = frame["registration_number"].str.upper()

    invalid_required = frame[config["required"]].isna().any(axis=1)
    if invalid_required.any():
        rows = (frame.index[invalid_required] + 2).tolist()
        raise ValueError(f"{path.name} has missing required values on CSV rows: {rows}")
    if frame.duplicated().any():
        raise ValueError(f"{path.name} contains duplicate rows")
    if "quantity" in frame and (frame["quantity"] <= 0).any():
        raise ValueError(f"{path.name} contains non-positive quantities")
    if "price" in frame and (frame["price"] < 0).any():
        raise ValueError(f"{path.name} contains negative prices")

    return frame


def validate_relationships(tables: dict[str, pd.DataFrame]) -> None:
    """Check foreign keys before opening a database connection."""
    checks = [
        ("orders", "customer_id", "customers", "customer_id"),
        ("order_items", "order_id", "orders", "order_id"),
        ("order_items", "product_id", "products", "product_id"),
        ("deliveries", "order_id", "orders", "order_id"),
        ("deliveries", "driver_id", "drivers", "driver_id"),
        ("deliveries", "vehicle_id", "vehicles", "vehicle_id"),
    ]
    for child_table, child_column, parent_table, parent_column in checks:
        parent_ids = set(tables[parent_table][parent_column].dropna())
        invalid = sorted(set(tables[child_table][child_column].dropna()) - parent_ids)
        if invalid:
            raise ValueError(f"{child_table}.{child_column} has unknown values: {invalid}")


def extract_transform(source_dir: Path, processed_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Extract all CSVs, transform them, validate relationships, and optionally persist them."""
    tables = {table: clean_table(table, source_dir) for table in LOAD_ORDER}
    validate_relationships(tables)
    if processed_dir:
        processed_dir.mkdir(parents=True, exist_ok=True)
        for table, frame in tables.items():
            frame.to_csv(processed_dir / f"{table}.csv", index=False)
    return tables


def load_to_mysql(tables: dict[str, pd.DataFrame], connection_config: dict[str, Any]) -> None:
    """Upsert transformed rows in foreign-key order, making reruns idempotent."""
    import mysql.connector

    connection = mysql.connector.connect(**connection_config)
    try:
        cursor = connection.cursor()
        for table in LOAD_ORDER:
            columns = TABLE_CONFIG[table]["columns"]
            quoted_columns = ", ".join(f"`{column}`" for column in columns)
            placeholders = ", ".join(["%s"] * len(columns))
            primary_key = TABLE_CONFIG[table]["primary_key"]
            update_columns = [column for column in columns if column != primary_key]
            update_clause = ", ".join(f"`{column}` = VALUES(`{column}`)" for column in update_columns)
            query = (
                f"INSERT INTO `{table}` ({quoted_columns}) VALUES ({placeholders}) "
                f"ON DUPLICATE KEY UPDATE {update_clause}"
            )
            rows = [
                tuple(
                    None if pd.isna(value) else (value.item() if hasattr(value, "item") else value)
                    for value in row
                )
                for row in tables[table].itertuples(index=False, name=None)
            ]
            cursor.executemany(query, rows)
            print(f"Loaded {len(rows)} rows into {table}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Clean and validate without loading MySQL")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tables = extract_transform(args.source_dir, args.processed_dir)
    print(f"Validated {sum(len(frame) for frame in tables.values())} rows across {len(tables)} tables")
    if args.dry_run:
        print("Dry run complete; no database changes made")
        return

    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "delivery_db"),
    }
    load_to_mysql(tables, config)


if __name__ == "__main__":
    main()