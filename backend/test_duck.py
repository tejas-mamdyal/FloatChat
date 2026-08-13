import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from services.scientific_query_service import ScientificQueryService

def run():
    svc = ScientificQueryService()
    # Test valid duckdb query
    res = svc.query(["D20250601_prof_0.parquet"], "temp", "avg")
    print("DuckDB test temp avg:", res)
    
    # Test invalid var
    res2 = svc.query(["D20250601_prof_0.parquet"], "fake_var", "avg")
    print("DuckDB test invalid var:", res2)

    # Test invalid op
    res3 = svc.query(["D20250601_prof_0.parquet"], "temp", "drop_table")
    print("DuckDB test invalid op:", res3)

if __name__ == "__main__":
    run()
