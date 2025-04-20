import logging
import os
from uuid import UUID

import cohere
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session

from vector_store.app.constants import EMBEDDING_DIM
from vector_store.app.db.index_factory import IndexFactory
from vector_store.app.db.repositories.chunk_repo import ChunkRepository
from vector_store.app.db.repositories.document_repo import DocumentRepository
from vector_store.app.db.repositories.library_repo import LibraryRepository
from vector_store.app.db.repositories.lsh_index_repo import LSHIndexRepository
from vector_store.app.models.library import LibraryCreate, LibraryUpdate

load_dotenv()
cohere_client = cohere.Client(os.environ["COHERE_API_KEY"])

logger = logging.getLogger(__name__)


class LibraryStoreService:
    """
    Service class for managing libraries Store.
    """

    def __init__(self, db: Session):
        self.db = db
        self.library_repo = LibraryRepository(db)
        self.document_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.lsh_repo = LSHIndexRepository(db)

    # Library Methods
    def create_library(self, data: LibraryCreate):
        # Create the library in the database
        library = self.library_repo.create(data)

        # Create and persist the index according to library configuration
        self._create_and_persist_index(library.id, data.index_type)

        return library

    def get_library(self, library_id: UUID):
        return self.library_repo.get(library_id)

    def list_libraries(self):
        return self.library_repo.list()

    def delete_library(self, library_id: UUID):
        library = self.library_repo.get(library_id)
        if not library:
            raise HTTPException(status_code=404, detail="Library not found")

        # Delete persistent index if exists
        self._delete_index(library_id, library.index_type)

        return self.library_repo.delete(library_id)

    def update_library(self, library_id: UUID, data: LibraryUpdate):
        library = self.library_repo.get(library_id)
        if not library:
            raise HTTPException(status_code=404, detail="Library not found")

        # If index type is changing, handle index migration
        if data.index_type and data.index_type != library.index_type:
            self._delete_index(library_id, library.index_type)
            self._create_and_persist_index(library_id, data.index_type)

        return self.library_repo.update(library_id, data)

    # Index management helper methods
    def _create_and_persist_index(self, library_id: UUID, index_type: str):
        """Create a new index and persist it if needed"""
        index = IndexFactory.create(index_type, dim=EMBEDDING_DIM)

        # Persist LSH indices
        if index_type == "lsh":
            self.lsh_repo.save(library_id, index)

        return index

    def _delete_index(self, library_id: UUID, index_type: str):
        """Delete an index if it's persistent"""
        if index_type == "lsh":
            self.lsh_repo.delete(library_id)
