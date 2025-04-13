import logging

from fastapi import FastAPI

from vector_store.app.api import chunks, documents, libraries, query
from vector_store.app.db.base import Base

# Importación explícita de modelos para registrarlos en Base.metadata
from vector_store.app.db.session import engine

logger = logging.getLogger(__name__)


print("🛠️ Creating tables at startup...")
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vector Store API")

# Rutas
app.include_router(libraries.router)
app.include_router(documents.router)
app.include_router(chunks.router)
app.include_router(chunks.router2)
app.include_router(query.router)


@app.get("/")
def root():
    return {"message": "Welcome to the Vector Store API"}
