from app.schemas.screening import TamperResult
from app.services.ocr.preprocessor import decode_image


def analyze_document(data: bytes) -> TamperResult:
    try:
        image = decode_image(data)
        indicators: list[str] = []
        try:
            import cv2
            import numpy as np
            pixels = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
            variance = float(cv2.Laplacian(pixels, cv2.CV_64F).var())
            if variance < 20:
                indicators.append("low local image detail")
        except (ImportError, ModuleNotFoundError):
            return TamperResult(mode="unavailable", assessment="unknown-unavailable", risk_score=10, indicators=["OpenCV forensic adapter unavailable"], suspicious_regions=[], limitations=["No trained forensic model is included."], message="Forensic analysis is unavailable.")
        return TamperResult(mode="forensic-baseline", assessment="suspicious" if indicators else "clear", risk_score=25 if indicators else 0, indicators=indicators, suspicious_regions=[], limitations=["Baseline signal only; it cannot establish authenticity."], message="Potential tampering indicators require human review." if indicators else "No baseline tampering signal was detected.")
    except Exception:
        return TamperResult(mode="unsupported", assessment="unknown-unavailable", risk_score=10, indicators=[], suspicious_regions=[], limitations=["Unreadable image."], message="Tampering analysis could not process this file.")