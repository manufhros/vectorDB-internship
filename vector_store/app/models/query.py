from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class QueryRequest(BaseModel):
    text: str | None = None
    embedding: list[float] | None = None
    k: int = Field(5, ge=1, le=50, example=5)
    filters: dict[str, str] | None = Field(
        default_factory=dict, example={"language": "en", "author": "support"}
    )

    @model_validator(mode="after")
    def check_text_or_embedding(self) -> "QueryRequest":
        if not self.text and self.embedding is None:
            raise ValueError("Either 'text' or 'embedding' must be provided")
        return self


class QueryResult(BaseModel):
    chunk_id: UUID
    score: float = Field(..., ge=0.0, le=1.0)
    text: str
    meta: dict[str, str] | None = None
