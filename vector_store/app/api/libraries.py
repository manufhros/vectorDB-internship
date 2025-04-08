from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from vector_store.app.db.database import get_db
from vector_store.app.db.store import Store
from vector_store.app.models.library import Library, LibraryCreate, LibraryUpdate

router = APIRouter(prefix="/libraries", tags=["libraries"])


@router.get("/", response_model=list[Library])
def list_libraries(db: Session = Depends(get_db)):
    store = Store(db)
    return store.list_libraries()


@router.post("/", response_model=Library)
def create_library(data: LibraryCreate, db: Session = Depends(get_db)):
    store = Store(db)
    return store.create_library(data)


@router.get("/{library_id}", response_model=Library)
def get_library(library_id: UUID, db: Session = Depends(get_db)):
    store = Store(db)
    library = store.get_library(library_id)
    if not library:
        raise HTTPException(status_code=404, detail="Library not found")
    return library


@router.delete("/{library_id}", status_code=204)
def delete_library(library_id: UUID, db: Session = Depends(get_db)):
    store = Store(db)
    store.delete_library(library_id)


@router.put("/{library_id}", response_model=Library)
def update_library(
    library_id: UUID, data: LibraryUpdate, db: Session = Depends(get_db)
):
    store = Store(db)
    updated = store.update_library(library_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Library not found")
    return updated
