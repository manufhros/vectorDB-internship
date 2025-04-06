from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LibraryBase(BaseModel):
    name: str = Field(..., example="chatbot_faqs")
    description: str | None = Field(
        None, example="Frequently asked questions from the support chatbot"
    )


class LibraryCreate(LibraryBase):
    pass  # Igual que LibraryBase, pero se puede extender en el futuro


class LibraryUpdate(BaseModel):
    name: str | None = Field(None, example="Updated Library Name")
    description: str | None = Field(None, example="Updated description")


class Library(LibraryBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
