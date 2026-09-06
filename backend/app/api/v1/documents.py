from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.config import get_settings
from app.schemas.documents import DocumentUploadResponse
from app.services.upload import sanitize_filename, validate_document_upload
from app.services.auth import require_officer


router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[Depends(require_officer)])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    document_type: Annotated[
        Literal["passport", "visa", "national_id", "driving_licence", "permit"], Form()
    ],
    document: Annotated[UploadFile, File()],
) -> DocumentUploadResponse:
    document_id, content_hash, size_bytes, _ = await validate_document_upload(
        document, document_type, get_settings()
    )
    return DocumentUploadResponse(
        document_id=document_id,
        document_type=document_type,
        filename=sanitize_filename(document.filename),
        content_type=document.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        content_hash=content_hash,
        status="accepted",
    )