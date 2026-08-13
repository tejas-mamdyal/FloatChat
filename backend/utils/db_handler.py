import psycopg2
from psycopg2.extras import execute_batch
import json
import os

class PostgresHandler:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "argo"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        self.create_tables()
    
    def create_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS parquet_metadata (
                    id SERIAL PRIMARY KEY,
                    file_path TEXT,
                    chunk_index INTEGER,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
    
    def store_metadata(self, file_path, metadata_list):
        with self.conn.cursor() as cur:
            query = """
                INSERT INTO parquet_metadata (file_path, chunk_index, metadata)
                VALUES (%s, %s, %s)
            """
            data = [
                (meta["file_path"], meta["chunk_index"], json.dumps(meta))
                for meta in metadata_list
            ]
            execute_batch(cur, query, data)
            self.conn.commit()
            print(f"Stored {len(metadata_list)} metadata entries for {file_path}")

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()