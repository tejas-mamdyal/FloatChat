import json
import os
import requests
from typing import List, Dict, Any
from pydantic import ValidationError

from models.query_plan import QueryPlan
from services.scientific_query_service import ScientificQueryService
from database.core import get_db_connection

# Initialize the new DuckDB service
duckdb_service = ScientificQueryService()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class QueryPlanner:
    """
    Uses Groq to transform natural language into a structured QueryPlan.
    """
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
    def generate_plan(self, prompt: str) -> QueryPlan:
        system_prompt = (
            "You are a query planner for an Oceanographic ARGO dataset. "
            "Extract intent and structured constraints into JSON. "
            "Intents: 'metadata', 'semantic', 'spatial', 'temporal', 'scientific_aggregation', 'mixed', 'conversational'. "
            "Variables: 'temperature', 'salinity', 'pressure'. "
            "Aggregations: 'avg', 'min', 'max'. "
            "Output strictly valid JSON matching this schema: "
            "{'intent': str, 'variable': str|null, 'aggregation': str|null, 'latitude': float|null, 'longitude': float|null, 'radius_km': float|null, 'start_time': str|null, 'end_time': str|null, 'semantic_query': str|null, 'limit': int}"
        )
        
        try:
            response = requests.post(
                self.api_url,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": "llama3-8b-8192", # Using a fast Groq model for planning
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"}
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(data)
            return QueryPlan(**parsed)
        except Exception as e:
            # Fallback for conversational
            return QueryPlan(intent="conversational", semantic_query=prompt)

def execute_plan(plan: QueryPlan) -> Dict[str, Any]:
    """
    Executes the structured plan securely across PostGIS and DuckDB.
    """
    result = {
        "intent": plan.intent,
        "data": {},
        "sources": []
    }
    
    # Normally we would query PostgreSQL/PostGIS here for candidate file IDs.
    # Since DB is unavailable, we fallback to all known parquet files if needed.
    candidate_files = []
    
    # 1. PostgreSQL Spatial/Temporal Filter (Mocked for safety since Docker is missing locally)
    # Check if DB is available first
    try:
        with get_db_connection() as conn:
            pass
    except Exception as e:
        # DB unavailable, raise safe error
        raise ConnectionError("PostgreSQL/PostGIS metadata database is currently unavailable.")

    if plan.latitude and plan.longitude and plan.radius_km:
        # e.g., query argo_profiles using ST_DWithin
        pass 
        
    # 2. pgvector Semantic Search
    if plan.intent in ['semantic', 'mixed'] and plan.semantic_query:
        # e.g., vector_cosine_ops search
        pass
        
    # 3. DuckDB Scientific Aggregation
    if plan.intent in ['scientific_aggregation', 'mixed']:
        if plan.variable and plan.aggregation:
            # If no candidates from PostGIS, we'd normally fail or scan all. 
            # For safety, if candidate_files is empty, we don't scan all files automatically.
            
            # Example hardcoded candidate for testing DuckDB if no spatial filter was hit:
            candidate_files = ['D20250601_prof_0.parquet'] 
            
            duck_res = duckdb_service.query(candidate_files, plan.variable, plan.aggregation)
            result["data"]["scientific_result"] = duck_res
            result["sources"] = candidate_files
            
    return result
