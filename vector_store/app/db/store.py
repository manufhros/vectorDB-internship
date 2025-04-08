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
from vector_store.app.db.repositories.chunk_repo import ChunkRepository
from vector_store.app.db.repositories.document_repo import DocumentRepository
from vector_store.app.db.repositories.library_repo import LibraryRepository
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

    # Library Methods
    def create_library(self, data: LibraryCreate):
        return self.library_repo.create(
            name=data.name,
            description=data.description,
            index_type=data.index_type,
        )

    def get_library(self, library_id: UUID):
        return self.library_repo.get(library_id)

    def list_libraries(self):
        return self.library_repo.list()

    def delete_library(self, library_id: UUID):
        library = self.library_repo.get(library_id)
        if not library:
            raise HTTPException(status_code=404, detail="Library not found")
        return self.library_repo.delete(library_id)

    def update_library(self, library_id: UUID, data: LibraryUpdate):
        if not self.library_repo.get(library_id):
            raise HTTPException(status_code=404, detail="Library not found")
        return self.library_repo.update(
            library_id,
            name=data.name,
            description=data.description,
        )

    # Document Methods
    def create_document(self, library_id: UUID, data: DocumentCreate):
        if not self.library_repo.get(library_id):
            raise HTTPException(status_code=404, detail="Library not found")
        return self.document_repo.create(
            library_id=library_id,
            title=data.title,
            source=data.source,
            description=data.description,
        )

    def get_document(self, document_id: UUID):
        doc = self.document_repo.get(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    def list_documents(self):
        return self.document_repo.list()

    def update_document(self, document_id: UUID, data: DocumentUpdate):
        if not self.document_repo.get(document_id):
            raise HTTPException(status_code=404, detail="Document not found")
        return self.document_repo.update(
            document_id,
            library_id=data.library_id,
            title=data.title,
            source=data.source,
            description=data.description,
        )

    def delete_document(self, document_id: UUID):
        if not self.document_repo.get(document_id):
            raise HTTPException(status_code=404, detail="Document not found")
        return self.document_repo.delete(document_id)

    # Chunk Methods
    def create_chunk(self, document_id: UUID, data: ChunkCreate):
        document = self.document_repo.get(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if data.embedding is not None and len(data.embedding) != EMBEDDING_DIM:
            raise HTTPException(
                status_code=400,
                detail=f"Embedding must be of length {EMBEDDING_DIM}, got {len(data.embedding)}",
            )

        embedding = data.embedding
        if embedding is None:
            try:
                response = cohere_client.embed(
                    texts=[data.text],
                    input_type="search_document",
                    model="embed-english-v3.0",
                )
                embedding = response.embeddings[0]
            except Exception:
                logger.exception("Error generating embedding with Cohere")
                raise HTTPException(
                    status_code=500, detail="Failed to generate embedding"
                )

        if len(embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"Cohere returned embedding of length {len(embedding)} (expected {EMBEDDING_DIM})"
            )

        chunk = self.chunk_repo.create(
            document_id=document_id,
            text=data.text,
            embedding=embedding,
            metadata=data.metadata,
        )
        chunk_cache[chunk.id] = chunk
        index = index_cache.get(document.library_id)
        if index:
            index.add(chunk.id, chunk.embedding)
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
        if not self.chunk_repo.get(chunk_id):
            raise HTTPException(status_code=404, detail="Chunk not found")
        return self.chunk_repo.update(
            chunk_id,
            text=data.text,
            embedding=data.embedding,
            metadata=data.metadata,
        )

    def delete_chunk(self, chunk_id: UUID):
        chunk = self.chunk_repo.get(chunk_id)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        document = self.document_repo.get(chunk.document_id)
        index_cache.pop(document.library_id, None)
        return self.chunk_repo.delete(chunk_id)

    # Query
    def query_chunks(self, library_id: UUID, query: QueryRequest) -> list[QueryResult]:

        # 1. Verifies if the library exists
        library = self.library_repo.get(library_id)
        if not library:
            raise HTTPException(status_code=404, detail="Library not found")

        # 2. Reuses the index if it exists
        index: Index = index_cache.get(library_id)
        if index is None:
            # 2a. Creates a new index
            index = IndexFactory.create(index_type=library.index_type)
            # 2b. Restores the index from the database
            chunks = self.chunk_repo.list_by_library(library_id)
            # 2c. Inserts the chunks into the index
            for chunk in chunks:
                index.add(chunk.id, chunk.embedding)
            # 2d. Caches
            index_cache[library_id] = index

        # 3. Executes the query
        results = index.search(query.embedding, query.k)

        # 4. Restores the chunks from the database
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
                    metadata=chunk.metadata,
                )
            )

        return output
