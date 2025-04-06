from uuid import UUID

from vectorstore_client import VectorStoreClient
from vectorstore_client.models.chunk import ChunkCreate
from vectorstore_client.models.document import DocumentCreate
from vectorstore_client.models.library import LibraryCreate
from vectorstore_client.models.query import QueryRequest


def main():
    client = VectorStoreClient("http://localhost:8080")

    print("🚀 Creating library...")
    lib = client.create_library(
        LibraryCreate(name="Manual Library", description="Testing manually")
    )
    print("✅ Library created:", lib)
    lib_id = UUID(lib["id"])

    print("📄 Creating document...")
    doc = client.create_document(
        lib_id,
        DocumentCreate(
            title="Doc Title", source="manual", description="Created via script"
        ),
    )
    print("✅ Document created:", doc)
    doc_id = UUID(doc["id"])

    print("🔖 Creating chunk with 1024D embedding...")
    embedding = [0.001 * i for i in range(1024)]
    chunk = client.create_chunk(
        doc_id,
        ChunkCreate(
            text="Chunk content for test.",
            embedding=embedding,
            metadata={"category": "demo"},
        ),
    )
    print("✅ Chunk created:", chunk)

    print("🔍 Performing query...")
    results = client.query(lib_id, QueryRequest(embedding=embedding, k=1))
    print("➡️ Query results:", results)


if __name__ == "__main__":
    main()
