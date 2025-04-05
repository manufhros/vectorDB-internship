# Vector Store Python SDK

A lightweight Python SDK to interact with the Vector Store REST API. This client simplifies the integration and management of vector libraries, documents, chunks, and similarity queries.

---

## 🚀 Installation

```bash
pip install -e .
```
Or, if published:
```bash
pip install vectorstore-client
```

## Requirements

- Python 3.8+
- requests
- Optional: pydantic (for shared model types)


## Usage

- Initialize the client
```python
from vectorstore_client import VectorStoreClient

client = VectorStoreClient("http://localhost:8000")
```

- Create a library
```python
from vectorstore_client.models.library import LibraryCreate

library = client.create_library(LibraryCreate(
    name="My Library",
    description="Library for testing"
))
```

- Add a document
```python
from vectorstore_client.models.document import DocumentCreate

document = client.create_document(library["id"], DocumentCreate(
    title="Sample Doc",
    source="manual",
    description="This is a test document."
))
```


- Add a chunk
```python
from vectorstore_client.models.chunk import ChunkCreate

chunk = client.create_chunk(document["id"], ChunkCreate(
    text="Chunk about vector search",
    embedding=[0.1, 0.3, 0.5, 0.2],
    metadata={"section": "intro"}
))
```

- Perform a vector query
```python
from vectorstore_client.models.query import QueryRequest

results = client.query(library["id"], QueryRequest(
    embedding=[0.1, 0.3, 0.5, 0.2],
    k=3
))

for result in results:
    print(result.text, result.score)
```

## Testing

You can test endpoints using curl or directly from this SDK. Ensure the Vector Store API is running locally before making requests.

## Project Structure

```graphql
vectorstore_client/
├── client.py                  # Main client interface
├── models/                    # Pydantic models (shared with API)
│   ├── library.py
│   ├── document.py
│   ├── chunk.py
│   └── query.py
├── __init__.py
└── README.md                  # You're here!
```

## License

MIT © 2025
