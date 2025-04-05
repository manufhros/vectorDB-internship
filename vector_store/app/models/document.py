from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class DocumentBase(BaseModel):
    title: str = Field(..., example="Refund Policy")
    source: Optional[str] = Field(None, example="support_docs")
    description: Optional[str] = Field(None, example="Detailed explanation of refund conditions.")


class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None

class Document(DocumentBase):
    id: UUID
    library_id: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
