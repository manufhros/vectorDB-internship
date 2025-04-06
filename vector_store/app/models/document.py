from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    title: str = Field(..., example="Refund Policy")
    source: str | None = Field(None, example="support_docs")
    description: str | None = Field(
        None, example="Detailed explanation of refund conditions."
    )


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: str | None = None
    source: str | None = None
    description: str | None = None


class Document(DocumentBase):
    id: UUID
    library_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
