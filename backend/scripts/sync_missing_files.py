import os
import hashlib
import psycopg2
import yaml
import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime, timedelta
from netCDF4 import Dataset

# =========================
# Load Configuration
# =========================
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

DOWNLOAD_DIR = config["data"]["download_dir"]
POSTGRES_CONFIG = config["postgres"]
CHROMA_DIR = config["chroma"]["persist_directory"]

# Embedding Model
EMBED_MODEL = "all-mpnet-base-v2"  # 768 dimensions
model = SentenceTransformer(EMBED_MODEL)

# =========================
# Helper Functions
# =========================
def generate_checksum(file_path):
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_metadata_from_netcdf(file_path):
    """Extract key metadata from a NetCDF file safely."""
    try:
        with Dataset(file_path, "r") as nc:
            variables = list(nc.variables.keys())
            variable_name = variables[0] if variables else "Unknown"

            # Latitude and Longitude
            try:
                lat = float(nc.variables['LATITUDE'][0]) if 'LATITUDE' in nc.variables else None
                lon = float(nc.variables['LONGITUDE'][0]) if 'LONGITUDE' in nc.variables else None
                region = f"lat:{lat:.2f}, lon:{lon:.2f}" if lat is not None and lon is not None else "Unknown"
            except:
                region = "Unknown"

            # Time range (Argo format: JULD is days since 1950-01-01)
            try:
                if 'JULD' in nc.variables:
                    base_date = datetime(1950, 1, 1)
                    start_date = base_date + timedelta(days=float(nc.variables['JULD'][0]))
                    end_date = base_date + timedelta(days=float(nc.variables['JULD'][-1]))
                else:
                    start_date, end_date = None, None
            except:
                start_date, end_date = None, None

            return {
                "variable_name": variable_name or "Unknown",
                "region": region or "Unknown",
                "start_date": str(start_date.date()) if start_date else "Unknown",
                "end_date": str(end_date.date()) if end_date else "Unknown"
            }
    except Exception as e:
        print(f"[ERROR] Failed to read {file_path}: {e}")
        return {
            "variable_name": "Unknown",
            "region": "Unknown",
            "start_date": "Unknown",
            "end_date": "Unknown"
        }

def generate_embedding(text):
    """Generate embedding vector for text."""
    return model.encode(text).tolist()

# =========================
# PostgreSQL Functions
# =========================
def connect_postgres():
    return psycopg2.connect(
        dbname=POSTGRES_CONFIG["dbname"],
        user=POSTGRES_CONFIG["user"],
        password=POSTGRES_CONFIG["password"],
        host=POSTGRES_CONFIG["host"],
        port=POSTGRES_CONFIG["port"]
    )

def get_file_id_from_postgres(checksum, file_path=None):
    """Check if file exists in PostgreSQL by checksum or file_path and return ID."""
    conn = connect_postgres()
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM netcdf_files 
        WHERE checksum = %s OR file_path = %s
    """, (checksum, file_path))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

def insert_into_postgres(file_path, metadata, checksum):
    """Insert file metadata into PostgreSQL only if it's new."""
    conn = connect_postgres()
    cur = conn.cursor()
    file_size = os.path.getsize(file_path)

    try:
        cur.execute("""
            INSERT INTO netcdf_files (file_path, start_date, end_date, variable_name, region, file_size, checksum)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id;
        """, (
            file_path,
            metadata["start_date"],
            metadata["end_date"],
            metadata["variable_name"],
            metadata["region"],
            file_size,
            checksum
        ))

        inserted = cur.fetchone()
        conn.commit()

        if inserted:
            file_id = inserted[0]
            print(f"[SUCCESS] Inserted into PostgreSQL: {file_path}")
            return file_id
        else:
            print(f"[INFO] Skipped (already exists in PostgreSQL): {file_path}")
            return None

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] PostgreSQL insert failed for {file_path}: {e}")
        return None

    finally:
        cur.close()
        conn.close()

# =========================
# Chroma DB Functions
# =========================
def connect_chroma():
    return chromadb.PersistentClient(path=CHROMA_DIR)

def is_file_in_chroma(file_id):
    """Check if a file is already in ChromaDB by file_id."""
    client = connect_chroma()
    collection = client.get_or_create_collection(name="netcdf_embeddings")
    results = collection.get(ids=[str(file_id)])
    return len(results["ids"]) > 0

def insert_into_chroma(file_id, file_path, metadata):
    """Insert file into ChromaDB with sanitized metadata."""
    if not file_id:
        return  # Don't insert into Chroma if not in PostgreSQL

    client = connect_chroma()
    collection = client.get_or_create_collection(name="netcdf_embeddings")

    # Convert all metadata values to strings to avoid NoneType errors
    safe_metadata = {k: str(v) if v is not None else "Unknown" for k, v in metadata.items()}
    safe_metadata["file_path"] = str(file_path)

    text_for_embedding = (
        f"File path: {safe_metadata['file_path']}, "
        f"Variable: {safe_metadata['variable_name']}, "
        f"Region: {safe_metadata['region']}, "
        f"Date Range: {safe_metadata['start_date']} to {safe_metadata['end_date']}"
    )

    embedding = generate_embedding(text_for_embedding)

    collection.add(
        ids=[str(file_id)],
        embeddings=[embedding],
        documents=[text_for_embedding],
        metadatas=[safe_metadata]
    )
    print(f"[SUCCESS] Inserted into ChromaDB: {file_path}")

# =========================
# Main Sync Logic
# =========================
def sync_missing_files():
    print("[INFO] Scanning local downloads folder...")

    if not os.path.exists(DOWNLOAD_DIR):
        print(f"[ERROR] Download directory does not exist: {DOWNLOAD_DIR}")
        return

    nc_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.nc')]
    print(f"[INFO] Found {len(nc_files)} NetCDF files locally.")

    for filename in nc_files:
        file_path = os.path.join(DOWNLOAD_DIR, filename)

        # Step 1: Compute checksum
        checksum = generate_checksum(file_path)

        # Step 2: Check if file already exists in PostgreSQL
        file_id = get_file_id_from_postgres(checksum, file_path)
        if file_id:
            print(f"[INFO] Already in PostgreSQL: {filename}")
        else:
            print(f"[INFO] Adding missing file to PostgreSQL: {filename}")
            metadata = extract_metadata_from_netcdf(file_path)
            file_id = insert_into_postgres(file_path, metadata, checksum)

        # Step 3: Insert into Chroma only if it's missing
        if file_id:
            if not is_file_in_chroma(file_id):
                print(f"[INFO] Adding missing file to ChromaDB: {filename}")
                metadata = extract_metadata_from_netcdf(file_path)
                insert_into_chroma(file_id, file_path, metadata)
            else:
                print(f"[INFO] Already in ChromaDB: {filename}")

    print("\n[INFO] Sync complete!")

# =========================
# Run Script
# =========================
if __name__ == "__main__":
    sync_missing_files()
