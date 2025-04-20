from vectorstore_client import VectorStoreClient
from vectorstore_client.models.chunk import ChunkCreate
from vectorstore_client.models.document import DocumentCreate
from vectorstore_client.models.library import LibraryCreate
from vectorstore_client.models.query import QueryRequest


def test_end_to_end():
    client = VectorStoreClient("http://localhost:8000")

    # Create a library
    lib = client.create_library(
        LibraryCreate(
            name="SDK Test Library",
            description="Library created during SDK test",
            index_type="lsh",
        )
    )

    assert "id" in lib
    lib_id = lib["id"]

    # Create a document
    doc = client.create_document(lib_id, DocumentCreate(title="SDK Test Document"))
    assert "id" in doc
    doc_id = doc["id"]

    # Add a chunk
    chunk = client.create_chunk(
        doc_id, ChunkCreate(text="Este es un fragmento de prueba")
    )
    assert "id" in chunk
    chunk_id = chunk["id"]

    # Perform a query
    query = QueryRequest(text="fragmento de prueba", k=1)
    results = client.query(lib_id, query)
    for res in results:
        print(f"Chunk ID: {res.chunk_id}, Score: {res.score}")
    assert isinstance(results, list)
    assert any(str(res.chunk_id) == str(chunk_id) for res in results)
