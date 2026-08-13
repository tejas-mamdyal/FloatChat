import os
import logging
from typing import List, Dict, Any, Optional
import yaml
import pandas as pd

try:
    import duckdb
except ImportError:
    duckdb = None

logger = logging.getLogger(__name__)

class ScientificQueryService:
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "config.yaml"), "r") as f:
            self.config = yaml.safe_load(f)
        self.parquet_dir = os.path.join(self.config["data"]["download_dir"], "parquet")
        
        # Map user variables to safe columns
        self.VAR_MAP = {
            "temp": "temp",
            "temperature": "temp",
            "psal": "psal",
            "salinity": "psal",
            "pres": "pres",
            "pressure": "pres"
        }
        
        # Allowed SQL aggregations
        self.OP_MAP = {
            "avg": "AVG",
            "min": "MIN",
            "max": "MAX",
            "count": "COUNT",
            "stddev": "STDDEV_SAMP"
        }

    def _validate_paths(self, file_names: List[str]) -> List[str]:
        valid_paths = []
        for name in file_names:
            # Prevent path traversal
            safe_name = os.path.basename(name)
            if not safe_name.endswith('.parquet'):
                safe_name += '.parquet'
                
            path = os.path.join(self.parquet_dir, safe_name)
            if os.path.exists(path):
                # Ensure it's inside the configured directory
                if os.path.abspath(path).startswith(os.path.abspath(self.parquet_dir)):
                    valid_paths.append(path)
        return valid_paths

    def query(
        self,
        file_names: List[str],
        variable: str,
        operation: str
    ) -> Dict[str, Any]:
        """
        Executes a controlled DuckDB aggregation over Parquet files.
        """
        if duckdb is None:
            return {"error": "DuckDB is not installed.", "result": None}

        valid_paths = self._validate_paths(file_names)
        if not valid_paths:
            return {"error": "No valid Parquet files provided or found.", "result": None}

        internal_var = self.VAR_MAP.get(variable.lower())
        if not internal_var:
            return {"error": f"Unsupported variable: {variable}", "result": None}

        sql_op = self.OP_MAP.get(operation.lower())
        if not sql_op:
            return {"error": f"Unsupported operation: {operation}", "result": None}

        # Build paths string for DuckDB
        paths_str = ", ".join([f"'{p}'" for p in valid_paths])
        
        # Construct exact safe SQL without user input interpolated directly as identifiers
        query_sql = f"SELECT {sql_op}({internal_var}) as result FROM read_parquet([{paths_str}]) WHERE {internal_var} IS NOT NULL"
        
        try:
            con = duckdb.connect(database=':memory:')
            df = con.execute(query_sql).df()
            val = df['result'][0]
            
            if pd.isna(val):
                val = None
            else:
                val = float(val)
                
            return {
                "result": val,
                "operation": operation,
                "variable": variable,
                "files_scanned": len(valid_paths)
            }
        except Exception as e:
            logger.error(f"DuckDB Query failed: {e}")
            return {"error": str(e), "result": None}
