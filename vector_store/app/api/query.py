from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from vector_store.app.db.database import get_db
from vector_store.app.db.services.query_store import QueryStoreService
from vector_store.app.models.query import QueryRequest, QueryResult

router = APIRouter(prefix="/libraries/{library_id}/query", tags=["query"])


@router.post("/", response_model=list[QueryResult])
def query_library(library_id: UUID, query: QueryRequest, db: Session = Depends(get_db)):
    store = QueryStoreService(db)
    return store.query_chunks(library_id, query)
