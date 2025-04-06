import json
import os
import pickle
from pathlib import Path
from uuid import UUID

from vector_store.app.db.lsh_index import LSHIndex
from vector_store.app.models.chunk import Chunk
from vector_store.app.models.document import Document
from vector_store.app.models.library import Library

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
LSH_INDEX_PATH = "data/lsh_indices.pkl"


# DB Data Persistance
def save_data(libraries, documents, chunks):
    with open(DATA_DIR / "libraries.json", "w") as f:
        json.dump(
            [lib.model_dump(mode="json") for lib in libraries.values()], f, indent=2
        )

    with open(DATA_DIR / "documents.json", "w") as f:
        json.dump(
            [doc.model_dump(mode="json") for doc in documents.values()], f, indent=2
        )

    with open(DATA_DIR / "chunks.json", "w") as f:
        json.dump(
            [chunk.model_dump(mode="json") for chunk in chunks.values()], f, indent=2
        )


def load_data():
    def load_json(path):
        return json.load(open(path)) if path.exists() else []

    libraries = {
        UUID(lib["id"]): Library(**lib)
        for lib in load_json(DATA_DIR / "libraries.json")
    }
    documents = {
        UUID(doc["id"]): Document(**doc)
        for doc in load_json(DATA_DIR / "documents.json")
    }
    chunks = {
        UUID(chk["id"]): Chunk(**chk) for chk in load_json(DATA_DIR / "chunks.json")
    }

    return libraries, documents, chunks


# LSH Index Persistance
def save_indices(indices: dict[UUID, LSHIndex]) -> None:
    with open(LSH_INDEX_PATH, "wb") as f:
        pickle.dump(indices, f)


def load_indices() -> dict[UUID, LSHIndex]:
    if not os.path.exists(LSH_INDEX_PATH):
        return {}
    with open(LSH_INDEX_PATH, "rb") as f:
        return pickle.load(f)
