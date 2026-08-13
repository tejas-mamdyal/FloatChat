# scripts/dashboard.py
import streamlit as st
import chromadb
import yaml
import sys
import requests
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from netCDF4 import Dataset
from sentence_transformers import SentenceTransformer
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression

# Import local query model utilities
from query_model import query_model, index_exists

# =========================
# Session State Initialization
# =========================
for key in ["search_done", "file_paths", "metadata_list", "stats_list", "lat_lon_list"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "list" in key else False

# =========================
# Load Configuration
# =========================
try:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    st.error("❌ config.yaml not found. Please make sure it's in the project root.")
    sys.exit(1)

CHROMA_DIR = config["chroma"]["persist_directory"]
GROQ_API_KEY = config.get("groq_api_key") or os.getenv("GROQ_API_KEY")
DOWNLOAD_DIR = config["data"]["download_dir"]

# =========================
# Initialize Embedding Model (Chroma fallback only)
# =========================
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-mpnet-base-v2")

embed_model = load_embedding_model()

def generate_embedding(text: str):
    return embed_model.encode(text).tolist()

# =========================
# ChromaDB Search
# =========================
def connect_chroma():
    return chromadb.PersistentClient(path=CHROMA_DIR)

@st.cache_data(show_spinner=False)
def search_chroma(query_text: str, top_k: int = 5):
    """Search in ChromaDB and return file paths with metadata."""
    client = connect_chroma()
    try:
        collection = client.get_collection(name="netcdf_embeddings")
    except Exception:
        st.error("❌ ChromaDB collection 'netcdf_embeddings' not found. Run the ingestion pipeline first.")
        return [], {}

    qemb = generate_embedding(query_text)
    results = collection.query(query_embeddings=[qemb], n_results=top_k)
    file_paths = [m.get("file_path") for m in results.get("metadatas", [[]])[0]]
    return file_paths, results

# =========================
# Read NetCDF Files
# =========================
@st.cache_data(show_spinner=False)
def read_netcdf_data(file_path):
    """Extract statistics and lat/lon from a NetCDF file."""
    try:
        with Dataset(file_path, "r") as nc:
            stats = {}
            lat, lon = None, None

            if 'LATITUDE' in nc.variables:
                lat = float(nc.variables['LATITUDE'][0])
            if 'LONGITUDE' in nc.variables:
                lon = float(nc.variables['LONGITUDE'][0])

            # Time parsing
            time_data = []
            if "JULD" in nc.variables:
                base_date = datetime(1950, 1, 1)
                time_data = [base_date + timedelta(days=float(t)) for t in nc.variables["JULD"][:]]

            # Extract main variables
            core_vars = [v for v in nc.variables.keys() if v not in ["LATITUDE", "LONGITUDE", "JULD", "time"]]

            for var in core_vars:
                try:
                    data = np.array(nc.variables[var][:]).flatten()
                    data = data[np.isfinite(data)]
                    if len(data) == 0:
                        continue

                    stats[var] = {
                        "min": float(np.min(data)),
                        "max": float(np.max(data)),
                        "mean": float(np.mean(data)),
                        "std_dev": float(np.std(data)),
                        "count": int(len(data))
                    }

                    # Detect trend
                    if time_data and len(time_data) == len(data) and len(data) > 2:
                        timestamps = np.array([t.timestamp() for t in time_data]).reshape(-1, 1)
                        lr = LinearRegression().fit(timestamps, data)
                        slope = lr.coef_[0]
                        stats[var]["trend"] = "Increasing" if slope > 0 else "Decreasing"
                    else:
                        stats[var]["trend"] = "Stable"

                except Exception as e:
                    st.warning(f"Could not compute stats for {var} in {os.path.basename(file_path)}: {e}")

            return stats, lat, lon, time_data
    except Exception as e:
        st.error(f"❌ Error reading {file_path}: {e}")
        return {}, None, None, None

# =========================
# Groq API Insights
# =========================
def generate_groq_insights(query, metadata_list, stats_list):
    if not GROQ_API_KEY:
        return "⚠️ Groq API key missing. Cannot generate AI insights."

    context = "Analyzed NetCDF files:\n\n"
    for idx, (meta, stats) in enumerate(zip(metadata_list, stats_list), start=1):
        context += f"File {idx}: {meta.get('file_path', 'Unknown')}\n"
        for var, s in stats.items():
            context += (
                f"  - {var}: min={s['min']}, max={s['max']}, mean={s['mean']}, "
                f"std_dev={s['std_dev']}, trend={s['trend']}\n"
            )
        context += "\n"

    prompt = (
        f"You are a senior oceanographic scientist.\n"
        f"User query: {query}\n\n"
        f"{context}\n"
        f"Provide insights, trends, and potential implications in simple terms."
    )

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are an expert ocean data analyst."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3
            }
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        return f"❌ Groq API Error {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"❌ API call failed: {str(e)}"

