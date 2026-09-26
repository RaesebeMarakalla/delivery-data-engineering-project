import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "python" / "business_insights.py"


class BusinessInsightsScriptTests(unittest.TestCase):
    def test_business_insights_script_exists_and_exposes_main(self):
        self.assertTrue(SCRIPT_PATH.exists(), "business_insights.py is missing")

        spec = importlib.util.spec_from_file_location("business_insights", SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertTrue(callable(getattr(module, "main", None)))
        self.assertTrue(callable(getattr(module, "load_processed_data", None)))


if __name__ == "__main__":
    unittest.main()
