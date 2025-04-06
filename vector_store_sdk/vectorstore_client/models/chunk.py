from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChunkBase(BaseModel):
    text: str = Field(..., example="Refunds are processed within 5 business days.")
    embedding: list[float] | None = Field(None, example=[0.123, -0.456, 0.789])
    metadata: dict[str, str] | None = Field(
        default_factory=dict, example={"author": "admin", "language": "en"}
    )


class ChunkCreate(ChunkBase):
    pass


class ChunkUpdate(BaseModel):
    text: str | None = None
    embedding: list[float] | None = None
    metadata: dict[str, str] | None = None


class Chunk(ChunkBase):
    id: UUID
    document_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
