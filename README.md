# Vector Store - Embedding-based Document Management API

**Author:** Manuel Francisco Hidalgo Ros  
**Date:** April 2025

---

## Overview

Vector Store is a RESTful application for managing fragmented documents with embeddings and similarity search using k-NN algorithms. It includes:

- A **REST API** built with **FastAPI**.
- Persistence of data and vector indices.
- Support for k-NN queries via **LSH (Locality Sensitive Hashing)**.
- A **Python SDK** for easy client integration.
- Docker containerization and Kubernetes deployment with Helm.

The system is designed to be robust, modular, and scalable.

---

## Technologies Used

- Python 3.10
- FastAPI
- Pydantic
- Uvicorn
- Docker
- Kubernetes + Minikube
- Helm
- Pytest

---

## Project Structure

```
vector-db/
├── vector_store/                # FastAPI REST API
│   ├── app/                     # Application logic
│   │   ├── api/                 # REST endpoints
│   │   ├── db/                  # Persistence and index layer (InMemoryStore, LSHIndex)
│   │   ├── models/              # Data models (Pydantic)
│   │   └── main.py              # FastAPI entry point
│   │   └── app_state.py         
│   └── scripts/                # Create Chunk With Cohere
│
├── vector_store_sdk/           # Python SDK for the API
│   ├── vectorstore_client/     # HTTP client
│   └── test_sdk_e2e.py         # Full end-to-end SDK test
│
├── Dockerfile                  # Dockerfile for building the image
├── deploy.sh                   # Automated Helm deployment script
├── requirements.txt
├── README.md                   # This file
└── vector-store/               # Helm chart generated via `helm create`
```

---

## Quick Installation

```bash
git clone ...
```

```bash
# 1. Create a virutal env
python3 -m venv venv
source venv/bin/activate  # en Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt
```

### Prerequisites
- Python >= 3.10
- Docker
- Helm
- kubectl
- Minikube (for local Kubernetes testing)

### Full Launch in Minikube

```bash
chmod +x deploy.sh
./deploy.sh
```

This script:
1. Starts Minikube if needed.
2. Uses Minikube's Docker daemon.
3. Builds the local Docker image.
4. Installs (or upgrades) the Helm Chart.
5. Waits for the pod.
6. Performs `port-forward` to `http://localhost:8080`

---

## API Usage

Once deployed:

### Example: Create Library
```bash
curl -X POST http://localhost:8080/libraries/ \
  -H 'Content-Type: application/json' \
  -d '{"name": "Test", "description": "Library for testing"}'
```

### Example: Query Chunks
```bash
curl -X POST http://localhost:8080/libraries/<LIB_ID>/query/ \
  -H 'Content-Type: application/json' \
  -d '{"embedding": [0.1, 0.2, ..., 0.1024], "k": 3}'
```

> You may omit the `embedding` field when creating a chunk: if not provided, the backend automatically generates one using Cohere's API.

---

## Python SDK

### Local SDK Installation
```bash
cd vector_store_sdk
pip install -e .
```

### Basic SDK Usage
```python
from vectorstore_client import VectorStoreClient
from vectorstore_client.models.library import LibraryCreate

client = VectorStoreClient("http://localhost:8080")
library = client.create_library(LibraryCreate(name="Test"))
```

### End-to-end SDK Test
```bash
pytest vector_store_sdk/test_sdk_e2e.py -v
```

### SDK Documentation

- `VectorStoreClient` methods for managing:
  - Libraries: `create_library`, `get_library`, `update_library`, `delete_library`
  - Documents: `create_document`, `update_document`, `delete_document`
  - Chunks: `create_chunk`, `update_chunk`, `get_chunk`, `delete_chunk`
  - Queries: `query`

All models are strongly typed and validated using Pydantic, located under `vectorstore_client.models.*`.

---

## Implementation Details

### 1. LSH Index

**What is LSH?**  
An approximate search algorithm that uses similarity-sensitive hash functions to group similar vectors.

#### Implementation
- `N` random planes (default 10) are generated when initializing the index.
- Each embedding is projected onto these planes and converted to a binary key.
- Hashes are stored in a dictionary: `{hash: [chunk_id, ...]}`.

#### Complexity:
- **Space:** O(n) in number of chunks (each maps to one hash).
- **Insertion Time:** O(d × p), where `d` is vector dimension, `p` is the number of planes.
- **Search Time:** O(1) to access the hash bucket and compare with candidates (≈k).

#### Persistence:
- Both random planes and generated hashes are saved in `lsh_index.json`.
- On API restart, indices are automatically rebuilt from disk.

### 2. Data Persistence

All data is stored on disk as JSON files:

- Libraries: `libraries.json`
- Documents: `documents_<lib_id>.json`
- Chunks: `chunks_<doc_id>.json`
- LSH Index: `lsh_index.json`

> The system automatically reloads all data at API startup.

### 3. Embedding Dimension Restriction

- All embeddings must be exactly **1024 dimensions**.
- Enforced on both manual creation and queries.
- If `embedding=None`, the system calls Cohere internally to generate a valid embedding.

### 4. Best Practices

- Extensive use of **Pydantic models** for input validation and strong typing.
- Clear separation of concerns:
  - `api/`: endpoints
  - `db/`: storage + indexing
  - `models/`: data definitions
- Semantic naming and clean code.
- Integration and end-to-end testing.
- Swagger documentation at `/docs`.

### 5. Docker and Helm

- Image based on `python:3.10-slim` with minimal dependencies.
- `deploy.sh` automates:
  - Minikube launch
  - Docker build
  - Helm upgrade/install
  - Automatic port-forward
- Helm Chart is configurable: replicaCount, port, image, probes, etc.

---

## Resetting the Database

To completely reset the system and start with a clean database (deleting all libraries, documents, chunks, and indices), follow these steps:

```bash
# 1. Uninstall the current Helm release
helm uninstall vector-store

# 2. Delete the Persistent Volume Claim (PVC)
kubectl delete pvc vector-store-pvc

# (Optional) 3. Delete the Persistent Volume (PV) if it still exists
kubectl get pv
kubectl delete pv <PV_NAME_IF_PRESENT>

# 4. Redeploy everything cleanly
./deploy.sh
```

This will remove all persisted data stored in the mounted volume and launch a fresh instance with no data.

---

## Verification and Tests

### API
```bash
uvicorn vector_store.app.main:app --reload
```
Access at `http://localhost:8000/docs`

### LSH Persistence Test
```bash
python vector_store_sdk/test_lsh_persistence.py
```
> Prompts you to restart the API and confirms embeddings remain queryable.

### End-to-end SDK Test
```bash
pytest vector_store_sdk/test_sdk_e2e.py -v
```

---

## Final Project Status

- [x] REST API: CRUD + k-NN query
- [x] LSH fully implemented from scratch with persistence
- [x] Full-featured SDK with docs and end-to-end test
- [x] Data and index persistence
- [x] Functional root-level Dockerfile
- [x] Kubernetes deployment via Helm
- [x] Fully automated `deploy.sh` script

---

## Thank You
This project represents a complete, handcrafted and well-documented implementation, fulfilling all technical requirements and going beyond to offer a maintainable and scalable architecture.

---

If you have any technical questions or want to contribute or extend the system, feel free to open an issue or contact the author!

