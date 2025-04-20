import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from vector_store.app.db.base import Base

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../../../data/database.db")
DATABASE_URL = f"sqlite:///{os.path.abspath(DB_PATH)}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# Import models to ensure they are registered with SQLAlchemy


def init_db():
    logger.info("🛠️ Initializing database (from main.py)...")
    Base.metadata.create_all(bind=engine)


# Generator function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
