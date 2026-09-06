import re
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from io import BytesIO

from app.core.config import Settings
from app.utils.hash import sha256_digest


_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "application/pdf": (b"%PDF-",),
}
_EXTENSIONS = {"image/jpeg": {".jpg", ".jpeg"}, "image/png": {".png"}, "application/pdf": {".pdf"}}


def sanitize_filename(filename: str | None) -> str:
    safe_name = Path(filename or "unnamed-document").name
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", safe_name)
    return safe_name[:128] or "unnamed-document"


async def validate_document_upload(
    upload: UploadFile, document_type: str, settings: Settings
) -> tuple[UUID, str, int, bytes]:
    if upload.content_type not in _SIGNATURES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported document format.",
        )
    filename = upload.filename or ""
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in _EXTENSIONS[upload.content_type]:
        raise HTTPException(status_code=400, detail="The file extension does not match its content type.")

    data = await upload.read(settings.max_upload_size_bytes + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded document is empty.")
    if len(data) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="The uploaded document is too large.")
    if not any(data.startswith(signature) for signature in _SIGNATURES[upload.content_type]):
        raise HTTPException(status_code=400, detail="The document content does not match its format.")
    if upload.content_type.startswith("image/"):
        try:
            with Image.open(BytesIO(data)) as image:
                image.verify()
        except (UnidentifiedImageError, OSError):
            raise HTTPException(status_code=400, detail="The uploaded image is corrupted or unreadable.") from None

    return uuid4(), sha256_digest(data), len(data), data