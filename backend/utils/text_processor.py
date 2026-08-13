import pandas as pd
import re
import numpy as np

def extract_text_from_parquet(parquet_path):
    """
    Extract text content from a Parquet file
    
    Args:
        parquet_path: Path to the Parquet file
    
    Returns:
        String containing the text representation of the data
    """
    try:
        # Read the Parquet file
        df = pd.read_parquet(parquet_path)
        
        # Convert DataFrame to string representation
        # This is a simple approach - you might need to customize this based on your data
        text_content = df.to_string()
        
        return text_content
    
    except Exception as e:
        print(f"Error extracting text from {parquet_path}: {str(e)}")
        return ""

def create_chunks(text, chunk_size=5000, overlap=200):
    """
    Create larger chunks from text with minimal overlap using a fast approach
    
    Args:
        text: Text to chunk
        chunk_size: Number of characters per chunk (increased for better performance)
        overlap: Number of characters to overlap between chunks
    """
    if not text:
        return []
    
    # Fast chunking with paragraph breaks
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size, save current chunk and start new one
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep some overlap from the end of the previous chunk
            current_chunk = current_chunk[-overlap:] if overlap > 0 else ""
        
        # Add paragraph to current chunk
        current_chunk += paragraph + "\n\n"
    
    # Add the last chunk if it's not empty
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # If chunks are still too large, split them further
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > chunk_size * 1.5:  # Only split if significantly larger
            # Simple splitting at sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', chunk)
            temp_chunk = ""
            
            for sentence in sentences:
                if len(temp_chunk) + len(sentence) > chunk_size and temp_chunk:
                    final_chunks.append(temp_chunk.strip())
                    temp_chunk = ""
                temp_chunk += sentence + " "
            
            if temp_chunk.strip():
                final_chunks.append(temp_chunk.strip())
        else:
            final_chunks.append(chunk)
    
    return final_chunks


def extract_vectors_from_parquet(parquet_path):
    """
    Extract data directly from parquet and prepare for vector storage
    """
    try:
        # Read the Parquet file
        df = pd.read_parquet(parquet_path)
        
        # Convert numeric columns to vectors
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Pad or truncate to match FAISS dimension (384 for 'all-MiniLM-L6-v2')
        target_dim = 384
        vectors = np.ascontiguousarray(df[numeric_cols].fillna(0).values.astype(np.float32))
        
        # Pad if fewer dimensions
        if vectors.shape[1] < target_dim:
            padding = np.zeros((vectors.shape[0], target_dim - vectors.shape[1]), dtype=np.float32)
            vectors = np.hstack([vectors, padding])
        # Truncate if more dimensions
        elif vectors.shape[1] > target_dim:
            vectors = vectors[:, :target_dim]
            
        metadata = {
            "columns": numeric_cols.tolist(),
            "file_path": parquet_path,
            "row_count": len(df),
            "original_dims": len(numeric_cols)
        }
        
        return vectors, metadata
    
    except Exception as e:
        print(f"Error processing {parquet_path}: {str(e)}")
        return None, None