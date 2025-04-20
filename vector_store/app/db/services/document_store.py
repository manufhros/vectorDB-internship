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
from vector_store.app.models.document import DocumentCreate, DocumentUpdate

load_dotenv()
cohere_client = cohere.Client(os.environ["COHERE_API_KEY"])

logger = logging.getLogger(__name__)


class DocumentStoreService:
    def __init__(self, db: Session):
        self.db = db
        self.library_repo = LibraryRepository(db)
        self.document_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.lsh_repo = LSHIndexRepository(db)

    def create_document(self, library_id: UUID, data: DocumentCreate):
        if not self.library_repo.get(library_id):
            raise HTTPException(status_code=404, detail="Library not found")
        return self.document_repo.create(library_id, data)

    def get_document(self, document_id: UUID, library_id: UUID):
        doc = self.document_repo.get(document_id, library_id)
        if not doc:
            raise HTTPException(
                status_code=404, detail="Document not found in this library"
            )
        return doc

    def list_documents(self):
        return self.document_repo.list()

    def list_documents_by_library(self, library_id: UUID):
        if not self.library_repo.get(library_id):
            raise HTTPException(status_code=404, detail="Library not found")
        return self.document_repo.list_by_library(library_id)

    def update_document(self, document_id: UUID, data: DocumentUpdate):
        document = self.document_repo.get(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return self.document_repo.update(document_id, data, document.library_id)

    def delete_document(self, document_id: UUID):
        if not self.document_repo.get(document_id):
            raise HTTPException(status_code=404, detail="Document not found")
        return self.document_repo.delete(document_id)

    # Index management helper methods
    def _create_and_persist_index(self, library_id: UUID, index_type: str):
        """Create a new index and persist it if needed"""
        index = IndexFactory.create(index_type, dim=EMBEDDING_DIM)

        # Persist LSH indices
        if index_type == "lsh":
            self.lsh_repo.save(library_id, index)

        return index
