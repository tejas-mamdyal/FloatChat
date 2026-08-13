from fastapi import APIRouter
from pydantic import BaseModel
import os
import chromadb

router = APIRouter()

class HealthStatus(BaseModel):
    status: str
    chroma_available: bool
    config_available: bool
    downloads_available: bool

@router.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint to verify system status"""
    
    # Check ChromaDB availability
    chroma_available = False
    try:
        client = chromadb.PersistentClient(path="./chroma_store")
        collections = client.list_collections()
        chroma_available = True
    except Exception:
        pass
    
    # Check config file
    config_available = os.path.exists("config.yaml")
    
    # Check downloads directory
    downloads_available = os.path.exists("./downloads") and os.path.isdir("./downloads")
    
    status = "healthy" if all([chroma_available, config_available, downloads_available]) else "degraded"
    
    return HealthStatus(
        status=status,
        chroma_available=chroma_available,
        config_available=config_available,
        downloads_available=downloads_available
    )

@router.get("/search/status")
async def search_status():
    return {"status": "ok"}
