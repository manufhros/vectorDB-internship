from fastapi import FastAPI
from contextlib import asynccontextmanager
from vector_store.app.api import libraries, documents, chunks, query
from vector_store.app.app_state import store
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # App starts
    logger.info("Saving store to disk on shutdown...")
    store.save()

app = FastAPI(title="Vector Store API", lifespan=lifespan)

# Register routers
app.include_router(libraries.router)
app.include_router(documents.router)
app.include_router(chunks.router)    # contextualized routes
app.include_router(chunks.router2)   # direct routes
app.include_router(query.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Vector Store API"}
