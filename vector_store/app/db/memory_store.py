import logging
import os
from datetime import datetime, timezone
from uuid import UUID, uuid4

import cohere
from dotenv import load_dotenv
from fastapi import HTTPException

from vector_store.app.constants import EMBEDDING_DIM

# from vector_store.app.db.index import BruteForceIndex
from vector_store.app.db.lsh_index import LSHIndex
from vector_store.app.db.persistence import (
    load_data,
    load_indices,
    save_data,
    save_indices,
)
from vector_store.app.models.chunk import Chunk, ChunkCreate, ChunkUpdate
from vector_store.app.models.document import Document, DocumentCreate, DocumentUpdate
from vector_store.app.models.library import Library, LibraryCreate, LibraryUpdate
from vector_store.app.models.query import QueryRequest, QueryResult

load_dotenv()
cohere_client = cohere.Client(os.environ["COHERE_API_KEY"])

logger = logging.getLogger(__name__)


class InMemoryStore:
    def __init__(self):
        self.libraries, self.documents, self.chunks = load_data()
        self.lsh_indices = load_indices()

    def save(self):
        print("📦 Saving data to disk...")
        save_data(self.libraries, self.documents, self.chunks)
        save_indices(self.lsh_indices)

    # Library Methods
    def create_library(self, data: LibraryCreate) -> Library:
        library_id = uuid4()
        library = Library(
            id=library_id,
            name=data.name,
            description=data.description,
            created_at=datetime.now(timezone.utc),
        )
        self.libraries[library_id] = library
        self.lsh_indices[library_id] = LSHIndex(dim=EMBEDDING_DIM)
        self.save()
        return library

    def get_library(self, library_id: UUID) -> Library | None:
        return self.libraries.get(library_id)

    def list_libraries(self) -> list[Library]:
        return list(self.libraries.values())

    def delete_library(self, library_id: UUID) -> None:
        if library_id not in self.libraries:
            logger.warning(f"Attempted to delete non-existent library {library_id}")
            return
        documents_to_delete = [
            doc.id for doc in self.documents.values() if doc.library_id == library_id
        ]
        for doc_id in documents_to_delete:
            self.delete_document(doc_id)
        self.libraries.pop(library_id)
        self.lsh_indices.pop(library_id, None)

    def update_library(self, library_id: UUID, data: LibraryUpdate) -> Library | None:
        library = self.libraries.get(library_id)
        if not library:
            return None

        updated_data = library.model_dump()
        if data.name is not None:
            updated_data["name"] = data.name
        if data.description is not None:
            updated_data["description"] = data.description

        updated_library = Library(**updated_data)
        self.libraries[library_id] = updated_library
        return updated_library

    # Document Methods
    def create_document(self, library_id: UUID, data: DocumentCreate) -> Document:
        if library_id not in self.libraries:
            raise HTTPException(status_code=404, detail="Library not found")
        document_id = uuid4()
        document = Document(
            title=data.title,
            source=data.source,
            description=data.description,
            id=document_id,
            library_id=library_id,
            created_at=datetime.now(timezone.utc),
        )
        self.documents[document_id] = document
        return document

    def get_document(self, document_id: UUID) -> Document | None:
        return self.documents.get(document_id)

    def list_documents(self) -> list[Document]:
        return list(self.documents.values())

    def list_documents_by_library(self, library_id: UUID) -> list[Document]:
        return [doc for doc in self.documents.values() if doc.library_id == library_id]

    def delete_document(self, document_id: UUID) -> None:
        if document_id not in self.documents:
            logger.warning(f"Attempted to delete non-existent document {document_id}")
            return
        chunks_to_delete = [
            chunk.id
            for chunk in self.chunks.values()
            if chunk.document_id == document_id
        ]
        for chunk_id in chunks_to_delete:
            self.delete_chunk(chunk_id)
        self.documents.pop(document_id)

    def update_document(
        self, document_id: UUID, data: DocumentUpdate
    ) -> Document | None:
        document = self.documents.get(document_id)
        if not document:
            return None

        updated_data = document.model_dump()
        if data.title is not None:
            updated_data["title"] = data.title
        if data.source is not None:
            updated_data["source"] = data.source
        if data.description is not None:
            updated_data["description"] = data.description

        updated_document = Document(**updated_data)
        self.documents[document_id] = updated_document
        return updated_document

    # Chunk Methods
    def create_chunk(self, document_id: UUID, data: ChunkCreate) -> Chunk:
        if document_id not in self.documents:
            raise HTTPException(status_code=404, detail="Document not found")

        document = self.documents[document_id]
        if document.library_id not in self.libraries:
            raise HTTPException(status_code=404, detail="Associated library not found")

        if data.embedding is not None and len(data.embedding) != EMBEDDING_DIM:
            raise HTTPException(
                status_code=400,
                detail=f"Embedding must be of length {EMBEDDING_DIM}, got {len(data.embedding)}",
            )

        embedding = data.embedding
        if embedding is None:
            response = cohere_client.embed(
                texts=[data.text],
                input_type="search_document",
                model="embed-english-v3.0",
            )
            embedding = response.embeddings[0]

        if len(embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"Cohere returned embedding of length {len(embedding)} (expected {EMBEDDING_DIM})"
            )

        chunk_id = uuid4()
        chunk = Chunk(
            text=data.text,
            embedding=embedding,
            metadata=data.metadata or {},
            id=chunk_id,
            document_id=document_id,
            created_at=datetime.now(timezone.utc),
        )
        self.chunks[chunk_id] = chunk

        # Add to the LSH index of the corresponding library
        self.lsh_indices[document.library_id].add(chunk_id, embedding)

        return chunk

    def get_chunk(self, chunk_id: UUID) -> Chunk | None:
        return self.chunks.get(chunk_id)

    def list_chunks(self) -> list[Chunk]:
        return list(self.chunks.values())

    def list_chunks_by_document(self, document_id: UUID) -> list[Chunk]:
        return [
            chunk for chunk in self.chunks.values() if chunk.document_id == document_id
        ]

    def delete_chunk(self, chunk_id: UUID) -> None:
        if chunk_id not in self.chunks:
            logger.warning(f"Attempted to delete non-existent chunk {chunk_id}")
            return
        self.chunks.pop(chunk_id)

    def update_chunk(self, chunk_id: UUID, data: ChunkUpdate) -> Chunk | None:
        chunk = self.chunks.get(chunk_id)
        if not chunk:
            return None

        updated_data = chunk.model_dump()
        if data.text is not None:
            updated_data["text"] = data.text
        if data.embedding is not None:
            updated_data["embedding"] = data.embedding
        if data.metadata is not None:
            updated_data["metadata"] = data.metadata

        updated_chunk = Chunk(**updated_data)
        self.chunks[chunk_id] = updated_chunk
        return updated_chunk

    def query_chunks(self, library_id: UUID, query: QueryRequest) -> list[QueryResult]:
        print("🚨 query_chunks() called!")
        if library_id not in self.libraries:
            raise HTTPException(status_code=404, detail="Library not found")

        logger.info(
            f"🔍 Running query in library {library_id} with vector {query.embedding}"
        )

        index = self.lsh_indices.get(library_id)
        if not index:
            raise HTTPException(
                status_code=500, detail="LSH index not found for library"
            )

        results = index.search(query.embedding, query.k)

        return [
            QueryResult(
                chunk_id=chunk_id,
                document_id=self.chunks[chunk_id].document_id,
                score=min(score, 1.0),
                text=self.chunks[chunk_id].text,
            )
            for chunk_id, score in results
        ]
