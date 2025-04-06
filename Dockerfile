# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy everything before installing
COPY . .

# Install dependencies (editable mode)
RUN uv pip install --no-cache --system --editable .

# FastAPI Port
EXPOSE 8000

# Launch API
CMD ["uvicorn", "vector_store.app.main:app", "--host", "0.0.0.0", "--port", "8000"]