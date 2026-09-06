from __future__ import annotations

from typing import Any

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a_arr = np.asarray(a, dtype=np.float32)
    b_arr = np.asarray(b, dtype=np.float32)
    norm_prod = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm_prod == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / norm_prod)


def similarity_to_risk(similarity: float) -> dict[str, Any]:
    similarity = max(0.0, min(1.0, float(similarity)))
    if similarity >= 0.80:
        return {"risk_level": "LOW", "risk_score": int((1.0 - similarity) * 100), "confidence": 0.8}
    if similarity >= 0.60:
        return {"risk_level": "MODERATE", "risk_score": int((1.0 - similarity) * 100), "confidence": 0.72}
    return {"risk_level": "HIGH", "risk_score": int((1.0 - similarity) * 100), "confidence": 0.66}


class SimilarityEngine:
    def __init__(self, thresholds: dict[str, float] | None = None) -> None:
        self.thresholds = thresholds or {
            "global_similarity_threshold": 0.75,
            "region_similarity_threshold": 0.70,
            "anomaly_threshold": 0.60,
        }

    def compare_embeddings(self, reference_embedding: np.ndarray, uploaded_embedding: np.ndarray) -> dict[str, Any]:
        global_similarity = cosine_similarity(reference_embedding, uploaded_embedding)
        risk = similarity_to_risk(global_similarity)
        return {
            "global_similarity": float(global_similarity),
            "global_risk": int(risk["risk_score"]),
            "risk_level": risk["risk_level"],
            "confidence": risk["confidence"],
            "threshold": self.thresholds["global_similarity_threshold"],
        }

    def compare_regions(self, reference_regions: dict[str, np.ndarray], uploaded_regions: dict[str, np.ndarray]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for region_name in sorted(set(reference_regions) | set(uploaded_regions)):
            reference_vector = reference_regions.get(region_name)
            uploaded_vector = uploaded_regions.get(region_name)
            if reference_vector is None or uploaded_vector is None:
                continue
            similarity = cosine_similarity(reference_vector, uploaded_vector)
            risk = similarity_to_risk(similarity)
            results.append({
                "region": region_name,
                "similarity": float(similarity),
                "risk": risk["risk_level"],
                "risk_score": risk["risk_score"],
                "confidence": risk["confidence"],
            })
        return results
