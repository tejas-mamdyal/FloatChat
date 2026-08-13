import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import torch
import time
from tqdm import tqdm
import json

class FAISSEmbeddingStore:
    def __init__(self, model_name="all-MiniLM-L6-v2", index_path=None):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Use GPU if available
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = self.model.to(self.device)
        print(f"Using device: {self.device} for embeddings")
        
        if index_path and os.path.exists(index_path):
            print(f"Loading existing index from {index_path}")
            self.index = faiss.read_index(index_path)
            with open(f"{index_path}_metadata.pkl", "rb") as f:
                self.minimal_metadata = pickle.load(f)
        else:
            print("Creating new FAISS index")
            self.index = faiss.IndexHNSWFlat(self.embedding_dim, 32)
            self.index.hnsw.efConstruction = 64
            self.index.hnsw.efSearch = 32
            self.minimal_metadata = []
    
    def add_texts(self, texts, file_path, chunk_indices):
        """
        Add texts to the FAISS index with minimal metadata
        """
        if not texts:
            return []
        
        start_time = time.time()
        print(f"Generating embeddings for {len(texts)} texts...")
        
        batch_size = 512
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            batch_embeddings = self.model.encode(
                batch_texts, 
                show_progress_bar=True,
                convert_to_numpy=True,
                batch_size=64,
                normalize_embeddings=False
            )
            embeddings.append(batch_embeddings)
        
        embeddings = np.vstack(embeddings).astype(np.float32)
        faiss.normalize_L2(embeddings)
        
        start_idx = len(self.minimal_metadata)
        self.index.add(embeddings)
        
        # Store only minimal metadata in FAISS
        self.minimal_metadata.extend([{
            "file_path": file_path,
            "chunk_index": idx
        } for idx in chunk_indices])
        
        elapsed = time.time() - start_time
        print(f"Added {len(texts)} embeddings in {elapsed:.2f} seconds")
        
        return list(range(start_idx, start_idx + len(texts)))
    
    def similarity_search(self, query, k=5):
        """
        Search for similar texts
        """
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        
        # Search
        scores, indices = self.index.search(query_embedding, k)
        
        # Return results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata) and idx >= 0:
                text = self.metadata[idx].get("text", "")
                results.append((text, self.metadata[idx], float(scores[0][i])))
        
        return results
    
    def save(self, index_path):
        """
        Save the FAISS index and metadata
        """
        start_time = time.time()
        print(f"Saving index with {self.index.ntotal} vectors to {index_path}")
        
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        # Save index
        faiss.write_index(self.index, index_path)
        
        # Save metadata separately with compression
        with open(f"{index_path}_metadata.pkl", "wb") as f:
            pickle.dump(self.metadata, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        elapsed = time.time() - start_time
        print(f"Index saved in {elapsed:.2f} seconds")