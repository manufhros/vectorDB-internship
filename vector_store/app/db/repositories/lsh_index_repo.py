from uuid import UUID

from sqlalchemy.orm import Session

from vector_store.app.db.lsh_index import LSHIndex
from vector_store.app.db.models.lsh_index import LSHIndexModel
from vector_store.app.db.cache import index_cache
import vector_store.app.db.index_factory as IndexFactory
from fastapi import HTTPException
from vector_store.app.constants import EMBEDDING_DIM
from vector_store.app.db.models.chunk import Chunk
from vector_store.app.db.models.library import Library

class LSHIndexRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, library_id: UUID) -> LSHIndex | None:
        index = index_cache.get(library_id)
        if index:
            return index
        row = self.db.query(LSHIndexModel).filter_by(library_id=str(library_id)).first()
        if row:
            index = LSHIndex.from_dict(
                {
                    "dim": row.dim,
                    "num_tables": row.num_tables,
                    "num_hashes": row.num_hashes,
                    "tables": row.tables,
                    "hyperplanes": row.hyperplanes,
                    "vectors": row.vectors,
                }
            )
            index_cache[library_id] = index
            return index
        return None

    def save(self, library_id: UUID, index: LSHIndex):
        existing = (
            self.db.query(LSHIndexModel).filter_by(library_id=str(library_id)).first()
        )
        data = index.to_dict()

        if existing:
            existing.dim = data["dim"]
            existing.num_tables = data["num_tables"]
            existing.num_hashes = data["num_hashes"]
            existing.tables = data["tables"]
            existing.hyperplanes = data["hyperplanes"]
            existing.vectors = data["vectors"]
        else:
            new = LSHIndexModel(
                library_id=str(library_id),
                dim=data["dim"],
                num_tables=data["num_tables"],
                num_hashes=data["num_hashes"],
                tables=data["tables"],
                hyperplanes=data["hyperplanes"],
                vectors=data["vectors"],
            )
            self.db.add(new)
        self.db.commit()
        index_cache[library_id] = index

    def delete(self, library_id: UUID):
        # Remove from the cache
        index_cache.pop(library_id, None)
        self.db.query(LSHIndexModel).filter_by(library_id=str(library_id)).delete()
        self.db.commit()


    def insert(self, library_id: UUID, chunk_id: UUID, embedding: list[float]):
        index = index_cache.get(library_id)
        if not index:
            library = self.library_repo.get(library_id)
            if not library:
                raise HTTPException(status_code=404, detail="Library not found")
            index = self.get(library_id)
            if not index:
                index = IndexFactory.create(library.index_type, dim=EMBEDDING_DIM)
                chunks = self.chunk_repo.list_by_library(library_id)
                for ch in chunks:
                    index.add(ch.id, ch.embedding)
        index.add(chunk_id, embedding)
        index_cache[library_id] = index

        if isinstance(index, LSHIndex):
            self.save(library_id, index)


    def remove(self, library_id: UUID, chunk_id: UUID):
        index = index_cache.get(library_id)
        if index:
            index.remove(chunk_id)
            if isinstance(index, LSHIndex):
                self.save(library_id, index)


    def get_or_create(self, library: Library, chunks: list[Chunk]) -> LSHIndex:
        index = index_cache.get(library.id)
        if index:
            return index

        if library.index_type == "lsh":
            index = self.get(library.id)
            if not index:
                index = IndexFactory.create(index_type="lsh", dim=EMBEDDING_DIM)
                for ch in chunks:
                    index.add(ch.id, ch.embedding)
                self.save(library.id, index)
        else:
            index = IndexFactory.create(index_type=library.index_type)
            for ch in chunks:
                index.add(ch.id, ch.embedding)

        index_cache[library.id] = index
        return index