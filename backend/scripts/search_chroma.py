import chromadb
import yaml
import sys
from sentence_transformers import SentenceTransformer

# =========================
# Load Configuration
# =========================
try:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    print("[ERROR] config.yaml not found. Please make sure it's in the project root.")
    sys.exit(1)

if "chroma" not in config or "persist_directory" not in config["chroma"]:
    print("[ERROR] Invalid config.yaml. Missing 'chroma.persist_directory'")
    sys.exit(1)

CHROMA_DIR = config["chroma"]["persist_directory"]

# =========================
# Embedding Model
# =========================
# Ensure this is the SAME model used for insertion
EMBED_MODEL = "all-mpnet-base-v2"  # 768 dimensions
print(f"[INFO] Using embedding model: {EMBED_MODEL}")
model = SentenceTransformer(EMBED_MODEL)

def generate_embedding(text: str):
    """Generate a vector embedding for the given query text."""
    return model.encode(text).tolist()

# =========================
# Infer embedding dimension dynamically
# =========================
def get_collection_dimension(collection):
    """
    Try to infer the embedding dimension dynamically.
    1. First, check metadata.
    2. If metadata is None, check the length of the first stored embedding.
    """
    if collection.metadata:
        dim = collection.metadata.get("embedding_dimension", None)
        if dim:
            return dim

    # Fallback: infer by fetching a single record
    try:
        sample = collection.get(limit=1)
        if sample and "embeddings" in sample and len(sample["embeddings"]) > 0:
            return len(sample["embeddings"][0])
    except Exception as e:
        print(f"[WARN] Could not infer embedding dimension dynamically: {e}")

    return None

# =========================
# Search Function
# =========================
def search(query_text: str, top_k: int = 5):
    """Perform semantic search on the NetCDF metadata collection."""
    print(f"[INFO] Connecting to Chroma DB at: {CHROMA_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Ensure collection exists
    try:
        collection = client.get_collection(name="netcdf_embeddings")
    except Exception:
        print("[ERROR] Collection 'netcdf_embeddings' not found. "
              "Run the insertion pipeline first.")
        return

    # Generate embedding for query
    query_embedding = generate_embedding(query_text)

    # Detect expected dimension
    expected_dim = get_collection_dimension(collection)
    if expected_dim is None:
        print("[WARN] Could not detect collection embedding dimension automatically. Skipping dimension check.")
    elif expected_dim != len(query_embedding):
        print(f"[ERROR] Dimension mismatch: Collection expects {expected_dim}, "
              f"but query embedding is {len(query_embedding)}.")
        print("Hint: Use the SAME embedding model for both insertion and search.")
        return

    # Perform semantic search
    print(f"[INFO] Searching for top {top_k} matches...")
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
    except Exception as e:
        print(f"[ERROR] Query failed: {str(e)}")
        return

    # Display results
    if not results.get("ids") or len(results["ids"][0]) == 0:
        print("[INFO] No matches found for this query.")
        return

    print("\n[SUCCESS] Top Matching Files:")
    for rank, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), start=1):
        print(f"\nRank {rank}:")
        print(f"  File       : {meta.get('file_path', 'Unknown')}")
        print(f"  Date Range : {meta.get('start_date', 'N/A')} to {meta.get('end_date', 'N/A')}")
        print(f"  Variable   : {meta.get('variable_name', 'N/A')}")
        print(f"  Region     : {meta.get('region', 'N/A')}")

# =========================
# Main Execution
# =========================
if __name__ == "__main__":
    query = "temperature data for August 2025 global region"
    search(query, top_k=5)
