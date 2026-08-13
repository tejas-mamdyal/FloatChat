import logging
from psycopg2 import DatabaseError
from database.core import get_db_connection

logger = logging.getLogger(__name__)

def initialize_schema():
    """
    Safely initialize the Phase 2B database schema.
    This does NOT drop or alter existing tables like netcdf_files.
    """
    schema_sql = """
    -- Ensure extensions are enabled
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Phase 2B Schema
    CREATE TABLE IF NOT EXISTS argo_files (
        file_id SERIAL PRIMARY KEY,
        file_path TEXT UNIQUE NOT NULL,
        checksum TEXT UNIQUE NOT NULL,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        trajectory_bbox GEOMETRY(Polygon, 4326),
        semantic_embedding VECTOR(768),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS argo_profiles (
        profile_id SERIAL PRIMARY KEY,
        file_id INTEGER REFERENCES argo_files(file_id) ON DELETE CASCADE,
        source_profile_id INTEGER NOT NULL,
        profile_time TIMESTAMP,
        location GEOMETRY(Point, 4326),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (file_id, source_profile_id)
    );

    -- Spatial and Temporal Indexes
    CREATE INDEX IF NOT EXISTS idx_argo_files_time ON argo_files(start_time, end_time);
    CREATE INDEX IF NOT EXISTS idx_argo_profiles_time ON argo_profiles(profile_time);
    CREATE INDEX IF NOT EXISTS idx_argo_profiles_location ON argo_profiles USING GIST (location);
    """
    
    # We do NOT create the HNSW index on `semantic_embedding` here.
    # It is recommended to create the HNSW index *after* backfilling data
    # to avoid sub-optimal graph construction and slow inserts during backfill.
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()
        logger.info("Phase 2B Database schema initialized successfully.")
    except DatabaseError as e:
        logger.error(f"Schema initialization failed: {e}")
        raise
