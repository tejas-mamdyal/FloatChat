import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.scientific_query_service import ScientificQueryService

class TestDuckDBService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = ScientificQueryService()
        # Find a valid parquet file if it exists locally to run a real test, else mock
        cls.test_file = None
        if os.path.exists(cls.service.parquet_dir):
            files = [f for f in os.listdir(cls.service.parquet_dir) if f.endswith('.parquet')]
            if files:
                cls.test_file = files[0]
                
    def setUp(self):
        if not self.test_file:
            self.skipTest("No local parquet files available for DuckDB testing.")

    def test_avg_temperature(self):
        res = self.service.query([self.test_file], "temp", "avg")
        self.assertNotIn("error", res)
        self.assertIsNotNone(res.get("result"))
        self.assertEqual(res.get("operation"), "avg")

    def test_min_max_count(self):
        for op in ["min", "max", "count"]:
            res = self.service.query([self.test_file], "salinity", op)
            self.assertNotIn("error", res)
            self.assertIsNotNone(res.get("result"))

    def test_invalid_variable(self):
        res = self.service.query([self.test_file], "invalid_var", "avg")
        self.assertIn("error", res)
        self.assertIsNone(res.get("result"))
        
    def test_invalid_operation(self):
        res = self.service.query([self.test_file], "temp", "invalid_op")
        self.assertIn("error", res)
        self.assertIsNone(res.get("result"))
        
    def test_path_traversal_prevention(self):
        # Attempt to access a file outside the directory
        res = self.service.query(["../../../../Windows/System32/config/SAM"], "temp", "avg")
        self.assertIn("error", res)
        self.assertEqual(res["result"], None)

if __name__ == '__main__':
    unittest.main()
