from vector_store_sdk.vectorstore_client import VectorStoreClient
from vector_store_sdk.vectorstore_client.models.chunk import ChunkCreate
from vector_store_sdk.vectorstore_client.models.document import DocumentCreate
from vector_store_sdk.vectorstore_client.models.library import LibraryCreate
from vector_store_sdk.vectorstore_client.models.query import QueryRequest

BASE_URL = "http://localhost:8000"


def test_sdk_full_flow():
    client = VectorStoreClient(base_url=BASE_URL)

    # Create library
    library = client.create_library(
        LibraryCreate(name="sdk_library", description="SDK test", index_type="lsh")
    )
    assert library["name"] == "sdk_library"
    lib_id = library["id"]

    # Create document
    doc = client.create_document(
        library_id=lib_id, data=DocumentCreate(title="SDK Doc", source="SDK")
    )
    doc_id = doc["id"]

    # Create chunk
    chunk = client.create_chunk(
        document_id=doc_id, data=ChunkCreate(text="chunk for sdk test")
    )
    assert chunk["document_id"] == doc_id

    # Query
    results = client.query(
        library_id=lib_id,
        query=QueryRequest(embedding=chunk["embedding"], k=1),
    )

    print("✅ Created chunk:", chunk["id"])
    print("🔍 Query results:", results)
    print("📌 First result chunk_id:", results[0].chunk_id)
    assert str(results[0].chunk_id) == chunk["id"]


if __name__ == "__main__":
    test_sdk_full_flow()
    print("✅ SDK test passed.")
