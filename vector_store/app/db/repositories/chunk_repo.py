from uuid import UUID

from sqlalchemy.orm import Session

from vector_store.app.db.models.chunk import Chunk
from vector_store.app.db.models.document import Document
from vector_store.app.models.chunk import ChunkCreate, ChunkUpdate


class ChunkRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, document_id: UUID, data: ChunkCreate) -> Chunk:
        chunk = Chunk(
            document_id=str(document_id),
            text=data.text,
            embedding=data.embedding,
            meta=data.meta or {},
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def get(self, chunk_id: UUID) -> Chunk | None:
        return self.db.query(Chunk).filter_by(id=str(chunk_id)).first()

    def list_by_document(self, document_id: UUID) -> list[Chunk]:
        return self.db.query(Chunk).filter_by(document_id=str(document_id)).all()

    def list_by_library(self, library_id: UUID) -> list[Chunk]:
        return (
            self.db.query(Chunk)
            .join(Document, Chunk.document_id == Document.id)
            .filter(Document.library_id == str(library_id))
            .all()
        )

    def update(self, chunk_id: UUID, data: ChunkUpdate) -> Chunk | None:
        chunk = self.get(chunk_id)
        if not chunk:
            return None

        if data.text is not None:
            chunk.text = data.text
        if data.embedding is not None:
            chunk.embedding = data.embedding
        if data.meta is not None:
            chunk.meta = data.meta

        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def delete(self, chunk_id: UUID) -> bool:
        chunk = self.get(chunk_id)
        if not chunk:
            return False
        self.db.delete(chunk)
        self.db.commit()
        return True
