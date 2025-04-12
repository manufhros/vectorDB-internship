from fastapi import FastAPI
import logging

from vector_store.app.db.base import Base
from vector_store.app.db.session import engine

# Importación explícita de modelos para registrarlos en Base.metadata
from vector_store.app.db.models.library import Library
from vector_store.app.db.models.document import Document
from vector_store.app.db.models.chunk import Chunk

from vector_store.app.api import chunks, documents, libraries, query

logger = logging.getLogger(__name__)

# ⬇️ Se crean las tablas nada más arrancar (sin async)
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