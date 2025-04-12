import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Asegura que la carpeta data existe
os.makedirs("data", exist_ok=True)

# Ruta absoluta a la base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "../../../data/database.db")
DATABASE_URL = f"sqlite:///{os.path.abspath(DATABASE_PATH)}"

print("🔍 database.py is executing...")
print(f"📂 BASE_DIR: {BASE_DIR}")
print(f"📄 Full DB Path: {DATABASE_PATH}")
print(f"🔗 DATABASE_URL: {DATABASE_URL}")

# Motor SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Generador para obtener sesiones
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()