from uuid import UUID

import requests
from vector_store_sdk.vectorstore_client.constants import EMBEDDING_DIM
from vector_store_sdk.vectorstore_client.models.chunk import ChunkCreate, ChunkUpdate
from vector_store_sdk.vectorstore_client.models.document import (
    DocumentCreate,
    DocumentUpdate,
)
from vector_store_sdk.vectorstore_client.models.library import (
    LibraryCreate,
    LibraryUpdate,
)
from vector_store_sdk.vectorstore_client.models.query import QueryRequest, QueryResult


class VectorStoreClient:
    """
    A Python SDK client for interacting with the Vector Store API.

    Example usage:

        from vectorstore_client import VectorStoreClient
        from app.models.library import LibraryCreate
        from uuid import UUID

        client = VectorStoreClient("http://localhost:8000")
        library = client.create_library(LibraryCreate(name="Demo", description="Example library"))
        print(library)
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    # Libraries
    def create_library(self, data: LibraryCreate) -> dict:
        response = requests.post(f"{self.base_url}/libraries/", json=data.model_dump())
        response.raise_for_status()
        return response.json()

    def get_library(self, library_id: UUID) -> dict:
        response = requests.get(f"{self.base_url}/libraries/{library_id}")
        response.raise_for_status()
        return response.json()

    def list_libraries(self) -> list[dict]:
        response = requests.get(f"{self.base_url}/libraries/")
        response.raise_for_status()
        return response.json()

    def update_library(self, library_id: UUID, data: LibraryUpdate) -> dict:
        response = requests.put(
            f"{self.base_url}/libraries/{library_id}", json=data.model_dump()
        )
        response.raise_for_status()
        return response.json()

    def delete_library(self, library_id: UUID) -> None:
        response = requests.delete(f"{self.base_url}/libraries/{library_id}")
        response.raise_for_status()

    # Documents
    def create_document(self, library_id: UUID, data: DocumentCreate) -> dict:
        response = requests.post(
            f"{self.base_url}/libraries/{library_id}/documents/", json=data.model_dump()
        )
        response.raise_for_status()
        return response.json()

    def get_document(self, library_id: UUID, document_id: UUID) -> dict:
        response = requests.get(
            f"{self.base_url}/libraries/{library_id}/documents/{document_id}"
        )
        response.raise_for_status()
        return response.json()

    def list_documents(self, library_id: UUID) -> list[dict]:
        response = requests.get(f"{self.base_url}/libraries/{library_id}/documents/")
        response.raise_for_status()
        return response.json()

    def update_document(
        self, library_id: UUID, document_id: UUID, data: DocumentUpdate
    ) -> dict:
        response = requests.put(
            f"{self.base_url}/libraries/{library_id}/documents/{document_id}",
            json=data.model_dump(),
        )
        response.raise_for_status()
        return response.json()

    def delete_document(self, library_id: UUID, document_id: UUID) -> None:
        response = requests.delete(
            f"{self.base_url}/libraries/{library_id}/documents/{document_id}"
        )
        response.raise_for_status()

    # Chunks
    def create_chunk(self, document_id: UUID, data: ChunkCreate) -> dict:
        if data.embedding is not None and len(data.embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"Embedding must have {EMBEDDING_DIM} dimensions, got {len(data.embedding)}"
            )

        response = requests.post(
            f"{self.base_url}/documents/{document_id}/chunks/", json=data.model_dump()
        )
        response.raise_for_status()
        return response.json()

    def get_chunk(self, chunk_id: UUID) -> dict:
        response = requests.get(f"{self.base_url}/chunks/{chunk_id}")
        response.raise_for_status()
        return response.json()

    def list_chunks(self, document_id: UUID) -> list[dict]:
        response = requests.get(f"{self.base_url}/documents/{document_id}/chunks/")
        response.raise_for_status()
        return response.json()

    def update_chunk(self, chunk_id: UUID, data: ChunkUpdate) -> dict:
        response = requests.put(
            f"{self.base_url}/chunks/{chunk_id}", json=data.model_dump()
        )
        response.raise_for_status()
        return response.json()

    def delete_chunk(self, chunk_id: UUID) -> None:
        response = requests.delete(f"{self.base_url}/chunks/{chunk_id}")
        response.raise_for_status()

    # Query
    def query(self, library_id: UUID, query: QueryRequest) -> list[QueryResult]:
        response = requests.post(
            f"{self.base_url}/libraries/{library_id}/query/", json=query.model_dump()
        )
        response.raise_for_status()
        return [QueryResult(**r) for r in response.json()]
