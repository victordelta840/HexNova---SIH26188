from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    document_type: Literal["passport", "visa", "national_id", "driving_licence", "permit"]
    filename: str
    content_type: str
    size_bytes: int = Field(gt=0)
    content_hash: str = Field(min_length=64, max_length=64)
    status: Literal["accepted"]