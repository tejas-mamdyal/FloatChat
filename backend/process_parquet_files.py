import os
import glob
import sys
import time
import multiprocessing
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import psutil

# Add virtual environment path to system path
venv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv')
if os.path.exists(venv_path):
    sys.path.insert(0, os.path.join(venv_path, 'Lib', 'site-packages'))

from utils.text_processor import extract_text_from_parquet, create_chunks
from utils.embedding_store import FAISSEmbeddingStore


class FastParquetProcessor:
    def __init__(self, batch_size=500, max_threads=8, use_gpu=False):
        self.batch_size = batch_size
        self.max_threads = max_threads
        self.use_gpu = use_gpu
        self.embedding_store = None
        self.processed_chunks = 0
        self.failed_files = []
        self.start_time = time.time()

    def _read_file(self, parquet_file):
        """Reads and extracts chunks from a single parquet file."""
        try:
            text_content = extract_text_from_parquet(parquet_file)
            if not text_content:
                return [], []

            chunks = create_chunks(text_content)
            metadatas = [{"source": parquet_file, "chunk_index": i} for i in range(len(chunks))]
            return chunks, metadatas
        except Exception as e:
            self.failed_files.append((parquet_file, str(e)))
            return [], []

    def _process_batch(self, chunks, metadatas):
        """Bulk inserts into FAISS in one call."""
        if not chunks:
            return
        if self.embedding_store is None:
            self.embedding_store = FAISSEmbeddingStore(use_gpu=self.use_gpu)

        self.embedding_store.add_texts(chunks, metadatas)
        self.processed_chunks += len(chunks)

    def process_files(self, parquet_dir, faiss_index_path):
        os.makedirs(parquet_dir, exist_ok=True)
        os.makedirs(os.path.dirname(faiss_index_path), exist_ok=True)

        parquet_files = glob.glob(os.path.join(parquet_dir, "*.parquet"))
        if not parquet_files:
            print(f"No parquet files found in {parquet_dir}")
            return

        print(f"Found {len(parquet_files)} files. Using {self.max_threads} threads.")
        print(f"Using {'GPU' if self.use_gpu else 'CPU'} for embeddings.")

        all_chunks = []
        all_metadatas = []

        # Step 1: Read files concurrently
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_file = {executor.submit(self._read_file, f): f for f in parquet_files}

            with tqdm(total=len(parquet_files), desc="Reading files") as pbar:
                for future in as_completed(future_to_file):
                    file = future_to_file[future]
                    try:
                        chunks, metadatas = future.result()
                        if chunks:
                            all_chunks.extend(chunks)
                            all_metadatas.extend(metadatas)
                    except Exception as e:
                        self.failed_files.append((file, str(e)))
                    pbar.update(1)

                    # Step 2: Dynamic batch processing to FAISS
                    if len(all_chunks) >= self.batch_size or self._memory_low():
                        self._process_batch(all_chunks, all_metadatas)
                        all_chunks.clear()
                        all_metadatas.clear()

        # Final batch flush
        if all_chunks:
            self._process_batch(all_chunks, all_metadatas)

        # Save final index
        if self.embedding_store:
            print(f"Saving FAISS index with {self.processed_chunks} vectors...")
            self.embedding_store.save(faiss_index_path)

        self._log_results(len(parquet_files))

    def _memory_low(self):
        """Check if system memory is running low to avoid crashes."""
        mem = psutil.virtual_memory()
        return mem.available < 500 * 1024 * 1024  # 500MB

    def _log_results(self, total_files):
        total_time = time.time() - self.start_time
        print("\n" + "=" * 50)
        print(f"Total files: {total_files}")
        print(f"Successfully processed: {total_files - len(self.failed_files)}")
        print(f"Failed: {len(self.failed_files)}")
        print(f"Total chunks processed: {self.processed_chunks}")
        print(f"Time taken: {total_time:.2f}s")
        print(f"Speed: {self.processed_chunks / max(1, total_time):.2f} chunks/sec")

        if self.failed_files:
            print("\nFailed files (top 5):")
            for file, error in self.failed_files[:5]:
                print(f"- {os.path.basename(file)}: {error}")


if __name__ == "__main__":
    parquet_dir = r"c:\SIH\backend\downloads\parquet"
    index_path = r"c:\SIH\backend\vector_store\faiss_index"

    use_gpu = False
    try:
        import torch
        use_gpu = torch.cuda.is_available()
    except ImportError:
        pass

    processor = FastParquetProcessor(batch_size=1000, max_threads=8, use_gpu=use_gpu)
    processor.process_files(parquet_dir, index_path)
