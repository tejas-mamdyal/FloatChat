# update_model.py
import os
import pickle
import numpy as np
from train_model import BASE_DIR, INDEX_FILE, model, make_meta_text

def load_index():
    if not os.path.exists(INDEX_FILE):
        return {"file_paths": [], "embeddings": np.zeros((0, model.get_sentence_embedding_dimension()))}
    with open(INDEX_FILE, "rb") as fh:
        return pickle.load(fh)

def save_index(index):
    with open(INDEX_FILE, "wb") as fh:
        pickle.dump(index, fh)

def update_index():
    index = load_index()
    existing = set(index["file_paths"])
    all_files = sorted([os.path.join(BASE_DIR, f) for f in os.listdir(BASE_DIR) if f.endswith(".nc")])

    new_paths = [p for p in all_files if p not in existing]
    if not new_paths:
        print("[INFO] No new NetCDF files found for index update.")
        return

    print(f"[INFO] Adding {len(new_paths)} new files to index...")
    new_embs = []
    for p in new_paths:
        meta_text = make_meta_text(p)
        emb = model.encode(meta_text, show_progress_bar=False)
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        new_embs.append(emb)

    if len(new_embs) > 0:
        new_embs = np.vstack(new_embs)
        if index["embeddings"].size == 0:
            index["embeddings"] = new_embs
        else:
            index["embeddings"] = np.vstack([index["embeddings"], new_embs])
        index["file_paths"].extend(new_paths)
        save_index(index)
        print("[SUCCESS] Index updated and saved.")
    else:
        print("[WARN] Nothing to append (no valid embeddings).")

if __name__ == "__main__":
    update_index()
