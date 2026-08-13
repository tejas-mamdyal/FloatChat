import unittest
from pydantic import ValidationError
from models.query_plan import QueryPlan

class TestQueryPlan(unittest.TestCase):
    def test_valid_plan(self):
        plan = QueryPlan(
            intent="scientific_aggregation",
            variable="temperature",
            aggregation="avg",
            latitude=10.0,
            longitude=70.0,
            radius_km=100.0,
            start_time="2025-01-01",
            end_time="2025-01-31"
        )
        self.assertEqual(plan.intent, "scientific_aggregation")
        
    def test_missing_intent(self):
        with self.assertRaises(ValidationError):
            QueryPlan(variable="temperature")
            
    def test_invalid_type(self):
        with self.assertRaises(ValidationError):
            QueryPlan(intent="metadata", latitude="not_a_float")

if __name__ == '__main__':
    unittest.main()
