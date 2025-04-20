import logging
import os
from uuid import UUID

import cohere
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session

from vector_store.app.constants import EMBEDDING_DIM
from vector_store.app.db.repositories.chunk_repo import ChunkRepository
from vector_store.app.db.repositories.document_repo import DocumentRepository
from vector_store.app.db.repositories.library_repo import LibraryRepository
from vector_store.app.db.repositories.lsh_index_repo import LSHIndexRepository
from vector_store.app.models.chunk import ChunkCreate, ChunkUpdate

load_dotenv()
cohere_client = cohere.Client(os.environ["COHERE_API_KEY"])

logger = logging.getLogger(__name__)


class ChunkStoreService:
    """
    Service class for managing chunks in the database and their corresponding
    embeddings in the index.
    """

    def __init__(self, db: Session):
        self.db = db
        self.library_repo = LibraryRepository(db)
        self.document_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.lsh_repo = LSHIndexRepository(db)

    # Chunk Methods
    def create_chunk(self, document_id: UUID, data: ChunkCreate):
        document = self.document_repo.get(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if data.embedding is None:
            data.embedding = self._generate_embedding(data.text)

        if len(data.embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"Embedding must be of length {EMBEDDING_DIM}, got {len(data.embedding)}"
            )

        # Persist the chunk in the database
        chunk = self.chunk_repo.create(document_id, data)

        # Update index with the new chunk
        library = self.library_repo.get(document.library_id)
        if library:
            self._update_index_add(
                library.id, library.index_type, chunk.id, data.embedding
            )

        return chunk

    def get_chunk(self, chunk_id: UUID):
        chunk = self.chunk_repo.get(chunk_id)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        return chunk

    def list_chunks(self):
        return self.chunk_repo.list()

    def list_chunks_by_document(self, document_id: UUID):
        if not self.document_repo.get(document_id):
            raise HTTPException(status_code=404, detail="Document not found")
        return self.chunk_repo.list_by_document(document_id)

    def update_chunk(self, chunk_id: UUID, data: ChunkUpdate):
        # Retrieve existing chunk
        existing_chunk = self.chunk_repo.get(chunk_id)
        if not existing_chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")

        # Detect if the embedding will change
        new_embedding = data.embedding
        embedding_changed = (
            new_embedding is not None and new_embedding != existing_chunk.embedding
        )

        # Perform DB update
        updated_chunk = self.chunk_repo.update(chunk_id, data)

        if embedding_changed:
            # Retrieve related document and library
            document = self.document_repo.get(updated_chunk.document_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")

            library = self.library_repo.get(document.library_id)
            if not library:
                raise HTTPException(status_code=404, detail="Library not found")

            # Update the index
            self._update_index_replace(
                library.id, library.index_type, chunk_id, updated_chunk.embedding
            )

        return updated_chunk

    def delete_chunk(self, chunk_id: UUID):
        chunk = self.chunk_repo.get(chunk_id)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")

        document = self.document_repo.get(chunk.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        library = self.library_repo.get(document.library_id)
        if not library:
            raise HTTPException(status_code=404, detail="Library not found")

        # Remove chunk from index
        self._update_index_remove(library.id, library.index_type, chunk_id)

        return self.chunk_repo.delete(chunk_id)

    # Index management helper methods

    def _update_index_add(
        self, library_id: UUID, index_type: str, chunk_id: UUID, embedding: list[float]
    ):
        """Add a chunk to the index"""
        if index_type == "lsh":
            index = self.lsh_repo.get(library_id)
            if index:
                index.add(chunk_id, embedding)
                self.lsh_repo.save(library_id, index)

    def _update_index_remove(self, library_id: UUID, index_type: str, chunk_id: UUID):
        """Remove a chunk from the index"""
        if index_type == "lsh":
            index = self.lsh_repo.get(library_id)
            if index:
                index.remove(chunk_id)
                self.lsh_repo.save(library_id, index)

    def _update_index_replace(
        self, library_id: UUID, index_type: str, chunk_id: UUID, embedding: list[float]
    ):
        """Replace a chunk in the index"""
        if index_type == "lsh":
            index = self.lsh_repo.get(library_id)
            if index:
                index.remove(chunk_id)
                index.add(chunk_id, embedding)
                self.lsh_repo.save(library_id, index)

    # Embedding helper methods
    def _generate_embedding(self, text: str) -> list[float]:
        try:
            response = cohere_client.embed(
                texts=[text],
                input_type="search_document",
                model="embed-english-v3.0",
            )
            return response.embeddings[0]
        except Exception as err:
            logger.exception("Error generating embedding with Cohere")
            raise HTTPException(
                status_code=500, detail="Failed to generate embedding"
            ) from err
