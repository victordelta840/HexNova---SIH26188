from typing import Literal

from pydantic import BaseModel, Field


class FaceDetection(BaseModel):
    status: Literal["FACE_DETECTED", "NO_FACE_DETECTED", "MULTIPLE_FACES", "IMAGE_UNREADABLE", "NOT_AVAILABLE"]
    detected: bool
    face_count: int = Field(ge=0)
    quality: dict[str, float | str] = Field(default_factory=dict)


class FaceComparison(BaseModel):
    status: Literal["REVIEW_REQUIRED", "NOT_AVAILABLE", "WARNING"]
    document_face: FaceDetection
    presented_face: FaceDetection
    comparison: dict[str, bool | float | str | None]
    review: dict[str, bool | str]