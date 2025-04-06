from uuid import UUID

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    embedding: list[float] = Field(..., example=[0.12, -0.34, 0.56])
    k: int = Field(5, ge=1, le=50, example=5)
    filters: dict[str, str] | None = Field(
        default_factory=dict, example={"language": "en", "author": "support"}
    )


class QueryResult(BaseModel):
    chunk_id: UUID
    score: float = Field(..., ge=0.0, le=1.0)  # Similarity
    text: str  # Chunk content
    metadata: dict[str, str] | None = None
