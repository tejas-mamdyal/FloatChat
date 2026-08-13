import os
import hashlib
import psycopg2
import psycopg2.extras
import xarray as xr
import yaml
import numpy as np
from datetime import datetime, timedelta

# =========================
# Load Configuration
# =========================
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

DB = {
    "database": config["postgres"]["dbname"],
    "user": config["postgres"]["user"],
    "password": config["postgres"]["password"],
    "host": config["postgres"]["host"],
    "port": config["postgres"]["port"],
}
BASE_PATH = config["data"]["download_dir"]

# =========================
# Database Connection
# =========================
def connect_db():
    """Connect to PostgreSQL database."""
    return psycopg2.connect(
        dbname=DB["database"],
        user=DB["user"],
        password=DB["password"],
        host=DB["host"],
        port=DB["port"]
    )

# =========================
# Utility Functions
# =========================
def file_checksum(file_path):
    """Generate MD5 checksum for deduplication."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def julian_to_datetime(juld):
    """Convert Argo Julian date (days since 1950-01-01) to standard datetime."""
    try:
        base_date = datetime(1950, 1, 1)
        return base_date + timedelta(days=float(juld))
    except (OverflowError, ValueError):
        return None  # Invalid date

def safe_mean(values):
    """Compute safe mean, ignoring NaNs and invalid data."""
    if values is None or len(values) == 0:
        return None
    clean_values = np.array(values, dtype=np.float64)
    clean_values = clean_values[~np.isnan(clean_values)]
    return float(np.mean(clean_values)) if clean_values.size > 0 else None

def extract_metadata(nc_file):
    """
    Extract metadata from an Argo NetCDF file.
    Handles missing variables and large integer conversions.
    """
    try:
        with xr.open_dataset(nc_file, decode_times=False) as ds:
            # --- Extract Time ---
            if "JULD" in ds.variables:
                juld_values = ds["JULD"].values
                juld_values = np.array(juld_values, dtype=np.float64)
                start_date = julian_to_datetime(np.nanmin(juld_values))
                end_date = julian_to_datetime(np.nanmax(juld_values))
            elif "REFERENCE_DATE_TIME" in ds.variables:
                ref_time_str = str(ds["REFERENCE_DATE_TIME"].values)
                try:
                    ref_time = datetime.strptime(ref_time_str[:14], "%Y%m%d%H%M%S")
                    start_date = end_date = ref_time
                except Exception:
                    start_date = end_date = None
            else:
                raise ValueError("No valid time variable ('JULD' or 'REFERENCE_DATE_TIME') found")

            # --- Extract Location ---
            lat = safe_mean(ds["LATITUDE"].values) if "LATITUDE" in ds.variables else None
            lon = safe_mean(ds["LONGITUDE"].values) if "LONGITUDE" in ds.variables else None

            region = f"lat:{lat:.2f}, lon:{lon:.2f}" if lat is not None and lon is not None else "Unknown"

            return {
                "variable_name": "Argo Profile",
                "start_date": start_date.strftime("%Y-%m-%d") if start_date else None,
                "end_date": end_date.strftime("%Y-%m-%d") if end_date else None,
                "region": region
            }

    except Exception as e:
        print(f"[ERROR] Could not read {nc_file}: {e}")
        return None

# =========================
# Main Insertion Pipeline
# =========================
def insert_into_postgres():
    """Insert new NetCDF metadata into PostgreSQL."""
    conn = connect_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Get all .nc files
    files = [f for f in os.listdir(BASE_PATH) if f.endswith(".nc")]
    if not files:
        print("[INFO] No NetCDF files found in the downloads folder.")
        return

    print(f"[INFO] Found {len(files)} NetCDF files. Processing...")

    inserted_count = 0

    for filename in files:
        file_path = os.path.join(BASE_PATH, filename)
        checksum = file_checksum(file_path)
        file_size = os.path.getsize(file_path)

        # Skip duplicate files
        cur.execute("SELECT id FROM netcdf_files WHERE checksum = %s", (checksum,))
        if cur.fetchone():
            print(f"[SKIP] {filename} already exists in database.")
            continue

        # Extract metadata
        metadata = extract_metadata(file_path)
        if not metadata:
            print(f"[WARN] Skipping {filename} due to metadata extraction failure.")
            continue

        try:
            # Insert record with conflict handling
            cur.execute("""
                INSERT INTO netcdf_files 
                (file_path, start_date, end_date, variable_name, region, file_size, checksum)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (checksum) DO NOTHING
            """, (
                file_path,
                metadata["start_date"],
                metadata["end_date"],
                metadata["variable_name"],
                metadata["region"],
                file_size,
                checksum
            ))
            inserted_count += 1
        except Exception as db_error:
            print(f"[DB ERROR] Failed to insert {filename}: {db_error}")
            conn.rollback()
            continue

    conn.commit()
    cur.close()
    conn.close()

    print(f"[SUCCESS] Metadata insertion complete. {inserted_count} new records added.")

# =========================
# Entry Point
# =========================
if __name__ == "__main__":
    insert_into_postgres()
