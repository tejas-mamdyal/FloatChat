from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os
import subprocess

router = APIRouter(prefix="/rag", tags=["rag"])


class QueryRequest(BaseModel):
	query: str
	k: int = 5


@router.post("/ingest")
async def trigger_ingest():
	try:
		# Run the unified pipeline
		ret = subprocess.call(["python", os.path.join("scripts", "pipeline.py")])
		if ret != 0:
			raise HTTPException(status_code=500, detail="Pipeline failed")
		return {"status": "ok"}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def rag_query(req: QueryRequest, request: Request):
	if not hasattr(request.app.state, "rag_service") or request.app.state.rag_service is None:
		raise HTTPException(status_code=503, detail="Search service unavailable (index or model missing)")
		
	rag_service = request.app.state.rag_service
	
	try:
		results = rag_service.search(req.query, req.k)
		return {"results": results}
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
	except RuntimeError as e:
		raise HTTPException(status_code=503, detail="Search service unavailable")
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
