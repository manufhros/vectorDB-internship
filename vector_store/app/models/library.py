from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LibraryBase(BaseModel):
    name: str = Field(..., example="chatbot_faqs")
    description: str | None = Field(
        None, example="Frequently asked questions from the support chatbot"
    )
    index_type: str = "lsh"


class LibraryCreate(LibraryBase):
    pass  # Same as LibraryBase, but can be extended in the future


class LibraryUpdate(BaseModel):
    name: str | None = Field(None, example="Updated Library Name")
    description: str | None = Field(None, example="Updated description")
    index_type: str | None = None


class Library(LibraryBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
