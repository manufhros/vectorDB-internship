import pytest
from uuid import UUID
from vectorstore_client import VectorStoreClient
from vectorstore_client.models.library import LibraryCreate, LibraryUpdate
from vectorstore_client.models.document import DocumentCreate, DocumentUpdate
from vectorstore_client.models.chunk import ChunkCreate, ChunkUpdate
from vectorstore_client.models.query import QueryRequest


def test_full_sdk_flow():
    client = VectorStoreClient("http://localhost:8000")

    # Create library
    lib = client.create_library(LibraryCreate(
        name="SDK Test Library",
        description="Testing all SDK functionality",
        index_type="lsh"
    ))
    assert "id" in lib
    lib_id = UUID(lib["id"])

    # Get library
    fetched_lib = client.get_library(lib_id)
    assert fetched_lib["id"] == str(lib_id)

    # Update library
    updated_lib = client.update_library(lib_id, LibraryUpdate(name="Updated Library"))
    assert updated_lib["name"] == "Updated Library"

    # List libraries
    libraries = client.list_libraries()
    assert any(lib["id"] == str(lib_id) for lib in libraries)

    # Create document
    doc = client.create_document(lib_id, DocumentCreate(title="Test Document"))
    doc_id = UUID(doc["id"])

    # Get document
    print("✅ lib_id -> ", lib_id)
    print("✅ doc_id -> ", doc_id)
    fetched_doc = client.get_document(lib_id, doc_id)
    print("✅ fetched_doc ---------------------->", fetched_doc["id"])
    assert str(fetched_doc["id"]) == str(doc_id)

    # Update document
    updated_doc = client.update_document(lib_id, doc_id, DocumentUpdate(title="Updated Document"))
    assert updated_doc["title"] == "Updated Document"

    # List documents
    documents = client.list_documents(lib_id)
    assert any(d["id"] == str(doc_id) for d in documents)

    # Create chunk
    chunk = client.create_chunk(doc_id, ChunkCreate(text="Texto para prueba completa SDK"))
    chunk_id = UUID(chunk["id"])

    # Get chunk
    fetched_chunk = client.get_chunk(chunk_id)
    assert fetched_chunk["id"] == str(chunk_id)

    # Update chunk
    updated_chunk = client.update_chunk(chunk_id, ChunkUpdate(text="Texto actualizado"))
    assert "Texto actualizado" in updated_chunk["text"]

    # List chunks
    chunks = client.list_chunks(doc_id)
    assert any(c["id"] == str(chunk_id) for c in chunks)

    # Query
    results = client.query(lib_id, "Texto actualizado", k=3)
    assert isinstance(results, list)
    assert any(str(res.chunk_id) == str(chunk_id) for res in results)

    # Clean up
    client.delete_chunk(chunk_id)
    client.delete_document(lib_id, doc_id)
    client.delete_library(lib_id)