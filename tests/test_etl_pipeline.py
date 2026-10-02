import importlib.util
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "python" / "etl_pipeline.py"
SPEC = importlib.util.spec_from_file_location("etl_pipeline", SCRIPT_PATH)
etl_pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(etl_pipeline)


class EtlDataQualityTests(unittest.TestCase):
    def clean_records(self, table_name, records):
        with tempfile.TemporaryDirectory() as temp_dir:
            pd.DataFrame(records).to_csv(Path(temp_dir) / f"{table_name}.csv", index=False)
            return etl_pipeline.clean_table(table_name, Path(temp_dir))

    def test_extract_transform_cleans_all_source_csvs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tables = etl_pipeline.extract_transform(ROOT / "data" / "raw", Path(temp_dir))

            self.assertEqual(set(tables), set(etl_pipeline.LOAD_ORDER))
            for table in etl_pipeline.LOAD_ORDER:
                self.assertTrue((Path(temp_dir) / f"{table}.csv").exists())

    def test_clean_table_normalizes_text_and_numeric_values(self):
        cleaned = self.clean_records("customers", [{
            "customer_id": " 1 ",
            "name": " Ada Lovelace ",
            "email": " ADA@EXAMPLE.COM ",
            "phone": " 555-0100 ",
            "city": " London ",
        }])

        self.assertEqual(cleaned.loc[0, "customer_id"], 1)
        self.assertEqual(cleaned.loc[0, "name"], "Ada Lovelace")
        self.assertEqual(cleaned.loc[0, "email"], "ada@example.com")

    def test_clean_table_rejects_missing_required_values(self):
        records = [{
            "customer_id": "1", "name": "", "email": "ada@example.com", "phone": "", "city": ""
        }]

        with self.assertRaisesRegex(ValueError, "missing required values"):
            self.clean_records("customers", records)

    def test_clean_table_rejects_duplicate_primary_keys(self):
        records = [
            {"customer_id": "1", "name": "Ada", "email": "ada@example.com", "phone": "", "city": ""},
            {"customer_id": "1", "name": "Grace", "email": "grace@example.com", "phone": "", "city": ""},
        ]

        with self.assertRaisesRegex(ValueError, "duplicate customer_id"):
            self.clean_records("customers", records)

    def test_clean_table_rejects_invalid_dates_and_nonpositive_quantities(self):
        orders = [{
            "order_id": "1", "customer_id": "2", "order_date": "not-a-date",
            "status": "pending", "total_amount": "10.00",
        }]
        items = [{
            "order_item_id": "1", "order_id": "2", "product_id": "3", "quantity": "0"
        }]

        with self.assertRaisesRegex(ValueError, "invalid dates"):
            self.clean_records("orders", orders)
        with self.assertRaisesRegex(ValueError, "non-positive quantities"):
            self.clean_records("order_items", items)

    def test_validate_relationships_rejects_unknown_foreign_keys(self):
        tables = {
            "customers": pd.DataFrame({"customer_id": [1]}),
            "products": pd.DataFrame({"product_id": [3]}),
            "orders": pd.DataFrame({"order_id": [2], "customer_id": [1]}),
            "drivers": pd.DataFrame({"driver_id": [4]}),
            "vehicles": pd.DataFrame({"vehicle_id": [5]}),
            "order_items": pd.DataFrame({"order_id": [99], "product_id": [3]}),
            "deliveries": pd.DataFrame({"order_id": [2], "driver_id": [4], "vehicle_id": [5]}),
        }

        with self.assertRaisesRegex(ValueError, "order_items.order_id has unknown values"):
            etl_pipeline.validate_relationships(tables)

if __name__ == "__main__":
    unittest.main()