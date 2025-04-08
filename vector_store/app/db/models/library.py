from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, String

from vector_store.app.db.database import Base


class Library(Base):
    __tablename__ = "libraries"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    index_type = Column(String, default="lsh")
