from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analysis, health, rag, rag_v2
from services.rag_service import RAGService
from contextlib import asynccontextmanager
import yaml
import sys
import logging

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        rag_service = RAGService(config)
        rag_service.load()
        app.state.rag_service = rag_service
    except Exception as e:
        logging.error(f"Startup failed: {e}")
        # Allow the app to start but service is broken, or sys.exit(1)
        # The prompt says: "Provide a clear startup error... fail clearly".
        # We will log the error. The app.state.rag_service will not be set or set to None.
        app.state.rag_service = None
        raise e
        
    yield
    app.state.rag_service = None

app = FastAPI(
    title="NetCDF Data Analysis API",
    description="API for searching and analyzing NetCDF oceanographic data",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rag_v2.router, prefix="/api/v1/rag", tags=["rag_v2"])
app.include_router(health.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(rag.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "NetCDF Data Analysis API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
