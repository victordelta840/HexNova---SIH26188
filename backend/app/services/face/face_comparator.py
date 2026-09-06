import cv2
import numpy as np

from app.services.face.face_detector import DetectionResult


def compare_faces(document_data: bytes, presented_data: bytes, document: DetectionResult, presented: DetectionResult) -> dict[str, bool | float | str | None]:
    if document.status != "FACE_DETECTED" or presented.status != "FACE_DETECTED":
        return {"available": False, "similarity_signal": None, "method": "Haar cascade detection; comparison unavailable without exactly one face in each image"}
    from app.services.ocr.preprocessor import decode_image

    document_image = cv2.cvtColor(np.array(decode_image(document_data)), cv2.COLOR_RGB2GRAY)
    presented_image = cv2.cvtColor(np.array(decode_image(presented_data)), cv2.COLOR_RGB2GRAY)
    document_x, document_y, document_w, document_h = document.faces[0]
    presented_x, presented_y, presented_w, presented_h = presented.faces[0]
    document_crop = cv2.resize(document_image[document_y:document_y + document_h, document_x:document_x + document_w], (128, 128))
    presented_crop = cv2.resize(presented_image[presented_y:presented_y + presented_h, presented_x:presented_x + presented_w], (128, 128))
    document_vector = document_crop.astype(np.float32).ravel()
    presented_vector = presented_crop.astype(np.float32).ravel()
    document_vector -= document_vector.mean()
    presented_vector -= presented_vector.mean()
    denominator = float(np.linalg.norm(document_vector) * np.linalg.norm(presented_vector))
    signal = float(np.dot(document_vector, presented_vector) / denominator) if denominator else None
    return {"available": signal is not None, "similarity_signal": signal, "method": "Haar cascade face detection + normalized grayscale correlation", "interpretation": "Technical comparison signal only; no identity conclusion is produced"}