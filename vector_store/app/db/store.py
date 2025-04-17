import logging
import os
from uuid import UUID

import cohere
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session

from vector_store.app.constants import EMBEDDING_DIM
from vector_store.app.db.index_factory import IndexFactory
from vector_store.app.db.lsh_index import LSHIndex
from vector_store.app.db.repositories.chunk_repo import ChunkRepository
from vector_store.app.db.repositories.document_repo import DocumentRepository
from vector_store.app.db.repositories.library_repo import LibraryRepository
from vector_store.app.db.repositories.lsh_index_repo import LSHIndexRepository
from vector_store.app.models.chunk import ChunkCreate, ChunkUpdate
from vector_store.app.models.document import DocumentCreate, DocumentUpdate
from vector_store.app.models.library import LibraryCreate, LibraryUpdate
from vector_store.app.models.query import QueryRequest, QueryResult

load_dotenv()
cohere_client = cohere.Client(os.environ["COHERE_API_KEY"])

logger = logging.getLogger(__name__)


class Store:
    def __init__(self, db: Session):
        self.db = db
        self.library_repo = LibraryRepository(db)
        self.document_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.lsh_repo = LSHIndexRepository(db)

    # Library Methods
    def create_library(self, data: LibraryCreate):
        # Create the library in the database
        library = self.library_repo.create(data)

        # If the index type is LSH, create the index and persist it
        if data.index_type == "lsh":
            index = LSHIndex(dim=EMBEDDING_DIM)
            self.lsh_repo.save(library.id, index)

        return library

    def get_library(self, library_id: UUID):
        return self.library_repo.get(library_id)

    def list_libraries(self):
        return self.library_repo.list()

    def delete_library(self, library_id: UUID):
        library = self.library_repo.get(library_id)
        if not library:
            raise HTTPException(status_code=404, detail="Library not found")

        # Delete persistent index if LSH
        if library.index_type == "lsh":
            self.lsh_repo.delete(library_id)

        return self.library_repo.delete(library_id)

    def update_library(self, library_id: UUID, data: LibraryUpdate):
        if not self.library_repo.get(library_id):
            raise HTTPException(status_code=404, detail="Library not found")
        return self.library_repo.update(library_id, data)

    # Document Methods
    def create_document(self, library_id: UUID, data: DocumentCreate):
        if not self.library_repo.get(library_id):
            raise HTTPException(status_code=404, detail="Library not found")
        return self.document_repo.create(library_id, data)

    def get_document(self, document_id: UUID, library_id: UUID):
        doc = self.document_repo.get(document_id, library_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found in this library")
        return doc

    def list_documents(self):
        return self.document_repo.list()

    def list_documents_by_library(self, library_id: UUID):
        if not self.library_repo.get(library_id):
            raise HTTPException(status_code=404, detail="Library not found")
        return self.document_repo.list_by_library(library_id)

    def update_document(self, document_id: UUID, data: DocumentUpdate):
        document = self.document_repo.get(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return self.document_repo.update(document_id, data, document.library_id)

    def delete_document(self, document_id: UUID):
        if not self.document_repo.get(document_id):
            raise HTTPException(status_code=404, detail="Document not found")
        return self.document_repo.delete(document_id)

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

            # Retrieve or rebuild index
            index = self.lsh_repo.get(library.id)
            if not index:
                index = self._build_index_from_chunks(library)

            # Update index with new embedding
            index.remove(chunk_id)
            index.add(chunk_id, updated_chunk.embedding)

            # Persist updated LSH index
            if isinstance(index, LSHIndex):
                self.lsh_repo.save(library.id, index)

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

        # Manage index removal (also cache)
        self.lsh_repo.remove(library.id, chunk.id)

        return self.chunk_repo.delete(chunk_id)

    # Query
    def query_chunks(self, library_id: UUID, query: QueryRequest) -> list[QueryResult]:
        # 1. Get the library or raise a 404 if it does not exist
        library = self.library_repo.get(library_id)
        if not library:
            raise HTTPException(status_code=404, detail="Library not found")
        # 2. Retrieve all chunks for the library
        chunks = self.chunk_repo.list_by_library(library_id)
        # 3. Load or create the index (LSH or brute force) depending on the library configuration
        index = (
            self.lsh_repo.get_or_create(library, chunks)
            if library.index_type == "lsh"
            else self._build_index_from_chunks(library, chunks)
        )
        # 4. Use the provided embedding or generate one from text
        embedding = query.embedding or self._generate_query_embedding(query)
        # 5. Validate that the embedding has the correct dimensionality
        if len(embedding) != EMBEDDING_DIM:
            raise HTTPException(
                status_code=400,
                detail=f"Embedding must have dimension {EMBEDDING_DIM}, but got {len(embedding)}",
            )
        # 6. Perform the similarity search
        try:
            results = index.search(embedding, query.k)
            # 6a. If no results and using LSH, fallback to brute force
            if not results and isinstance(index, LSHIndex):
                results = self._fallback_bruteforce(chunks, embedding, query.k)
        except ValueError as err:
            raise HTTPException(
                status_code=400, detail=f"Error during similarity search: {str(err)}"
            ) from err
        # 7. Build and return the final query result list
        return self._build_query_results(results)


    # Helper method to generate embedding using Cohere
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

    def _build_query_results(self, results: list[tuple[UUID, float]]) -> list[QueryResult]:
        output = []
        for chunk_id, score in results:
            chunk = self.get_chunk(chunk_id)
            if not chunk:
                continue
            output.append(
                QueryResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    score=min(score, 1.0),
                    text=chunk.text,
                    meta=chunk.meta,
                )
            )
        return output

    def _fallback_bruteforce(self, chunks, embedding, k) -> list[tuple[UUID, float]]:
        brute = IndexFactory.create("bruteforce")
        for c in chunks:
            brute.add(c.id, c.embedding)
        return brute.search(embedding, k)

    def _generate_query_embedding(self, query: QueryRequest) -> list[float]:
        if not query.text:
            raise HTTPException(
                status_code=400,
                detail="Either 'embedding' or 'text' must be provided",
            )
        try:
            response = cohere_client.embed(
                texts=[query.text],
                input_type="search_query",
                model="embed-english-v3.0",
            )
            return response.embeddings[0]
        except Exception as err:
            logger.exception("Error generating embedding with Cohere")
            raise HTTPException(
                status_code=500, detail="Failed to generate embedding"
            ) from err

    def _build_index_from_chunks(self, library):
        if library.index_type == "lsh":
            index = self.lsh_repo.get(library.id)
            if not index:
                index = IndexFactory.create(index_type="lsh", dim=EMBEDDING_DIM)
        else:
            index = IndexFactory.create(index_type=library.index_type)

        chunks = self.chunk_repo.list_by_library(library.id)
        for ch in chunks:
            index.add(ch.id, ch.embedding)

        return index
