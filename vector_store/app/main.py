import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from vector_store.app.api import chunks, documents, libraries, query

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # App starts


app = FastAPI(title="Vector Store API", lifespan=lifespan)

# Register routers
app.include_router(libraries.router)
app.include_router(documents.router)
app.include_router(chunks.router)  # contextualized routes
app.include_router(chunks.router2)  # direct routes
app.include_router(query.router)


@app.get("/")
def root():
    return {"message": "Welcome to the Vector Store API"}
