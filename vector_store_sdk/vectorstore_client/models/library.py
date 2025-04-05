from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class LibraryBase(BaseModel):
    name: str = Field(..., example="chatbot_faqs")
    description: Optional[str] = Field(None, example="Frequently asked questions from the support chatbot")


class LibraryCreate(LibraryBase):
    pass  # Igual que LibraryBase, pero se puede extender en el futuro


class LibraryUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated Library Name")
    description: Optional[str] = Field(None, example="Updated description")


class Library(LibraryBase):
    id: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
