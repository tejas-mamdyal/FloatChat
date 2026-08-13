import unittest
from datetime import datetime, timedelta
import os
import sys

# Ensure backend package is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.backfill_argo_metadata import julian_to_datetime

class TestBackfill(unittest.TestCase):
    def test_julian_to_datetime_valid(self):
        # 1950-01-01 + 10 days = 1950-01-11
        dt = julian_to_datetime(10.0)
        self.assertEqual(dt.year, 1950)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 11)

    def test_julian_to_datetime_invalid(self):
        self.assertIsNone(julian_to_datetime(None))
        self.assertIsNone(julian_to_datetime("invalid"))
        
    def test_coordinate_validation_logic(self):
        # This tests the logic for dropping invalid profiles.
        # Since the actual backfill is in a large function, we simulate the bounds check here
        def is_valid_coord(lat, lon):
            if lat is None or lon is None: return False
            if lat < -90 or lat > 90: return False
            if lon < -180 or lon > 180: return False
            return True
            
        self.assertTrue(is_valid_coord(10.0, 70.0))
        self.assertFalse(is_valid_coord(-91.0, 70.0)) # Invalid lat
        self.assertFalse(is_valid_coord(10.0, 181.0)) # Invalid lon
        self.assertFalse(is_valid_coord(None, 70.0))   # Null lat

if __name__ == '__main__':
    unittest.main()
