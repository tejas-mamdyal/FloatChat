import unittest
import os
import psycopg2
from database.core import init_pool, close_pool, get_db_connection
from database.schema import initialize_schema

class TestDatabasePhase2B(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We assume a local dev PostgreSQL is running and accessible
        os.environ["ENVIRONMENT"] = "development"
        try:
            init_pool()
            cls.db_available = True
            # Setup fresh tables for testing
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DROP TABLE IF EXISTS argo_profiles CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS argo_files CASCADE;")
                conn.commit()
            
            initialize_schema()
        except Exception as e:
            cls.db_available = False
            cls.db_error = str(e)

    @classmethod
    def tearDownClass(cls):
        if cls.db_available:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM argo_profiles;")
                    cur.execute("DELETE FROM argo_files;")
                conn.commit()
            close_pool()

    def setUp(self):
        if not self.db_available:
            self.skipTest(f"Database not available: {self.db_error}")

    def test_schema_initialization(self):
        # Test 2: Schema can be initialized (called in setUpClass)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check tables exist
                cur.execute("SELECT to_regclass('public.argo_files');")
                self.assertIsNotNone(cur.fetchone()[0])
                cur.execute("SELECT to_regclass('public.argo_profiles');")
                self.assertIsNotNone(cur.fetchone()[0])

    def test_insert_file_record(self):
        # Test 3: A file record can be inserted
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO argo_files (file_path, checksum, start_time, end_time)
                    VALUES ('/fake/path.nc', 'checksum123', '2025-01-01 10:00:00', '2025-01-02 10:00:00')
                    RETURNING file_id;
                """)
                file_id = cur.fetchone()[0]
                self.assertIsNotNone(file_id)
            conn.commit()

    def test_duplicate_checksum_rejected(self):
        # Test 4: Duplicate checksum is rejected
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO argo_files (file_path, checksum)
                    VALUES ('/fake/path2.nc', 'checksum_dup')
                """)
                conn.commit()
            
            with self.assertRaises(psycopg2.IntegrityError):
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO argo_files (file_path, checksum)
                        VALUES ('/fake/path3.nc', 'checksum_dup')
                    """)
            conn.rollback()

    def test_insert_profile_with_location(self):
        # Test 5: Profile with PostGIS location
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO argo_files (file_path, checksum) VALUES ('/fake/path4.nc', 'checksum4') RETURNING file_id;")
                file_id = cur.fetchone()[0]
                
                cur.execute("""
                    INSERT INTO argo_profiles (file_id, profile_time, location)
                    VALUES (%s, '2025-01-01 12:00:00', ST_SetSRID(ST_MakePoint(72.8, 18.9), 4326))
                    RETURNING profile_id;
                """, (file_id,))
                profile_id = cur.fetchone()[0]
                self.assertIsNotNone(profile_id)
            conn.commit()

    def test_spatial_query(self):
        # Test 7: Spatial distance query works
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO argo_files (file_path, checksum) VALUES ('/fake/path_spatial.nc', 'checksum_sp') RETURNING file_id;")
                file_id = cur.fetchone()[0]
                
                # Insert profile in Mumbai
                cur.execute("""
                    INSERT INTO argo_profiles (file_id, profile_time, location)
                    VALUES (%s, '2025-01-01 12:00:00', ST_SetSRID(ST_MakePoint(72.8, 18.9), 4326))
                """, (file_id,))
                
                # Query within 50km of Mumbai (ST_DWithin using geography for meters)
                cur.execute("""
                    SELECT count(*) FROM argo_profiles 
                    WHERE ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(72.8, 18.9), 4326)::geography, 50000)
                    AND file_id = %s;
                """, (file_id,))
                count = cur.fetchone()[0]
                self.assertEqual(count, 1)
            conn.commit()

    def test_valid_embedding(self):
        # Test 8: Embedding column accepts 768-d vector
        vec = [0.1] * 768
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO argo_files (file_path, checksum, semantic_embedding)
                    VALUES ('/fake/path_vec.nc', 'checksum_vec', %s)
                    RETURNING file_id;
                """, (vec,))
                file_id = cur.fetchone()[0]
                self.assertIsNotNone(file_id)
            conn.commit()

    def test_invalid_embedding_dimension(self):
        # Test 9: Invalid embedding dimension is rejected
        vec = [0.1] * 384 # MiniLM dim, should be rejected by 768 constraint
        with get_db_connection() as conn:
            with self.assertRaises(psycopg2.errors.DataException): # expected dimensions 768
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO argo_files (file_path, checksum, semantic_embedding)
                        VALUES ('/fake/path_vec_bad.nc', 'checksum_vec_bad', %s)
                    """, (vec,))
            conn.rollback()

if __name__ == '__main__':
    unittest.main()
