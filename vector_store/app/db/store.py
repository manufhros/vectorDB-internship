import logging
import os
from uuid import UUID

import cohere
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session

from vector_store.app.constants import EMBEDDING_DIM
from vector_store.app.db.cache import chunk_cache, index_cache
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
            index_cache[library.id] = index
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

        # Remove from caches
        index_cache.pop(library_id, None)

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

    def get_document(self, document_id: UUID):
        doc = self.document_repo.get(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    def list_documents(self):
        return self.document_repo.list()

    def list_documents_by_library(self, library_id: UUID):
        if not self.library_repo.get(library_id):
            raise HTTPException(status_code=404, detail="Library not found")
        return self.document_repo.list_by_library(library_id)

    def update_document(self, document_id: UUID, data: DocumentUpdate):
        if not self.document_repo.get(document_id):
            raise HTTPException(status_code=404, detail="Document not found")
        return self.document_repo.update(document_id, data)

    def delete_document(self, document_id: UUID):
        if not self.document_repo.get(document_id):
            raise HTTPException(status_code=404, detail="Document not found")
        return self.document_repo.delete(document_id)

    # Chunk Methods
    def create_chunk(self, document_id: UUID, data: ChunkCreate):
        # Retrieve the parent document from the database
        document = self.document_repo.get(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Validate the embedding length if provided manually
        if data.embedding is not None and len(data.embedding) != EMBEDDING_DIM:
            raise HTTPException(
                status_code=400,
                detail=f"Embedding must be of length {EMBEDDING_DIM}, got {len(data.embedding)}",
            )

        embedding = data.embedding

        # If no embedding is provided, generate it using Cohere
        if embedding is None:
            try:
                response = cohere_client.embed(
                    texts=[data.text],
                    input_type="search_document",
                    model="embed-english-v3.0",
                )
                embedding = response.embeddings[0]
            except Exception as err:
                logger.exception("Error generating embedding with Cohere")
                raise HTTPException(
                    status_code=500, detail="Failed to generate embedding"
                ) from err

        # Double-check the embedding size even if generated by Cohere
        if len(embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"Cohere returned embedding of length {len(embedding)} (expected {EMBEDDING_DIM})"
            )

        # Save the embedding in the chunk object
        data.embedding = embedding

        # Persist the chunk in the database
        chunk = self.chunk_repo.create(document_id, data)

        # Cache the chunk in memory
        chunk_cache[chunk.id] = chunk

        # Try to retrieve the index from memory
        index = index_cache.get(document.library_id)

        # If not in cache, try to load it or create a new one
        if not index:
            # If the library uses LSH indexing, try to load the persisted index from the database
            library = self.library_repo.get(document.library_id)
            if not library:
                raise HTTPException(status_code=404, detail="Library not found")
            if library.index_type == "lsh":
                index = self.lsh_repo.get(document.library_id)

                # If it doesn't exist yet, create a new empty LSH index
                if not index:
                    index = IndexFactory.create(index_type="lsh", dim=EMBEDDING_DIM)
            else:
                # For BruteForce (or other in-memory) indices, just create a new one on the fly
                index = IndexFactory.create(index_type=library.index_type)

            # Populate the index with all existing chunks in the library
            chunks = self.chunk_repo.list_by_library(document.library_id)
            for ch in chunks:
                index.add(ch.id, ch.embedding)

        index_cache[document.library_id] = index

        # Add the new chunk to the index
        index.add(chunk.id, chunk.embedding)

        # If LSH, persist the updated index
        if isinstance(index, LSHIndex):
            self.lsh_repo.save(document.library_id, index)

        return chunk

    def get_chunk(self, chunk_id: UUID):
        if chunk_id in chunk_cache:
            return chunk_cache[chunk_id]
        chunk = self.chunk_repo.get(chunk_id)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        chunk_cache[chunk_id] = chunk
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

        # Update the chunk cache
        chunk_cache[chunk_id] = updated_chunk

        if embedding_changed:
            # Retrieve related document and library
            document = self.document_repo.get(updated_chunk.document_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")

            library = self.library_repo.get(document.library_id)
            if not library:
                raise HTTPException(status_code=404, detail="Library not found")

            # Retrieve the index from cache (or build it if missing)
            index = index_cache.get(library.id)
            if not index:
                if library.index_type == "lsh":
                    index = self.lsh_repo.get(library.id)
                    if not index:
                        index = IndexFactory.create(index_type="lsh", dim=EMBEDDING_DIM)
                else:
                    index = IndexFactory.create(index_type=library.index_type)

                chunks = self.chunk_repo.list_by_library(library.id)
                for ch in chunks:
                    index.add(ch.id, ch.embedding)
                index_cache[library.id] = index

            # Remove old embedding and add the new one
            index.remove(chunk_id)
            index.add(chunk_id, updated_chunk.embedding)

            # Persist index if it's LSH
            if isinstance(index, LSHIndex):
                self.lsh_repo.save(library.id, index)

        return updated_chunk

    def delete_chunk(self, chunk_id: UUID):
        chunk = self.chunk_repo.get(chunk_id)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")

        document = self.document_repo.get(chunk.document_id)
        library = self.library_repo.get(document.library_id)

        index = index_cache.get(library.id)
        if index:
            index.remove(chunk.id)
            if isinstance(index, LSHIndex):
                self.lsh_repo.save(library.id, index)

        chunk_cache.pop(chunk.id, None)
        return self.chunk_repo.delete(chunk_id)

    # Query
    def query_chunks(self, library_id: UUID, query: QueryRequest) -> list[QueryResult]:
        # 1. Verifies if the library exists
        library = self.library_repo.get(library_id)
        if not library:
            raise HTTPException(status_code=404, detail="Library not found")

        # 2. Reuses the index if it exists
        index = index_cache.get(library_id)

        if index is None:
            if library.index_type == "lsh":
                # Try to load the LSH index from persistent storage
                index = self.lsh_repo.get(library_id)

                if not index:
                    # If not persisted, create a new LSH index
                    index = IndexFactory.create(index_type="lsh", dim=EMBEDDING_DIM)

                    # Populate it from DB
                    chunks = self.chunk_repo.list_by_library(library_id)
                    for chunk in chunks:
                        index.add(chunk.id, chunk.embedding)

                    # Save to persistent repo
                    self.lsh_repo.save(library_id, index)
            else:
                # Create in-memory BruteForce index
                index = IndexFactory.create(index_type=library.index_type)

                # Populate it from DB
                chunks = self.chunk_repo.list_by_library(library_id)
                for chunk in chunks:
                    index.add(chunk.id, chunk.embedding)

            # Cache the index
            index_cache[library_id] = index

        # 3. Generate embedding if not provided
        embedding = query.embedding
        if embedding is None:
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
                embedding = response.embeddings[0]
            except Exception as err:
                logger.exception("Error generating embedding with Cohere")
                raise HTTPException(
                    status_code=500, detail="Failed to generate embedding"
                ) from err

        # 4. Validate embedding dimensionality
        if len(embedding) != EMBEDDING_DIM:
            raise HTTPException(
                status_code=400,
                detail=f"Embedding must have dimension {EMBEDDING_DIM}, but got {len(embedding)}",
            )

        # 5. Executes the query
        try:
            results = index.search(embedding, query.k)

            # Fallback to BruteForce if LSH returns no results
            if not results and isinstance(index, LSHIndex):
                brute = IndexFactory.create("bruteforce")
                chunks = self.chunk_repo.list_by_library(library_id)
                for c in chunks:
                    brute.add(c.id, c.embedding)
                results = brute.search(embedding, query.k)

        except ValueError as err:
            raise HTTPException(
                status_code=400, detail=f"Error during similarity search: {str(err)}"
            ) from err

        # 6. Restores the chunks from the database
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
