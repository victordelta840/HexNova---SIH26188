from __future__ import annotations

import numpy as np


class AnomalyEngine:
    def __init__(self, threshold: float = 0.60) -> None:
        self.threshold = threshold

    def calculate_anomaly_score(self, similarity: float, deviation: float = 0.0) -> float:
        similarity = max(0.0, min(1.0, float(similarity)))
        deviation = max(0.0, min(1.0, float(deviation)))
        return float(max(0.0, min(1.0, (1.0 - similarity) * 0.7 + deviation * 0.3)))

    def detect_outlier(self, similarity: float, deviation: float = 0.0) -> str:
        score = self.calculate_anomaly_score(similarity, deviation)
        if score >= self.threshold:
            return "HIGH"
        if score >= 0.35:
            return "MODERATE"
        return "LOW"

    def analyze_features(self, reference_embedding: np.ndarray, uploaded_embedding: np.ndarray, *, deviation: float = 0.0) -> dict[str, float | str | list[str]]:
        similarity = float(np.dot(reference_embedding, uploaded_embedding) / (np.linalg.norm(reference_embedding) * np.linalg.norm(uploaded_embedding))) if np.linalg.norm(reference_embedding) and np.linalg.norm(uploaded_embedding) else 0.0
        score = self.calculate_anomaly_score(similarity, deviation)
        reasons: list[str] = []
        if score >= self.threshold:
            reasons.append("Unusual anomaly detected in the visual feature distribution.")
        elif score >= 0.35:
            reasons.append("Moderate visual deviation detected compared with the enrolled reference.")
        else:
            reasons.append("Global visual structure remains largely consistent with the reference.")
        return {
            "anomaly_score": float(score),
            "severity": self.detect_outlier(similarity, deviation),
            "reasons": reasons,
            "similarity": similarity,
        }
