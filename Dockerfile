# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código
COPY . .

# Expone el puerto de FastAPI
EXPOSE 8000

# Comando para lanzar la API
CMD ["uvicorn", "vector_store.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
