from uuid import UUID

import pytest

from vectorstore_client import VectorStoreClient
from vectorstore_client.models.chunk import ChunkCreate
from vectorstore_client.models.document import DocumentCreate
from vectorstore_client.models.library import LibraryCreate
from vectorstore_client.models.query import QueryRequest


@pytest.fixture(scope="module")
def client():
    return VectorStoreClient("http://localhost:8080")


def test_sdk_minimal_flow(client):
    # Create a library
    lib = client.create_library(
        LibraryCreate(name="Minimal Test", description="Quick test")
    )
    assert lib["name"] == "Minimal Test"
    lib_id = UUID(lib["id"])

    # Create a document
    doc = client.create_document(
        lib_id,
        DocumentCreate(title="Test Doc", source="test", description="Doc for test"),
    )
    doc_id = UUID(doc["id"])

    # Create a chunk with a fixed embedding (valid 1024D)
    embedding = [0.001 * i for i in range(1024)]
    chunk = client.create_chunk(
        doc_id,
        ChunkCreate(
            text="This is a test chunk for minimal test case.",
            embedding=embedding,
            metadata={"type": "demo"},
        ),
    )
    assert chunk["text"].startswith("This is a test")
    chunk_id = UUID(chunk["id"])

    # Query using the same embedding
    results = client.query(lib_id, QueryRequest(embedding=embedding, k=1))
    assert len(results) == 1
    assert results[0].text.startswith("This is a test")

    # Clean up
    client.delete_chunk(chunk_id)
    client.delete_document(lib_id, doc_id)
    client.delete_library(lib_id)
