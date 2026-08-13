import os
import yaml
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import xarray as xr

# =========================
# Config
# =========================
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

DOWNLOAD_DIR = config["data"]["download_dir"]
INDEX_DIR = os.path.join(DOWNLOAD_DIR, "faiss")
MODEL_NAME = "all-mpnet-base-v2"


def make_meta_text(nc_path: str) -> str:
    """Produce a compact metadata string from NetCDF for embedding."""
    try:
        ds = xr.open_dataset(nc_path)
        attrs = ds.attrs or {}
        variable_names = list(ds.data_vars)
        start = str(ds.coords.get("time").min().values) if "time" in ds.coords else ""
        end = str(ds.coords.get("time").max().values) if "time" in ds.coords else ""
        region = attrs.get("geospatial_bounds", attrs.get("region", ""))
        var = variable_names[0] if variable_names else ""
        return f"file:{os.path.basename(nc_path)} var:{var} region:{region} time:{start}..{end}"
    except Exception:
        return f"file:{os.path.basename(nc_path)}"


def build_index(nc_dir: str = DOWNLOAD_DIR, index_dir: str = INDEX_DIR) -> str:
    os.makedirs(index_dir, exist_ok=True)
    model = SentenceTransformer(MODEL_NAME)
    files = sorted([os.path.join(nc_dir, f) for f in os.listdir(nc_dir) if f.endswith(".nc")])
    if not files:
        raise RuntimeError("No .nc files found for FAISS index building")

    embeddings = []
    for path in files:
        text = make_meta_text(path)
        vec = model.encode(text)
        # L2-normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        embeddings.append(vec.astype("float32"))

    mat = np.vstack(embeddings)
    dim = mat.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine via dot on normalized vectors
    index.add(mat)

    faiss_path = os.path.join(index_dir, "netcdf.index")
    faiss.write_index(index, faiss_path)

    # Save mapping file list for reverse lookup
    np.save(os.path.join(index_dir, "file_paths.npy"), np.array(files))
    return faiss_path


if __name__ == "__main__":
    path = build_index()
    print(f"[SUCCESS] Wrote FAISS index to: {path}")


