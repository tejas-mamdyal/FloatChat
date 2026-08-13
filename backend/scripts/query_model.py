# query_model.py
import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-mpnet-base-v2"
MODEL = SentenceTransformer(EMBED_MODEL)
INDEX_FILE = "./models/index.pkl"

def index_exists():
    return os.path.exists(INDEX_FILE)

def load_index():
    if not index_exists():
        raise FileNotFoundError("Index file not found. Run train_model.py first.")
    with open(INDEX_FILE, "rb") as fh:
        return pickle.load(fh)

def query_model(query_text, top_k=5):
    """
    Returns list of file paths (top_k) matching query_text using cosine similarity.
    """
    index = load_index()
    if index["embeddings"].size == 0:
        return []

    qemb = MODEL.encode(query_text)
    qnorm = np.linalg.norm(qemb)
    if qnorm > 0:
        qemb = qemb / qnorm

    sims = index["embeddings"] @ qemb  # dot products (embeddings are normalized)
    idx_sorted = np.argsort(sims)[::-1][:top_k]
    return [index["file_paths"][i] for i in idx_sorted]

if __name__ == "__main__":
    print(query_model("temperature August 2025", top_k=5))
