# train_model.py
import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from netCDF4 import Dataset
from datetime import datetime, timedelta

BASE_DIR = "./downloads"
MODELS_DIR = "./models"
INDEX_FILE = os.path.join(MODELS_DIR, "index.pkl")
EMBED_MODEL = "all-mpnet-base-v2"

os.makedirs(MODELS_DIR, exist_ok=True)
model = SentenceTransformer(EMBED_MODEL)

def make_meta_text(path):
    # Lightweight metadata string used for embeddings
    try:
        with Dataset(path, "r") as nc:
            lat = nc.variables['LATITUDE'][0] if 'LATITUDE' in nc.variables else None
            lon = nc.variables['LONGITUDE'][0] if 'LONGITUDE' in nc.variables else None
            if 'JULD' in nc.variables:
                arr = nc.variables['JULD'][:]
                base = datetime(1950,1,1)
                start = str((base + timedelta(days=float(arr.min()))) .date()) if len(arr)>0 else None
                end = str((base + timedelta(days=float(arr.max()))) .date()) if len(arr)>0 else None
            else:
                start, end = None, None
            var_list = ",".join(list(nc.variables.keys()))
            return f"path:{os.path.basename(path)}, lat:{lat}, lon:{lon}, start:{start}, end:{end}, vars:{var_list}"
    except Exception:
        return f"path:{os.path.basename(path)}"

def build_index():
    files = sorted([f for f in os.listdir(BASE_DIR) if f.endswith(".nc")])
    file_paths = []
    embeddings = []

    print(f"[INFO] Building index from {len(files)} files...")
    for f in files:
        path = os.path.join(BASE_DIR, f)
        meta_text = make_meta_text(path)
        emb = model.encode(meta_text, show_progress_bar=False)
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        embeddings.append(emb)
        file_paths.append(path)

    embeddings = np.vstack(embeddings) if embeddings else np.zeros((0, model.get_sentence_embedding_dimension()))
    index = {"file_paths": file_paths, "embeddings": embeddings}
    with open(INDEX_FILE, "wb") as fh:
        pickle.dump(index, fh)
    print(f"[SUCCESS] Index saved: {INDEX_FILE}. Embedding dim: {model.get_sentence_embedding_dimension()}")

if __name__ == "__main__":
    build_index()
