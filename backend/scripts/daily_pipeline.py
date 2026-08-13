import os
import hashlib
import psycopg2
import yaml
import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime
from netCDF4 import Dataset
from ftplib import FTP

# =========================
# Load Configuration
# =========================
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

FTP_HOST = "ftp.ifremer.fr"
FTP_DIR = "/ifremer/argo/latest_data/"
DOWNLOAD_DIR = config["data"]["download_dir"]

POSTGRES_CONFIG = config["postgres"]
CHROMA_DIR = config["chroma"]["persist_directory"]

# =========================
# Embedding Model
# =========================
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
    """Extract metadata safely from a NetCDF file."""
    metadata = {
        "variable_name": "Unknown",
        "region": "Unknown",
        "start_date": None,
        "end_date": None
    }

    try:
        with Dataset(file_path, "r") as nc:
            # Extract variable name
            variables = list(nc.variables.keys())
            if variables:
                metadata["variable_name"] = variables[0]

            # Extract region (lat/lon)
            try:
                lat = nc.variables.get('lat') or nc.variables.get('latitude')
                lon = nc.variables.get('lon') or nc.variables.get('longitude')
                if lat is not None and lon is not None:
                    lat_mean = float(lat[:].mean())
                    lon_mean = float(lon[:].mean())
                    metadata["region"] = f"lat:{lat_mean:.2f}, lon:{lon_mean:.2f}"
            except Exception as e:
                print(f"[WARN] Could not extract region from {file_path}: {e}")

            # Extract time range
            try:
                time_var = nc.variables.get('time')
                if time_var is not None and len(time_var) > 0:
                    start = min(time_var[:])
                    end = max(time_var[:])
                    metadata["start_date"] = datetime.utcfromtimestamp(start).date()
                    metadata["end_date"] = datetime.utcfromtimestamp(end).date()
            except Exception as e:
                print(f"[WARN] Could not extract time range from {file_path}: {e}")

    except Exception as e:
        print(f"[ERROR] Failed to read NetCDF file {file_path}: {e}")

    return metadata

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

def file_exists_in_postgres(checksum):
    """Check if a file already exists in PostgreSQL using checksum."""
    conn = connect_postgres()
    cur = conn.cursor()
    cur.execute("SELECT id FROM netcdf_files WHERE checksum = %s", (checksum,))
    exists = cur.fetchone()
    cur.close()
    conn.close()
    return exists is not None

def insert_into_postgres(file_path, metadata, checksum):
    """Insert file metadata into PostgreSQL."""
    conn = connect_postgres()
    cur = conn.cursor()

    file_size = os.path.getsize(file_path)

    try:
        cur.execute("""
            INSERT INTO netcdf_files (file_path, start_date, end_date, variable_name, region, file_size, checksum)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (checksum) DO NOTHING
            RETURNING id;
        """, (
            file_path,
            metadata.get("start_date"),
            metadata.get("end_date"),
            metadata.get("variable_name", "Unknown"),
            metadata.get("region", "Unknown"),
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
            print(f"[INFO] File already exists in PostgreSQL (checksum match): {file_path}")
            return None

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to insert into PostgreSQL for {file_path}: {e}")
        return None

    finally:
        cur.close()
        conn.close()

# =========================
# Chroma DB Functions
# =========================
def insert_into_chroma(file_id, file_path, metadata):
    """Insert file details into ChromaDB with fully safe metadata."""
    if file_id is None:
        print(f"[WARN] Skipping ChromaDB insert because file_id is None for {file_path}")
        return

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(name="netcdf_embeddings")

    # ---- FULL SANITIZATION ----
    safe_metadata = {}
    for key, value in metadata.items():
        if value is None:
            safe_metadata[key] = "Unknown"  # Replace None with "Unknown"
        elif isinstance(value, (int, float, bool)):
            safe_metadata[key] = str(value)  # Convert numbers & bools to strings
        else:
            safe_metadata[key] = str(value)  # Ensure all remaining are strings

    # Always include file_path
    safe_metadata["file_path"] = str(file_path)

    # Create clean text for embedding
    text_for_embedding = (
        f"File path: {safe_metadata['file_path']}, "
        f"Variable: {safe_metadata.get('variable_name', 'Unknown')}, "
        f"Region: {safe_metadata.get('region', 'Unknown')}, "
        f"Date Range: {safe_metadata.get('start_date', 'Unknown')} to {safe_metadata.get('end_date', 'Unknown')}"
    )

    # Generate embedding
    embedding = generate_embedding(text_for_embedding)

    # Debug print to verify metadata
    print("[DEBUG] Final metadata being inserted into ChromaDB:", safe_metadata)

    try:
        collection.add(
            ids=[str(file_id)],
            embeddings=[embedding],
            documents=[text_for_embedding],
            metadatas=[safe_metadata]
        )
        print(f"[SUCCESS] Inserted into ChromaDB: {file_path}")
    except Exception as e:
        print(f"[ERROR] Failed to insert into ChromaDB for {file_path}: {e}")


# =========================
# FTP Functions
# =========================
def list_ftp_files():
    """List all files in the FTP latest_data directory."""
    ftp = FTP(FTP_HOST)
    ftp.login()  # Anonymous login
    ftp.cwd(FTP_DIR)

    files = ftp.nlst()
    ftp.quit()

    return [f for f in files if f.endswith('.nc')]

def download_ftp_file(filename):
    """Download a single file from the FTP server."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    local_path = os.path.join(DOWNLOAD_DIR, filename)

    ftp = FTP(FTP_HOST)
    ftp.login()
    ftp.cwd(FTP_DIR)

    with open(local_path, "wb") as f:
        ftp.retrbinary(f"RETR {filename}", f.write)

    ftp.quit()
    return local_path

# =========================
# Main Processing
# =========================
def process_new_files():
    print("[INFO] Connecting to FTP and listing files...")
    all_files = list_ftp_files()
    print(f"[INFO] Found {len(all_files)} files on FTP server.")

    # Check which files are missing locally
    local_files = set(os.listdir(DOWNLOAD_DIR)) if os.path.exists(DOWNLOAD_DIR) else set()
    missing_files = [f for f in all_files if f not in local_files]

    print(f"[INFO] Missing files to download: {len(missing_files)}")

    for filename in missing_files:
        print(f"\n[INFO] Downloading new file: {filename}")
        local_path = download_ftp_file(filename)

        # Generate checksum
        checksum = generate_checksum(local_path)

        # Skip if already in PostgreSQL
        if file_exists_in_postgres(checksum):
            print(f"[INFO] Skipping {filename}, already exists in PostgreSQL.")
            continue

        # Extract metadata
        metadata = extract_metadata_from_netcdf(local_path)

        # Insert into PostgreSQL
        file_id = insert_into_postgres(local_path, metadata, checksum)

        # Insert into ChromaDB
        insert_into_chroma(file_id, local_path, metadata)

    print("\n[INFO] Daily processing complete.")

# =========================
# Main Execution
# =========================
if __name__ == "__main__":
    process_new_files()
