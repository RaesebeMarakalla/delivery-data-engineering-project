
"""Clean local CSV source data, validate it, and load MySQL."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "data" / "raw"
DEFAULT_PROCESSED_DIR = ROOT / "data" / "processed"
DEFAULT_REJECTED_DIR = ROOT / "data" / "rejected"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("delivery_etl")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(LOG_DIR / "etl_pipeline.log", mode="a")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

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


def clean_table(table_name: str, source_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return valid rows and quarantined rows with their source row and rejection reasons."""
    config = TABLE_CONFIG[table_name]
    path = source_dir / f"{table_name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing source file: {path}")

    logger.info("Cleaning table %s from %s", table_name, path)
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    frame.columns = [column.strip().lower() for column in frame.columns]
    missing_columns = set(config["columns"]) - set(frame.columns)
    if missing_columns:
        raise ValueError(f"{path.name} is missing columns: {sorted(missing_columns)}")

    frame = frame[config["columns"]].copy()
    original = frame.copy()
    reasons = pd.Series("", index=frame.index, dtype="string")

    def reject(mask: pd.Series, reason: str) -> None:
        for row_index in frame.index[mask]:
            current = reasons.at[row_index]
            reasons.at[row_index] = f"{current}; {reason}" if current else reason

    for column in frame.columns:
        frame[column] = frame[column].astype("string").str.strip()
        frame[column] = frame[column].replace({"": pd.NA, "nan": pd.NA, "none": pd.NA})

    for column in config["numeric_columns"]:
        converted = pd.to_numeric(frame[column], errors="coerce")
        invalid = frame[column].notna() & converted.isna()
        reject(invalid, f"invalid numeric value: {column}")
        frame[column] = converted
    for column in config["date_columns"]:
        converted = pd.to_datetime(frame[column], errors="coerce")
        invalid = frame[column].notna() & converted.isna()
        reject(invalid, f"invalid date: {column}")
        frame[column] = converted.dt.date

    if "email" in frame:
        frame["email"] = frame["email"].str.lower()
    if "status" in frame:
        frame["status"] = frame["status"].str.title()
    if "registration_number" in frame:
        frame["registration_number"] = frame["registration_number"].str.upper()

    for column in config["required"]:
        reject(frame[column].isna(), f"missing required value: {column}")
    primary_key = config["primary_key"]
    duplicate_keys = frame[primary_key].notna() & frame[primary_key].duplicated(keep=False)
    reject(duplicate_keys, f"duplicate primary key: {primary_key}")
    if "quantity" in frame:
        reject(frame["quantity"].notna() & (frame["quantity"] <= 0), "quantity must be positive")
    if "price" in frame:
        reject(frame["price"].notna() & (frame["price"] < 0), "price must not be negative")

    rejected_mask = reasons.ne("")
    rejected = original.loc[rejected_mask].copy()
    rejected.insert(0, "source_row", rejected.index + 2)
    rejected["reject_reason"] = reasons.loc[rejected_mask]

    valid = frame.loc[~rejected_mask].copy()
    valid["__source_row"] = valid.index + 2
    logger.info(
        "Table %s: %d valid rows, %d rejected rows",
        table_name,
        len(valid),
        len(rejected),
    )
    return valid, rejected