# =========================
# Streamlit UI
# =========================
st.set_page_config(page_title="NetCDF Data Dashboard", layout="wide")
st.title("🌊 NetCDF Data Search & Analysis Dashboard")

query = st.text_input("Enter your query:", placeholder="e.g., Salinity trends in Indian Ocean")
top_k = st.slider("Number of results", 1, 10, 5)

# Toggle between index and Chroma search
use_index = st.checkbox("Use local model index (fast)", value=index_exists())

# ---------------------------
# Search Button Logic
# ---------------------------
if st.button("Search & Analyze"):
    st.session_state.search_done = False
    st.session_state.file_paths = []
    st.session_state.metadata_list = []
    st.session_state.stats_list = []
    st.session_state.lat_lon_list = []

    if not query.strip():
        st.warning("⚠️ Please enter a query.")
    else:
        # Try local model search first
        if use_index and index_exists():
            with st.spinner("🔎 Searching local index..."):
                try:
                    st.session_state.file_paths = query_model(query, top_k=top_k)
                    st.info("Using local index search (fast).")
                except Exception as e:
                    st.warning(f"Local index search failed: {e}. Falling back to ChromaDB.")
                    use_index = False

        # Fallback to ChromaDB
        if (not use_index) or (use_index and not st.session_state.file_paths):
            with st.spinner("🔍 Searching ChromaDB..."):
                st.session_state.file_paths, chroma_results = search_chroma(query, top_k=top_k)
                if chroma_results.get("metadatas"):
                    st.session_state.metadata_list = chroma_results["metadatas"][0]

        if st.session_state.file_paths:
            st.session_state.search_done = True
        else:
            st.warning("⚠️ No matching files found.")

# ---------------------------
# Display Results
# ---------------------------
if st.session_state.search_done:
    st.success(f"Found {len(st.session_state.file_paths)} matching files.")

    tabs = st.tabs(["Overview", "Statistics", "Maps", "AI Insights"])

    # ---- Overview ----
    with tabs[0]:
        st.subheader("Top Matching Files")
        for i, fp in enumerate(st.session_state.file_paths, start=1):
            st.json({"Rank": i, "File": fp})

    # ---- Statistics ----
    with tabs[1]:
        st.subheader("Computed Statistics")
        if not st.session_state.stats_list:
            with st.spinner("Reading files and calculating stats..."):
                for fp in st.session_state.file_paths:
                    stats, lat, lon, _ = read_netcdf_data(fp)
                    st.session_state.stats_list.append(stats)
                    st.session_state.lat_lon_list.append((lat, lon))

        for fp, stats in zip(st.session_state.file_paths, st.session_state.stats_list):
            if stats:
                st.write(f"**{os.path.basename(fp)}**")
                st.dataframe(pd.DataFrame(stats).T)

    # ---- Maps ----
    with tabs[2]:
        st.subheader("Buoy Locations")
        valid_points = [
            (lat, lon, fp) for (lat, lon), fp in zip(st.session_state.lat_lon_list, st.session_state.file_paths)
            if lat is not None and lon is not None and not np.isnan(lat) and not np.isnan(lon)
        ]
        if valid_points:
            mean_lat = np.mean([v[0] for v in valid_points])
            mean_lon = np.mean([v[1] for v in valid_points])
            m = folium.Map(location=[mean_lat, mean_lon], zoom_start=2)
            for lat, lon, fp in valid_points:
                folium.Marker([lat, lon], popup=os.path.basename(fp)).add_to(m)
            st_folium(m, width=700, height=500)
        else:
            st.info("No valid coordinates found for mapping.")

    # ---- AI Insights ----
    with tabs[3]:
        st.subheader("AI-Generated Insights")
        if st.session_state.stats_list:
            with st.spinner("Generating AI insights..."):
                insights = generate_groq_insights(query, st.session_state.metadata_list, st.session_state.stats_list)
            st.write(insights)
        else:
            st.info("Run the Statistics tab first to generate insights.")
