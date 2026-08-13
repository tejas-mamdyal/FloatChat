import os
import glob
import time
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from concurrent.futures import ThreadPoolExecutor
from backend.utils.text_processor import create_chunks

# ---------------------- CONFIG ----------------------
PARQUET_DIR = r"c:\SIH\backend\downloads\parquet"
INDEX_DIR = r"c:\SIH\backend\vector_store"
INDEX_FILE = os.path.join(INDEX_DIR, "faiss_index_streaming_cpu.faiss")
METADATA_FILE = os.path.join(INDEX_DIR, "metadata.parquet")

MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
BATCH_SIZE_ROWS = 10000         # rows per parquet batch
BATCH_SIZE_EMBEDDINGS = 32      # embedding batch size
MAX_WORKERS = 4                 # threads for chunking
KEYWORD_FILTER = "ocean"        # Example: filter rows containing this keyword
TOP_K = 5
# ---------------------------------------------------

os.makedirs(INDEX_DIR, exist_ok=True)
model = SentenceTransformer(MODEL_NAME)
d = 384  # embedding dimension
index = faiss.IndexFlatL2(d)
metadata_list = []

def row_to_text(row):
    return (
        f"Profile {row.get('profile_id', 'N/A')} at ({row.get('latitude', 'N/A')}, {row.get('longitude', 'N/A')}) "
        f"on {row.get('juld', 'N/A')}:\n"
        f"Temperature: {row.get('temp', 'N/A')} C, Salinity: {row.get('psal', 'N/A')} PSU.\n"
        f"Source: {row.get('global_source', 'N/A')}, Title: {row.get('global_title', 'N/A')}, "
        f"History: {row.get('global_history', 'N/A')}"
    )

def create_chunks_parallel(texts):
    chunks = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(create_chunks, texts))
        for r in results:
            chunks.extend(r)
    return chunks

start_time = time.time()
parquet_files = glob.glob(os.path.join(PARQUET_DIR, "*.parquet"))
print(f"[INFO] Found {len(parquet_files)} parquet files")

for file_idx, file in enumerate(parquet_files):
    print(f"[INFO] Processing file {file_idx+1}/{len(parquet_files)}: {file}")

    # Read the entire file as a DataFrame
    batch_df_full = pq.ParquetFile(file).read().to_pandas()
    n_rows = len(batch_df_full)

    for start in range(0, n_rows, BATCH_SIZE_ROWS):
        end = min(start + BATCH_SIZE_ROWS, n_rows)
        batch_df = batch_df_full.iloc[start:end]

        # Optional keyword filtering
        if KEYWORD_FILTER:
            combined_texts = batch_df.apply(row_to_text, axis=1)
            mask = combined_texts.str.contains(KEYWORD_FILTER, case=False, na=False)
            batch_df = batch_df[mask]
            if batch_df.empty:
                continue

        texts = batch_df.apply(row_to_text, axis=1).tolist()
        chunks = create_chunks_parallel(texts)
        if not chunks:
            continue

        for i in range(0, len(chunks), BATCH_SIZE_EMBEDDINGS):
            batch_chunks = chunks[i:i+BATCH_SIZE_EMBEDDINGS]
            embeddings = model.encode(batch_chunks, convert_to_numpy=True).astype('float32')
            index.add(embeddings)

        metadata_list.extend([{"source_file": os.path.basename(file), "chunk_index": i} for i in range(len(chunks))])

faiss.write_index(index, INDEX_FILE)
pd.DataFrame(metadata_list).to_parquet(METADATA_FILE)
print(f"[INFO] FAISS index saved to {INDEX_FILE}")
print(f"[INFO] Metadata saved to {METADATA_FILE}")
print(f"[INFO] Total processing time: {time.time() - start_time:.2f} seconds")

def search(query, top_k=TOP_K):
    index = faiss.read_index(INDEX_FILE)
    metadata_df = pd.read_parquet(METADATA_FILE)
    query_vector = model.encode([query]).astype('float32')
    distances, indices = index.search(query_vector, top_k)
    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            "score": float(distances[0][i]),
            "metadata": metadata_df.iloc[idx].to_dict(),
            "chunk_index": metadata_df.iloc[idx]["chunk_index"]
        })
    return results

if __name__ == "__main__":
    user_query = "ocean temperature variations near Indian coast"
    results = search(user_query)
    print("\n[RESULTS]")
    for r in results:
        print(r)
