from uuid import UUID

from fastapi import APIRouter, HTTPException

from vector_store.app.app_state import store
from vector_store.app.models.library import Library, LibraryCreate, LibraryUpdate

router = APIRouter(prefix="/libraries", tags=["libraries"])


@router.get("/", response_model=list[Library])
def list_libraries():
    return store.list_libraries()


@router.post("/", response_model=Library)
def create_library(data: LibraryCreate):
    return store.create_library(data)


@router.get("/{library_id}", response_model=Library)
def get_library(library_id: UUID):
    library = store.get_library(library_id)
    if not library:
        raise HTTPException(status_code=404, detail="Library not found")
    return library


@router.delete("/{library_id}", status_code=204)
def delete_library(library_id: UUID):
    store.delete_library(library_id)


@router.put("/{library_id}", response_model=Library)
def update_library(library_id: UUID, data: LibraryUpdate):
    updated = store.update_library(library_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Library not found")
    return updated
