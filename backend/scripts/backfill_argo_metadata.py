import os
import sys
import argparse
import hashlib
import pyarrow.parquet as pq
import pandas as pd
from datetime import datetime, timedelta
import yaml

# Ensure database package is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.core import get_db_connection

def file_checksum(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def julian_to_datetime(juld):
    try:
        base_date = datetime(1950, 1, 1)
        return base_date + timedelta(days=float(juld))
    except (OverflowError, ValueError, TypeError):
        return None

def backfill(dry_run=False, limit=None):
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.yaml"))
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    parquet_dir = os.path.join(config["data"]["download_dir"], "parquet")
    if not os.path.exists(parquet_dir):
        print(f"Parquet directory not found: {parquet_dir}")
        return
        
    files = [f for f in os.listdir(parquet_dir) if f.endswith(".parquet")]
    print(f"Discovered: {len(files)} files")
    
    if limit:
        files = files[:limit]
        
    inserted_files = 0
    inserted_profiles = 0
    skipped_profiles = 0
    failed_files = 0
    
    for filename in files:
        file_path = os.path.join(parquet_dir, filename)
        
        try:
            # Read only required columns for memory efficiency
            df = pd.read_parquet(file_path, engine='fastparquet', columns=['profile_id', 'latitude', 'longitude', 'juld'])
            
            # Aggregate to profile level (taking first row since coords repeat per level)
            profiles_df = df.groupby('profile_id').first().reset_index()
            
            valid_profiles = []
            file_start_time = None
            file_end_time = None
            
            min_lon, max_lon = 180.0, -180.0
            min_lat, max_lat = 90.0, -90.0
            
            for _, row in profiles_df.iterrows():
                prof_id = int(row['profile_id'])
                
                lat = float(row['latitude']) if not pd.isna(row['latitude']) else None
                lon = float(row['longitude']) if not pd.isna(row['longitude']) else None
                juld = row['juld'] if not pd.isna(row['juld']) else None
                
                prof_time = julian_to_datetime(juld) if juld is not None else None
                
                if lat is None or lon is None or lat < -90 or lat > 90 or lon < -180 or lon > 180:
                    skipped_profiles += 1
                    lat, lon = None, None
                else:
                    min_lat = min(min_lat, lat)
                    max_lat = max(max_lat, lat)
                    min_lon = min(min_lon, lon)
                    max_lon = max(max_lon, lon)
                    
                if prof_time:
                    if file_start_time is None or prof_time < file_start_time:
                        file_start_time = prof_time
                    if file_end_time is None or prof_time > file_end_time:
                        file_end_time = prof_time
                        
                valid_profiles.append({
                    'source_profile_id': prof_id,
                    'lat': lat,
                    'lon': lon,
                    'time': prof_time
                })
            
            bbox_wkt = None
            if min_lat <= max_lat and min_lon <= max_lon:
                # Basic Envelope. PostGIS supports proper geography, but we use ST_MakeEnvelope internally
                # ST_MakeEnvelope(xmin, ymin, xmax, ymax, srid) is preferred
                bbox_wkt = f"ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat}, 4326)"

            checksum = file_checksum(file_path)
            
            if not dry_run:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        # Upsert file identity
                        if bbox_wkt:
                            cur.execute(f"""
                                INSERT INTO argo_files (file_path, checksum, start_time, end_time, trajectory_bbox)
                                VALUES (%s, %s, %s, %s, {bbox_wkt})
                                ON CONFLICT (file_path) DO UPDATE SET
                                    checksum = EXCLUDED.checksum,
                                    start_time = EXCLUDED.start_time,
                                    end_time = EXCLUDED.end_time,
                                    trajectory_bbox = EXCLUDED.trajectory_bbox,
                                    updated_at = CURRENT_TIMESTAMP
                                RETURNING file_id;
                            """, (file_path, checksum, file_start_time, file_end_time))
                        else:
                            cur.execute("""
                                INSERT INTO argo_files (file_path, checksum, start_time, end_time, trajectory_bbox)
                                VALUES (%s, %s, %s, %s, NULL)
                                ON CONFLICT (file_path) DO UPDATE SET
                                    checksum = EXCLUDED.checksum,
                                    start_time = EXCLUDED.start_time,
                                    end_time = EXCLUDED.end_time,
                                    trajectory_bbox = EXCLUDED.trajectory_bbox,
                                    updated_at = CURRENT_TIMESTAMP
                                RETURNING file_id;
                            """, (file_path, checksum, file_start_time, file_end_time))
                        
                        file_id = cur.fetchone()[0]
                        
                        # Upsert profiles in batch
                        for p in valid_profiles:
                            if p['lat'] is not None and p['lon'] is not None:
                                loc_wkt = f"POINT({p['lon']} {p['lat']})"
                                cur.execute("""
                                    INSERT INTO argo_profiles (file_id, source_profile_id, profile_time, location)
                                    VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326))
                                    ON CONFLICT (file_id, source_profile_id) DO UPDATE SET
                                        profile_time = EXCLUDED.profile_time,
                                        location = EXCLUDED.location
                                """, (file_id, p['source_profile_id'], p['time'], loc_wkt))
                            else:
                                cur.execute("""
                                    INSERT INTO argo_profiles (file_id, source_profile_id, profile_time, location)
                                    VALUES (%s, %s, %s, NULL)
                                    ON CONFLICT (file_id, source_profile_id) DO UPDATE SET
                                        profile_time = EXCLUDED.profile_time,
                                        location = EXCLUDED.location
                                """, (file_id, p['source_profile_id'], p['time']))
                    conn.commit()
                    
            inserted_files += 1
            inserted_profiles += len(valid_profiles)
            
        except Exception as e:
            failed_files += 1
            print(f"Failed to process {filename}: {e}")

    print(f"\nProcessed: {inserted_files + failed_files}")
    print(f"Inserted files: {inserted_files}")
    print(f"Inserted profiles: {inserted_profiles}")
    print(f"Skipped invalid/null profiles: {skipped_profiles}")
    print(f"Failed files: {failed_files}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    backfill(dry_run=args.dry_run, limit=args.limit)
