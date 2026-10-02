import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "python" / "etl_pipeline.py"
SPEC = importlib.util.spec_from_file_location("etl_pipeline", SCRIPT_PATH)
etl_pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(etl_pipeline)
GENERATOR_PATH = ROOT / "python" / "generate_sample_data.py"
GENERATOR_SPEC = importlib.util.spec_from_file_location("generate_sample_data", GENERATOR_PATH)
sample_data = importlib.util.module_from_spec(GENERATOR_SPEC)
GENERATOR_SPEC.loader.exec_module(sample_data)


class EtlDataQualityTests(unittest.TestCase):
    def clean_records(self, table_name, records):
        with tempfile.TemporaryDirectory() as temp_dir:
            pd.DataFrame(records).to_csv(Path(temp_dir) / f"{table_name}.csv", index=False)
            return etl_pipeline.clean_table(table_name, Path(temp_dir))

    def test_extract_transform_cleans_all_source_csvs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tables, rejected = etl_pipeline.extract_transform(ROOT / "data" / "raw", Path(temp_dir))

            self.assertEqual(set(tables), set(etl_pipeline.LOAD_ORDER))
            self.assertEqual(sum(map(len, rejected.values())), 0)
            for table in etl_pipeline.LOAD_ORDER:
                self.assertTrue((Path(temp_dir) / f"{table}.csv").exists())

    def test_sample_generator_is_repeatable_and_preserves_relationships(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "raw"
            shutil.copytree(ROOT / "data" / "raw", data_dir)

            counts = sample_data.generate_sample_data(data_dir)
            first_outputs = {
                table: (data_dir / f"{table}.csv").read_bytes()
                for table in etl_pipeline.LOAD_ORDER
            }
            repeated_counts = sample_data.generate_sample_data(data_dir)
            tables, rejected = etl_pipeline.extract_transform(data_dir)

            self.assertEqual(counts, repeated_counts)
            self.assertEqual(counts, {
                "customers": 250,
                "products": 35,
                "orders": 1000,
                "order_items": 2273,
                "drivers": 30,
                "vehicles": 24,
                "deliveries": 965,
            })
            self.assertEqual(
                first_outputs,
                {table: (data_dir / f"{table}.csv").read_bytes() for table in etl_pipeline.LOAD_ORDER},
            )
            self.assertEqual(sum(map(len, rejected.values())), 0)
            line_totals = (
                tables["order_items"]
                .merge(tables["products"][ ["product_id", "price"] ], on="product_id")
                .assign(line_total=lambda frame: frame["quantity"] * frame["price"])
                .groupby("order_id")["line_total"]
                .sum()
                .round(2)
            )
            order_totals = tables["orders"].set_index("order_id")["total_amount"].round(2)
            self.assertEqual(line_totals.to_dict(), order_totals.to_dict())

    def test_clean_table_normalizes_text_and_numeric_values(self):
        cleaned, rejected = self.clean_records("customers", [{
            "customer_id": " 1 ",
            "name": " Ada Lovelace ",
            "email": " ADA@EXAMPLE.COM ",
            "phone": " 555-0100 ",
            "city": " London ",
        }])

        self.assertEqual(cleaned.loc[0, "customer_id"], 1)
        self.assertEqual(cleaned.loc[0, "name"], "Ada Lovelace")
        self.assertEqual(cleaned.loc[0, "email"], "ada@example.com")
        self.assertTrue(rejected.empty)

    def test_clean_table_quarantines_missing_required_values_and_keeps_valid_rows(self):
        records = [{
            "customer_id": "1", "name": "Ada", "email": "ada@example.com", "phone": "", "city": ""
        }, {
            "customer_id": "2", "name": "", "email": "grace@example.com", "phone": "", "city": ""
        }]

        cleaned, rejected = self.clean_records("customers", records)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected.iloc[0]["source_row"], 3)
        self.assertIn("missing required value: name", rejected.iloc[0]["reject_reason"])

    def test_clean_table_quarantines_duplicate_primary_keys(self):
        records = [
            {"customer_id": "1", "name": "Ada", "email": "ada@example.com", "phone": "", "city": ""},
            {"customer_id": "1", "name": "Grace", "email": "grace@example.com", "phone": "", "city": ""},
            {"customer_id": "2", "name": "Linus", "email": "linus@example.com", "phone": "", "city": ""},
        ]

        cleaned, rejected = self.clean_records("customers", records)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(len(rejected), 2)
        self.assertTrue(rejected["reject_reason"].str.contains("duplicate primary key").all())

    def test_clean_table_quarantines_invalid_dates_and_nonpositive_quantities(self):
        orders = [{
            "order_id": "1", "customer_id": "2", "order_date": "not-a-date",
            "status": "pending", "total_amount": "10.00",
        }]
        items = [{
            "order_item_id": "1", "order_id": "2", "product_id": "3", "quantity": "0"
        }]

        _, rejected_orders = self.clean_records("orders", orders)
        _, rejected_items = self.clean_records("order_items", items)

        self.assertIn("invalid date: order_date", rejected_orders.loc[0, "reject_reason"])
        self.assertIn("quantity must be positive", rejected_items.loc[0, "reject_reason"])

    def test_extract_transform_writes_rejected_rows_and_keeps_valid_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "raw"
            shutil.copytree(ROOT / "data" / "raw", source_dir)
            customers_path = source_dir / "customers.csv"
            customers = pd.read_csv(customers_path, dtype=str, keep_default_na=False)
            rejected_customer = pd.DataFrame([{
                "customer_id": "999", "name": "", "email": "invalid@example.com", "phone": "", "city": ""
            }])
            pd.concat([customers, rejected_customer], ignore_index=True).to_csv(customers_path, index=False)

            processed_dir = Path(temp_dir) / "processed"
            rejected_dir = Path(temp_dir) / "rejected"
            tables, rejected = etl_pipeline.extract_transform(source_dir, processed_dir, rejected_dir)

            self.assertEqual(len(rejected["customers"]), 1)
            self.assertIn("missing required value: name", rejected["customers"].iloc[0]["reject_reason"])
            self.assertTrue((processed_dir / "customers.csv").exists())
            saved_rejections = pd.read_csv(rejected_dir / "customers.csv")
            self.assertEqual(len(saved_rejections), 1)
            self.assertNotIn(999, tables["customers"]["customer_id"].tolist())

    def test_validate_relationships_rejects_unknown_foreign_keys(self):
        tables = {
            "customers": pd.DataFrame({"customer_id": [1]}),
            "products": pd.DataFrame({"product_id": [3]}),
            "orders": pd.DataFrame({"order_id": [2], "customer_id": [1]}),
            "drivers": pd.DataFrame({"driver_id": [4]}),
            "vehicles": pd.DataFrame({"vehicle_id": [5]}),
            "order_items": pd.DataFrame({
                "order_item_id": [6], "order_id": [99], "product_id": [3], "quantity": [1]
            }),
            "deliveries": pd.DataFrame({
                "delivery_id": [7], "order_id": [2], "driver_id": [4], "vehicle_id": [5],
                "delivery_date": [None], "status": ["Delivered"],
            }),
        }
        for frame in tables.values():
            frame["__source_row"] = range(2, len(frame) + 2)

        rejected = etl_pipeline.validate_relationships(tables)

        self.assertIn("order_items", rejected)
        self.assertIn("unknown foreign key: order_id=99", rejected["order_items"].iloc[0]["reject_reason"])
        self.assertTrue(tables["order_items"].empty)

if __name__ == "__main__":
    unittest.main()