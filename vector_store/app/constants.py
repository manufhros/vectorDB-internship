from pathlib import Path

EMBEDDING_DIM = 1024

# Folder for persistent data
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Path to store LSH index data
LSH_INDEX_FILE = DATA_DIR / "lsh_index.json"
