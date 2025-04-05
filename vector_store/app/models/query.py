from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime


class QueryRequest(BaseModel):
    embedding: List[float] = Field(..., example=[0.12, -0.34, 0.56])
    k: int = Field(5, ge=1, le=50, example=5)
    filters: Optional[Dict[str, str]] = Field(default_factory=dict, example={"language": "en", "author": "support"})


class QueryResult(BaseModel):
    chunk_id: UUID
    score: float = Field(..., ge=0.0, le=1.0)           # Similarity
    text: str                                           # Chunk content
    metadata: Optional[Dict[str, str]] = None