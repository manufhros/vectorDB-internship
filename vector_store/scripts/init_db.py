from vector_store.app.db.database import Base, engine


from vector_store.app.db.models.library import Library
from vector_store.app.db.models.document import Document
from vector_store.app.db.models.chunk import Chunk
from vector_store.app.db.models.lsh_index import LSHIndexModel

print("📦 Creating tables...")
Base.metadata.create_all(bind=engine)

print("✅ Tables created.")