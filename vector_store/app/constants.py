from pathlib import Path

EMBEDDING_DIM = 1024
CHUNKS_LRU_CACHE_SIZE = 1000
LSH_LRU_CACHE_SIZE = 10

# Folder for persistent data
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Path to store LSH index data
LSH_INDEX_FILE = DATA_DIR / "lsh_index.json"
