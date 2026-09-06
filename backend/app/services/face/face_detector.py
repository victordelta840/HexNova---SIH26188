from dataclasses import dataclass

import cv2
import numpy as np

from app.services.ocr.preprocessor import decode_image


@dataclass
class DetectionResult:
    status: str
    detected: bool
    faces: list[tuple[int, int, int, int]]
    quality: dict[str, float | str]


def detect_faces(data: bytes) -> DetectionResult:
    try:
        image = decode_image(data)
        pixels = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = [tuple(int(value) for value in face) for face in detector.detectMultiScale(pixels, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))]
        status = "FACE_DETECTED" if len(faces) == 1 else "MULTIPLE_FACES" if len(faces) > 1 else "NO_FACE_DETECTED"
        return DetectionResult(status=status, detected=bool(faces), faces=faces, quality={"width": float(pixels.shape[1]), "height": float(pixels.shape[0])})
    except Exception:
        return DetectionResult(status="IMAGE_UNREADABLE", detected=False, faces=[], quality={})