def validate_relationships(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Remove rows with invalid foreign keys and return them with rejection reasons."""
    checks = [
        ("orders", "customer_id", "customers", "customer_id"),
        ("order_items", "order_id", "orders", "order_id"),
        ("order_items", "product_id", "products", "product_id"),
        ("deliveries", "order_id", "orders", "order_id"),
        ("deliveries", "driver_id", "drivers", "driver_id"),
        ("deliveries", "vehicle_id", "vehicles", "vehicle_id"),
    ]
    rejected_rows: dict[str, dict[int, list[str]]] = {table: {} for table in tables}
    for child_table, child_column, parent_table, parent_column in checks:
        parent = tables[parent_table]
        rejected_parent_indexes = set(rejected_rows[parent_table])
        parent_ids = set(parent.loc[~parent.index.isin(rejected_parent_indexes), parent_column].dropna())
        child = tables[child_table]
        invalid = child[child_column].notna() & ~child[child_column].isin(parent_ids)
        for row_index in child.index[invalid]:
            value = child.at[row_index, child_column]
            rejected_rows[child_table].setdefault(row_index, []).append(
                f"unknown foreign key: {child_column}={value} (no matching {parent_table}.{parent_column})"
            )

    rejected: dict[str, pd.DataFrame] = {}
    total_relationship_rejections = 0
    for table, rows in rejected_rows.items():
        if rows:
            invalid_indexes = list(rows)
            invalid_records = tables[table].loc[invalid_indexes].copy()
            invalid_records.insert(0, "source_row", invalid_records.pop("__source_row"))
            invalid_records["reject_reason"] = ["; ".join(rows[index]) for index in invalid_indexes]
            rejected[table] = invalid_records[[
                "source_row", *TABLE_CONFIG[table]["columns"], "reject_reason"
            ]]
            tables[table] = tables[table].drop(index=invalid_indexes)
            total_relationship_rejections += len(invalid_indexes)
            logger.warning("Rejected %d rows from %s due to invalid relationships", len(invalid_indexes), table)

        tables[table] = tables[table].drop(columns="__source_row").reset_index(drop=True)
    logger.info("Relationship validation rejected %d rows across tables", total_relationship_rejections)
    return rejected


def extract_transform(
    source_dir: Path,
    processed_dir: Path | None = None,
    rejected_dir: Path | None = None,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    """Extract, clean, and validate CSVs, returning accepted and rejected records."""
    tables: dict[str, pd.DataFrame] = {}
    rejected: dict[str, pd.DataFrame] = {}
    logger.info("Starting extract-transform for source directory %s", source_dir)
    for table in LOAD_ORDER:
        tables[table], rejected[table] = clean_table(table, source_dir)

    relationship_rejections = validate_relationships(tables)
    for table, records in relationship_rejections.items():
        rejected[table] = pd.concat([rejected[table], records], ignore_index=True)

    if processed_dir:
        processed_dir.mkdir(parents=True, exist_ok=True)
        for table, frame in tables.items():
            frame.to_csv(processed_dir / f"{table}.csv", index=False)
            logger.info("Wrote %d accepted rows for %s", len(frame), table)
    if rejected_dir:
        rejected_dir.mkdir(parents=True, exist_ok=True)
        for table in LOAD_ORDER:
            columns = ["source_row", *TABLE_CONFIG[table]["columns"], "reject_reason"]
            rejected[table].reindex(columns=columns).to_csv(rejected_dir / f"{table}.csv", index=False)
            logger.info("Wrote %d rejected rows for %s", len(rejected[table]), table)

    total_accepted = sum(len(frame) for frame in tables.values())
    total_rejected = sum(len(frame) for frame in rejected.values())
    logger.info("ETL summary: %d accepted rows, %d rejected rows", total_accepted, total_rejected)
    return tables, rejected


def load_to_mysql(tables: dict[str, pd.DataFrame], connection_config: dict[str, Any]) -> None:
    """Upsert transformed rows in foreign-key order, making reruns idempotent."""
    import mysql.connector

    logger.info("Connecting to MySQL for data load")
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
            logger.info("Loaded %d rows into %s", len(rows), table)
            print(f"Loaded {len(rows)} rows into {table}")
        connection.commit()
        logger.info("MySQL load completed successfully")
    except Exception:
        connection.rollback()
        logger.exception("MySQL load failed")
        raise
    finally:
        connection.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR)
    parser.add_argument(
        "--rejected-dir",
        type=Path,
        default=DEFAULT_REJECTED_DIR,
        help="Directory for rejected-row CSV files",
    )
    parser.add_argument("--dry-run", action="store_true", help="Clean and validate without loading MySQL")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logger.info("Starting ETL run with source=%s, processed=%s, rejected=%s", args.source_dir, args.processed_dir, args.rejected_dir)
    tables, rejected = extract_transform(args.source_dir, args.processed_dir, args.rejected_dir)
    accepted_count = sum(len(frame) for frame in tables.values())
    rejected_count = sum(len(frame) for frame in rejected.values())
    print(f"Accepted {accepted_count} rows across {len(tables)} tables")
    print(f"Rejected {rejected_count} rows; details written to {args.rejected_dir}")
    logger.info("ETL run complete: accepted=%d rejected=%d", accepted_count, rejected_count)
    if args.dry_run:
        print("Dry run complete; no database changes made")
        logger.info("Dry run complete; no database changes made")
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