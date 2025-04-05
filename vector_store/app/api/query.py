from fastapi import APIRouter
from uuid import UUID
from vector_store.app.app_state import store
from typing import List
from vector_store.app.models.query import QueryRequest, QueryResult

router = APIRouter(prefix="/libraries/{library_id}/query", tags=["query"])

@router.post("/", response_model=List[QueryResult])
def query_library(library_id: UUID, query: QueryRequest):
    return store.query_chunks(library_id, query)