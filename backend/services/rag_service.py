import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.index = None
        self.files = None
        self.dimension = 768

    def load(self):
        try:
            logger.info("Loading embedding model...")
            self.model = SentenceTransformer("all-mpnet-base-v2")
            
            logger.info("Loading FAISS index...")
            index_dir = os.path.join(self.config["data"]["download_dir"], "faiss")
            index_path = os.path.join(index_dir, "netcdf.index")
            paths_path = os.path.join(index_dir, "file_paths.npy")
            
            if not os.path.exists(index_path) or not os.path.exists(paths_path):
                raise FileNotFoundError(f"FAISS index or paths file not found in {index_dir}")
                
            self.index = faiss.read_index(index_path)
            self.files = np.load(paths_path, allow_pickle=True)
            
            if self.index.d != self.dimension:
                raise ValueError(f"FAISS index dimension mismatch. Expected {self.dimension}, got {self.index.d}")
                
            if self.index.ntotal != len(self.files):
                raise ValueError(f"FAISS metadata mismatch. Index has {self.index.ntotal} vectors, but found {len(self.files)} file paths.")
                
            logger.info("RAG Service loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load RAG Service: {e}")
            raise

    def search(self, query: str, top_k: int = 5):
        if not self.model or not self.index:
            raise RuntimeError("RAG Service not initialized")
            
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
            
        vec = self.model.encode(query.strip())
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        vec = vec.astype("float32")[None, :]
        
        scores, ids = self.index.search(vec, top_k)
        
        results = []
        parquet_dir = os.path.join(self.config["data"]["download_dir"], "parquet")
        
        for i in range(min(top_k, ids.shape[1])):
            idx = int(ids[0][i])
            if idx < 0 or idx >= len(self.files):
                continue
            nc_path = str(self.files[idx])
            base = os.path.splitext(os.path.basename(nc_path))[0]
            parquet_path = os.path.join(parquet_dir, f"{base}.parquet")
            preferred_path = parquet_path if os.path.exists(parquet_path) else nc_path
            
            results.append({
                "score": float(scores[0][i]),
                "file_path": preferred_path,
                "source_netcdf": nc_path,
                "parquet": parquet_path if os.path.exists(parquet_path) else None
            })
            
        return results
