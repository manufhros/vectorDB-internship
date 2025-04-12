from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from vector_store.app.db.base import Base

class LSHIndexModel(Base):
    __tablename__ = "lsh_indices"

    library_id = Column(String, primary_key=True)
    dim = Column(Integer, nullable=False)
    num_tables = Column(Integer, nullable=False)
    num_hashes = Column(Integer, nullable=False)
    tables = Column(JSON, nullable=False)
    hyperplanes = Column(JSON, nullable=False)
    vectors = Column(JSON, nullable=False)