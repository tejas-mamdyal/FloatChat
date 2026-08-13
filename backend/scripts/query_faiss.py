import os
import sys
import yaml
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

DOWNLOAD_DIR = config["data"]["download_dir"]
INDEX_DIR = os.path.join(DOWNLOAD_DIR, "faiss")
MODEL_NAME = "all-mpnet-base-v2"


def load_index(index_dir: str = INDEX_DIR):
    index_path = os.path.join(index_dir, "netcdf.index")
    if not os.path.exists(index_path):
        raise FileNotFoundError("FAISS index not found. Build it first.")
    index = faiss.read_index(index_path)
    files = np.load(os.path.join(index_dir, "file_paths.npy"), allow_pickle=True)
    return index, files


def search(query: str, k: int = 5):
    model = SentenceTransformer(MODEL_NAME)
    vec = model.encode(query)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    vec = vec.astype("float32")[None, :]
    index, files = load_index()
    scores, ids = index.search(vec, k)
    return [(float(scores[0][i]), str(files[ids[0][i]])) for i in range(min(k, ids.shape[1]))]


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "temperature profile Bay of Bengal"
    results = search(q, k=5)
    for s, f in results:
        print(f"{s:.4f}  {f}")


