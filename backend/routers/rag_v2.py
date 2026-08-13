from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time

from services.query_planner import QueryPlanner, execute_plan
from models.query_plan import QueryPlan

router = APIRouter()
planner = QueryPlanner()

class QueryRequestV2(BaseModel):
    query: str

class QueryResponseV2(BaseModel):
    query: str
    intent: str
    data: Dict[str, Any]
    sources: List[str]
    answer: str
    execution_time_ms: float

@router.post("/query_v2", response_model=QueryResponseV2)
async def query_v2(request: QueryRequestV2, app_req: Request):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    start_time = time.time()
    
    # 1. Plan query
    try:
        plan = planner.generate_plan(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning failed: {e}")
        
    # 2. Execute plan across DuckDB/PostGIS/pgvector
    try:
        result = execute_plan(plan)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {e}")
        
    # 3. Format response (Simulating LLM synthesis for now)
    # The actual LLM call to Groq would synthesize the answer from the result["data"]
    synth_answer = f"Generated answer for intent '{plan.intent}'."
    if "scientific_result" in result.get("data", {}):
        val = result["data"]["scientific_result"].get("result")
        op = result["data"]["scientific_result"].get("operation")
        var = result["data"]["scientific_result"].get("variable")
        if val is not None:
            synth_answer = f"The {op} of {var} is {val:.2f}."
        else:
            synth_answer = f"No valid data found for {var}."

    exec_time = (time.time() - start_time) * 1000
    
    return QueryResponseV2(
        query=request.query,
        intent=result["intent"],
        data=result["data"],
        sources=result["sources"],
        answer=synth_answer,
        execution_time_ms=exec_time
    )
