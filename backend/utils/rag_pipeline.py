import os
from .db_handler import PostgresHandler
from .embedding_store import FAISSEmbeddingStore
from .text_processor import extract_text_from_parquet, create_chunks
import json

class RAGPipeline:
    def __init__(self):
        self.db = PostgresHandler()
        self.embedding_store = FAISSEmbeddingStore()
    
    def process_parquet_file(self, file_path):
        """Process a single parquet file"""
        try:
            # Extract text from parquet
            text_content = extract_text_from_parquet(file_path)
            
            if not text_content:
                print(f"No content extracted from {file_path}")
                return 0
            
            # Create chunks with larger size
            chunks = create_chunks(text_content, chunk_size=5000, overlap=200)
            if not chunks:
                print(f"No chunks created from {file_path}")
                return 0
            
            # Create summary metadata for the file (not for each chunk)
            file_metadata = {
                "file_path": file_path,
                "total_chunks": len(chunks),
                "processed_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "sample_text": chunks[0][:500] if chunks else ""  # Just store a sample
            }
            
            # Store only file-level metadata in PostgreSQL
            self.db.store_file_metadata(file_path, file_metadata)
            
            # Store in FAISS with minimal chunk metadata
            chunk_indices = list(range(len(chunks)))
            self.embedding_store.add_texts(chunks, file_path, chunk_indices)
            
            return len(chunks)
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            raise
    
    def save_index(self, index_path):
        """Save the FAISS index"""
        if not index_path.endswith('.index'):
            index_path += '.index'
        
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        self.embedding_store.save(index_path)
        print(f"FAISS index saved to {index_path}")
    
    def query(self, query_text, k=5):
        """Query the RAG pipeline"""
        # Get similar chunks from FAISS
        results = self.embedding_store.similarity_search(query_text, k)
        
        # Enhance results with full metadata from PostgreSQL
        enhanced_results = []
        for text, minimal_meta, score in results:
            full_metadata = self.db.get_metadata(
                minimal_meta["file_path"],
                minimal_meta["chunk_index"]
            )
            enhanced_results.append({
                "text": text,
                "metadata": full_metadata,
                "score": score
            })
        
        return enhanced_results