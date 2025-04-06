from uuid import UUID

from fastapi import APIRouter

from vector_store.app.app_state import store
from vector_store.app.models.query import QueryRequest, QueryResult

router = APIRouter(prefix="/libraries/{library_id}/query", tags=["query"])


@router.post("/", response_model=list[QueryResult])
def query_library(library_id: UUID, query: QueryRequest):
    return store.query_chunks(library_id, query)
