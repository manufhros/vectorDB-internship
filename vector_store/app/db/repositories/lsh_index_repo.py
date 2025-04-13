from uuid import UUID

from sqlalchemy.orm import Session

from vector_store.app.db.lsh_index import LSHIndex
from vector_store.app.db.models.lsh_index import LSHIndexModel


class LSHIndexRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, library_id: UUID) -> LSHIndex | None:
        row = self.db.query(LSHIndexModel).filter_by(library_id=str(library_id)).first()
        if row:
            return LSHIndex.from_dict(
                {
                    "dim": row.dim,
                    "num_tables": row.num_tables,
                    "num_hashes": row.num_hashes,
                    "tables": row.tables,
                    "hyperplanes": row.hyperplanes,
                    "vectors": row.vectors,
                }
            )
        return None

    def save(self, library_id: UUID, index: LSHIndex):
        existing = (
            self.db.query(LSHIndexModel).filter_by(library_id=str(library_id)).first()
        )
        data = index.to_dict()

        if existing:
            existing.dim = data["dim"]
            existing.num_tables = data["num_tables"]
            existing.num_hashes = data["num_hashes"]
            existing.tables = data["tables"]
            existing.hyperplanes = data["hyperplanes"]
            existing.vectors = data["vectors"]
        else:
            new = LSHIndexModel(
                library_id=str(library_id),
                dim=data["dim"],
                num_tables=data["num_tables"],
                num_hashes=data["num_hashes"],
                tables=data["tables"],
                hyperplanes=data["hyperplanes"],
                vectors=data["vectors"],
            )
            self.db.add(new)
        self.db.commit()

    def delete(self, library_id: UUID):
        self.db.query(LSHIndexModel).filter_by(library_id=str(library_id)).delete()
        self.db.commit()
