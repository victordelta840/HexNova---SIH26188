from io import BytesIO

from PIL import Image

from app.schemas.screening import MetadataResult


def analyze_metadata(data: bytes, content_type: str) -> MetadataResult:
    if not content_type.startswith("image/"):
        return MetadataResult(status="unsupported", format=content_type, width=None, height=None, exif_present=None, software=None, findings=["Metadata analysis is limited to image files."])
    try:
        image = Image.open(BytesIO(data))
        exif = image.getexif()
        software = exif.get(305)
        findings = ["Metadata unavailable" if not exif else "Metadata present"]
        if software:
            findings.append("Editing software metadata present; review required")
        return MetadataResult(status="analyzed", format=image.format or content_type, width=image.width, height=image.height, exif_present=bool(exif), software=software, findings=findings)
    except Exception:
        return MetadataResult(status="unavailable", format=content_type, width=None, height=None, exif_present=None, software=None, findings=["Metadata unavailable"])