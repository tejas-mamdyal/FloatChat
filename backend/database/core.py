import os
import logging
from psycopg2 import pool
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_pool = None

def init_pool():
    global _pool
    if _pool is None:
        # Configuration
        db_name = os.getenv("POSTGRES_DB")
        db_user = os.getenv("POSTGRES_USER")
        db_pass = os.getenv("POSTGRES_PASSWORD")
        db_host = os.getenv("POSTGRES_HOST")
        db_port = os.getenv("POSTGRES_PORT")

        env = os.getenv("ENVIRONMENT", "development")

        if env == "development":
            db_name = db_name or "argo"
            db_user = db_user or "postgres"
            db_pass = db_pass or "postgres_dev_only"
            db_host = db_host or "localhost"
            db_port = db_port or "5432"
        else:
            if not all([db_name, db_user, db_pass, db_host, db_port]):
                raise ValueError("Missing database configuration environment variables for production.")

        try:
            _pool = pool.ThreadedConnectionPool(
                1, 20,
                dbname=db_name,
                user=db_user,
                password=db_pass,
                host=db_host,
                port=db_port
            )
            logger.info("Database connection pool created successfully.")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise

def close_pool():
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None

@contextmanager
def get_db_connection():
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    try:
        yield conn
    finally:
        _pool.putconn(conn)
