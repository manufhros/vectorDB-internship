from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from vector_store.app.db.database import get_db
from vector_store.app.db.store import Store
from vector_store.app.models.document import Document, DocumentCreate, DocumentUpdate

router = APIRouter(prefix="/libraries/{library_id}/documents", tags=["documents"])


@router.post("/", response_model=Document)
def create_document(
    library_id: UUID, data: DocumentCreate, db: Session = Depends(get_db)
):
    store = Store(db)
    return store.create_document(library_id, data)


@router.get("/", response_model=list[Document])
def list_documents(library_id: UUID, db: Session = Depends(get_db)):
    store = Store(db)
    return store.list_documents_by_library(library_id)


@router.get("/{document_id}", response_model=Document)
def get_document(library_id: UUID, document_id: UUID, db: Session = Depends(get_db)):
    store = Store(db)
    return store.get_document(document_id, library_id)


@router.delete("/{document_id}", status_code=204)
def delete_document(library_id: UUID, document_id: UUID, db: Session = Depends(get_db)):
    store = Store(db)
    store.get_document(document_id, library_id)  # Ensure it exists or raise 404
    store.delete_document(document_id)


@router.put("/{document_id}", response_model=Document)
def update_document(
    library_id: UUID,
    document_id: UUID,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
):
    store = Store(db)
    store.get_document(document_id, library_id)  # Ensure it exists or raise 404
    return store.update_document(document_id, data)
