from uuid import UUID

from sqlalchemy.orm import Session

from vector_store.app.db.models.library import Library
from vector_store.app.models.library import LibraryCreate, LibraryUpdate


class LibraryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: LibraryCreate) -> Library:
        library = Library(
            name=data.name,
            description=data.description,
            index_type=data.index_type,
        )
        self.db.add(library)
        self.db.commit()
        self.db.refresh(library)
        return library

    def get(self, library_id: UUID) -> Library | None:
        return self.db.query(Library).filter_by(id=str(library_id)).first()

    def list(self) -> list[Library]:
        return self.db.query(Library).all()

    def update(self, library_id: UUID, data: LibraryUpdate) -> Library | None:
        library = self.get(library_id)
        if not library:
            return None

        if data.name is not None:
            library.name = data.name
        if data.description is not None:
            library.description = data.description

        self.db.commit()
        self.db.refresh(library)
        return library

    def delete(self, library_id: UUID) -> bool:
        library = self.get(library_id)
        if not library:
            return False
        self.db.delete(library)
        self.db.commit()
        return True
