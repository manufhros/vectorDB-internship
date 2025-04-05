import cohere
import requests
import json
import os
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
API_BASE_URL = "http://localhost:8000"
DOCUMENT_ID = "fdd177d1-1c7b-46d4-8a15-f0a0d5c2ed7b"
TEXT = "Hello, how's life going? I'm doing soooo well."
METADATA = {"section": "greeting"}

# --- GET EMBEDDING FROM COHERE ---
co = cohere.Client(COHERE_API_KEY)
response = co.embed(
    texts=[TEXT],
    model="embed-english-v3.0",
    input_type="search_document"
)
embedding = response.embeddings[0]

# --- CREATE CHUNK VIA FASTAPI ---
payload = {
    "text": TEXT,
    "embedding": embedding,
    "metadata": METADATA
}

res = requests.post(
    f"{API_BASE_URL}/documents/{DOCUMENT_ID}/chunks/",
    headers={"Content-Type": "application/json"},
    data=json.dumps(payload)
)

# --- OUTPUT ---
print("✅ Chunk created:\n")
print(json.dumps(res.json(), indent=2))

# --- CURL EQUIVALENT ---
print("\n💡 Equivalent curl command:\n")
print(f"""curl -X POST {API_BASE_URL}/documents/{DOCUMENT_ID}/chunks/ \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(payload)}'""")
