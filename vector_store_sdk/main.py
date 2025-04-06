from vectorstore_client import VectorStoreClient

if __name__ == "__main__":
    client = VectorStoreClient("http://localhost:8080")
    print(client.list_libraries())
