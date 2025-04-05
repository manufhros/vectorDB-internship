from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID
from vector_store.app.models.document import Document, DocumentCreate, DocumentUpdate
from vector_store.app.app_state import store

router = APIRouter(prefix="/libraries/{library_id}/documents", tags=["documents"])


@router.post("/", response_model=Document)
def create_document(library_id: UUID, data: DocumentCreate):
    return store.create_document(library_id, data)

@router.get("/", response_model=List[Document])
def list_documents(library_id: UUID):
    return store.list_documents_by_library(library_id)

@router.get("/{document_id}", response_model=Document)
def get_document(library_id: UUID, document_id: UUID):
    doc = store.get_document(document_id)
    if not doc or doc.library_id != library_id:
        raise HTTPException(status_code=404, detail="Document not found in this library")
    return doc

@router.delete("/{document_id}", status_code=204)
def delete_document(library_id: UUID, document_id: UUID):
    doc = store.get_document(document_id)
    if not doc or doc.library_id != library_id:
        raise HTTPException(status_code=404, detail="Document not found in this library")
    store.delete_document(document_id)

@router.put("/{document_id}", response_model=Document)
def update_document(library_id: UUID, document_id: UUID, data: DocumentUpdate):
    doc = store.get_document(document_id)
    if not doc or doc.library_id != library_id:
        raise HTTPException(status_code=404, detail="Document not found in this library")
    return store.update_document(document_id, data)
    