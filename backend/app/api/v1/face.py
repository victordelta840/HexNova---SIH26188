from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.schemas.face import FaceComparison
from app.services.face.service import compare_face_images
from app.services.upload import validate_document_upload
from app.core.config import get_settings
from app.services.auth import require_officer


router = APIRouter(prefix="/face", tags=["face"], dependencies=[Depends(require_officer)])


@router.post("/compare", response_model=FaceComparison)
async def compare_face(
    document: Annotated[UploadFile, File()],
    presented_person: Annotated[UploadFile, File()],
) -> FaceComparison:
    if document.content_type not in {"image/jpeg", "image/png"} or presented_person.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=415, detail="Face comparison requires PNG or JPEG images.")
    _, _, _, document_data = await validate_document_upload(document, "passport", get_settings())
    _, _, _, presented_data = await validate_document_upload(presented_person, "passport", get_settings())
    return compare_face_images(document_data, presented_data)