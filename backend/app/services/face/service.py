from app.schemas.face import FaceComparison, FaceDetection
from app.services.face.face_comparator import compare_faces
from app.services.face.face_detector import detect_faces


def compare_face_images(document_data: bytes, presented_face_data: bytes | None = None) -> FaceComparison:
    if presented_face_data is None:
        unavailable = FaceDetection(status="NOT_AVAILABLE", detected=False, face_count=0, quality={})
        return FaceComparison(status="NOT_AVAILABLE", document_face=unavailable, presented_face=unavailable, comparison={"available": False, "similarity_signal": None, "method": "Not run"}, review={"required": True, "message": "Provide a presented-person image for assistive comparison."})
    document = detect_faces(document_data)
    presented = detect_faces(presented_face_data)
    comparison = compare_faces(document_data, presented_face_data, document, presented)
    document_result = FaceDetection(status=document.status, detected=document.detected, face_count=len(document.faces), quality=document.quality)
    presented_result = FaceDetection(status=presented.status, detected=presented.detected, face_count=len(presented.faces), quality=presented.quality)
    status = "REVIEW_REQUIRED" if comparison["available"] else "WARNING" if presented.status == "MULTIPLE_FACES" or document.status == "MULTIPLE_FACES" else "NOT_AVAILABLE"
    return FaceComparison(status=status, document_face=document_result, presented_face=presented_result, comparison=comparison, review={"required": True, "message": "Face comparison is an assistive signal. Authorized human review is required."})