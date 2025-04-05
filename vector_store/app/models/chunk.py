from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime

class ChunkBase(BaseModel):
    text: str = Field(..., example="Refunds are processed within 5 business days.")
    embedding: Optional[List[float]] = Field(None, example=[0.123, -0.456, 0.789])
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict, example={"author": "admin", "language": "en"})

class ChunkCreate(ChunkBase):
    pass

class ChunkUpdate(BaseModel):
    text: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, str]] = None

class Chunk(ChunkBase):
    id: UUID
    document_id: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
