from fastapi import APIRouter, HTTPException
from typing import List
from vector_store.app.app_state import store
from vector_store.app.models.chunk import Chunk, ChunkCreate, ChunkUpdate
from uuid import UUID

# Router for operations related to a specific document
router = APIRouter(prefix="/documents/{document_id}/chunks", tags=["chunks"])

@router.post("/", response_model=Chunk)
def create_chunk(document_id: UUID, data: ChunkCreate):
    return store.create_chunk(document_id, data)

@router.get("/", response_model=List[Chunk])
def list_chunks(document_id: UUID):
    return store.list_chunks_by_document(document_id)

@router.get("/{chunk_id}", response_model=Chunk)
def get_chunk(document_id: UUID, chunk_id: UUID):
    chunk = store.get_chunk(chunk_id)
    if not chunk or chunk.document_id != document_id:
        raise HTTPException(status_code=404, detail="Chunk not found in this document")
    return chunk

@router.delete("/{chunk_id}", status_code=204)
def delete_chunk(document_id: UUID, chunk_id: UUID):
    chunk = store.get_chunk(chunk_id)
    if not chunk or chunk.document_id != document_id:
        raise HTTPException(status_code=404, detail="Chunk not found in this document")
    store.delete_chunk(chunk_id)


# Router to access directly by chunk_id (without document_id in the route)
router2 = APIRouter(prefix="/chunks", tags=["chunks"])

@router2.get("/{chunk_id}", response_model=Chunk)
def get_chunk(chunk_id: UUID):
    chunk = store.get_chunk(chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return chunk

@router2.put("/{chunk_id}", response_model=Chunk)
def update_chunk(chunk_id: UUID, data: ChunkUpdate):
    updated = store.update_chunk(chunk_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return updated

@router2.delete("/{chunk_id}", status_code=204)
def delete_chunk(chunk_id: UUID):
    chunk = store.get_chunk(chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    store.delete_chunk(chunk_id)
