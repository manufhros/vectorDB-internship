# scripts/test_db_init.py

from sqlalchemy import inspect
from vector_store.app.db.database import Base, engine

# 👇 IMPORTA TUS MODELOS EXPLÍCITAMENTE
from vector_store.app.db.models.library import Library
from vector_store.app.db.models.document import Document
from vector_store.app.db.models.chunk import Chunk

print("📦 Creando tablas...")
Base.metadata.create_all(bind=engine)

print("🔎 Tablas registradas:")
inspector = inspect(engine)
print(inspector.get_table_names())