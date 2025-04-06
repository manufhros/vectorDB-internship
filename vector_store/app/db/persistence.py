import json
from uuid import UUID

from vector_store.app.constants import DATA_DIR, LSH_INDEX_FILE
from vector_store.app.db.lsh_index import LSHIndex
from vector_store.app.models.chunk import Chunk
from vector_store.app.models.document import Document
from vector_store.app.models.library import Library


# DB Data Persistence
def save_data(libraries, documents, chunks):
    with open(DATA_DIR / "libraries.json", "w") as f:
        json.dump(
            [lib.model_dump(mode="json") for lib in libraries.values()],
            f,
            indent=2,
        )

    with open(DATA_DIR / "documents.json", "w") as f:
        json.dump(
            [doc.model_dump(mode="json") for doc in documents.values()],
            f,
            indent=2,
        )

    with open(DATA_DIR / "chunks.json", "w") as f:
        json.dump(
            [chunk.model_dump(mode="json") for chunk in chunks.values()],
            f,
            indent=2,
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


# LSH Index Persistence
def save_indices(indices: dict[UUID, object]) -> None:
    """Saves persistent LSH indexes to disk."""
    serializable = {
        str(lib_id): index.to_dict()
        for lib_id, index in indices.items()
        if isinstance(index, LSHIndex)
    }
    with open(LSH_INDEX_FILE, "w") as f:
        json.dump(serializable, f)


def load_lsh() -> dict[UUID, LSHIndex]:
    """Loads all persisted LSH indexes from disk."""
    if not LSH_INDEX_FILE.exists():
        return {}
    with open(LSH_INDEX_FILE) as f:
        raw = json.load(f)
    return {UUID(lib_id): LSHIndex.from_dict(data) for lib_id, data in raw.items()}
