import builtins
from uuid import UUID

from sqlalchemy.orm import Session

from vector_store.app.db.models.document import Document
from vector_store.app.models.document import DocumentCreate, DocumentUpdate


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, library_id: UUID, data: DocumentCreate) -> Document:
        document = Document(
            library_id=str(library_id),
            title=data.title,
            source=data.source,
            description=data.description,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get(self, document_id: UUID, library_id: UUID | None = None) -> Document | None:
        query = self.db.query(Document).filter_by(id=str(document_id))
        if library_id:
            query = query.filter_by(library_id=str(library_id))
        return query.first()

    def list(self) -> list[Document]:
        return self.db.query(Document).all()

    def list_by_library(self, library_id: UUID) -> builtins.list[Document]:  # 👈 Y esto
        return self.db.query(Document).filter_by(library_id=str(library_id)).all()

    def update(
        self, document_id: UUID, data: DocumentUpdate, library_id: UUID
    ) -> Document | None:
        document = self.get(document_id, library_id)
        if not document:
            return None

        if library_id is not None:
            document.library_id = str(library_id)
        if data.title is not None:
            document.title = data.title
        if data.source is not None:
            document.source = data.source
        if data.description is not None:
            document.description = data.description

        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document_id: UUID) -> bool:
        document = self.get(document_id)
        if not document:
            return False
        self.db.delete(document)
        self.db.commit()
        return True
