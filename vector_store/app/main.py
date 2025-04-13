import logging

from fastapi import FastAPI

from vector_store.app.api import chunks, documents, libraries, query
from vector_store.app.db.base import Base
from vector_store.app.db.database import init_db



logger = logging.getLogger(__name__)

app = FastAPI(title="Vector Store API")


# Inicializar la base de datos al arrancar la app
@app.on_event("startup")
def startup_event():
    init_db()

# Rutas
app.include_router(libraries.router)
app.include_router(documents.router)
app.include_router(chunks.router)
app.include_router(chunks.router2)
app.include_router(query.router)


@app.get("/")
def root():
    return {"message": "Welcome to the Vector Store API"}
