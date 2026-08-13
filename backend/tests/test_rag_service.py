import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from services.rag_service import RAGService
import os

class TestRAGService(unittest.TestCase):
    def setUp(self):
        self.config = {"data": {"download_dir": "/fake/dir"}}
        self.service = RAGService(self.config)

    @patch("services.rag_service.os.path.exists")
    @patch("services.rag_service.faiss.read_index")
    @patch("services.rag_service.np.load")
    @patch("services.rag_service.SentenceTransformer")
    def test_load_success(self, mock_st, mock_np_load, mock_faiss, mock_exists):
        mock_exists.return_value = True
        mock_index = MagicMock()
        mock_index.d = 768
        mock_index.ntotal = 2
        mock_faiss.return_value = mock_index
        mock_np_load.return_value = np.array(["file1.nc", "file2.nc"])

        self.service.load()
        self.assertIsNotNone(self.service.model)
        self.assertIsNotNone(self.service.index)

    @patch("services.rag_service.os.path.exists")
    @patch("services.rag_service.faiss.read_index")
    @patch("services.rag_service.np.load")
    @patch("services.rag_service.SentenceTransformer")
    def test_dimension_mismatch(self, mock_st, mock_np_load, mock_faiss, mock_exists):
        mock_exists.return_value = True
        mock_index = MagicMock()
        mock_index.d = 384  # Wrong dimension
        mock_index.ntotal = 2
        mock_faiss.return_value = mock_index
        mock_np_load.return_value = np.array(["file1.nc", "file2.nc"])

        with self.assertRaises(ValueError) as context:
            self.service.load()
        self.assertIn("FAISS index dimension mismatch", str(context.exception))

    @patch("services.rag_service.os.path.exists")
    @patch("services.rag_service.faiss.read_index")
    @patch("services.rag_service.np.load")
    @patch("services.rag_service.SentenceTransformer")
    def test_metadata_mismatch(self, mock_st, mock_np_load, mock_faiss, mock_exists):
        mock_exists.return_value = True
        mock_index = MagicMock()
        mock_index.d = 768
        mock_index.ntotal = 5 # Mismatch
        mock_faiss.return_value = mock_index
        mock_np_load.return_value = np.array(["file1.nc", "file2.nc"])

        with self.assertRaises(ValueError) as context:
            self.service.load()
        self.assertIn("FAISS metadata mismatch", str(context.exception))

    @patch("services.rag_service.os.path.exists")
    def test_missing_index(self, mock_exists):
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.service.load()

    def test_empty_query(self):
        self.service.model = MagicMock()
        self.service.index = MagicMock()
        with self.assertRaises(ValueError):
            self.service.search("", top_k=5)

    @patch("services.rag_service.os.path.exists")
    def test_query_retrieval(self, mock_exists):
        # mock paths
        mock_exists.return_value = False
        
        # mock service state
        self.service.model = MagicMock()
        self.service.model.encode.return_value = np.zeros(768)
        
        self.service.index = MagicMock()
        self.service.index.search.return_value = (np.array([[0.9, 0.8]]), np.array([[0, 1]]))
        self.service.files = np.array(["path1.nc", "path2.nc"])
        
        results = self.service.search("ocean", top_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["source_netcdf"], "path1.nc")
        self.assertEqual(results[1]["source_netcdf"], "path2.nc")

if __name__ == '__main__':
    unittest.main()
