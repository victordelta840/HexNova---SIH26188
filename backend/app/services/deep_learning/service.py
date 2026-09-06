from __future__ import annotations

from io import BytesIO
from typing import Any

import numpy as np
from PIL import Image

from app.services.deep_learning.anomaly_engine import AnomalyEngine
from app.services.deep_learning.config import get_deep_learning_settings
from app.services.deep_learning.explainability import DeepLearningExplainability
from app.services.deep_learning.feature_extractor import FeatureExtractor
from app.services.deep_learning.region_feature_extractor import RegionFeatureExtractor
from app.services.deep_learning.similarity_engine import SimilarityEngine


class DeepLearningService:
    def __init__(self) -> None:
        self.settings = get_deep_learning_settings()
        self.feature_extractor = FeatureExtractor(self.settings.model_name)
        self.similarity_engine = SimilarityEngine({
            "global_similarity_threshold": self.settings.global_similarity_threshold,
            "region_similarity_threshold": self.settings.region_similarity_threshold,
            "anomaly_threshold": self.settings.anomaly_threshold,
        })
        self.anomaly_engine = AnomalyEngine(self.settings.anomaly_threshold)
        self.region_extractor = RegionFeatureExtractor(self.feature_extractor)

    def analyze_document(self, image_bytes: bytes, *, document_type: str = "passport", reference_profile: dict[str, Any] | None = None) -> dict[str, Any]:
        settings = get_deep_learning_settings()
        if not settings.enabled:
            return {
                "status": "unavailable",
                "reason": "Deep learning is disabled in configuration.",
                "fallback_used": True,
                "model_status": "disabled",
                "global_similarity": 0.0,
                "global_risk": 0,
                "region_analysis": [],
                "anomaly_score": 0.0,
                "risk_contribution": 0,
                "explanations": ["Deep learning analysis is disabled, so the rest of the screening pipeline continued in fallback mode."],
            }

        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            uploaded_embedding = self.feature_extractor.extract_embedding(image)
            reference_embedding = self._extract_reference_embedding(reference_profile, uploaded_embedding)
            global_match = self.similarity_engine.compare_embeddings(reference_embedding, uploaded_embedding)
            region_map = {
                "header": (0, 0, max(1, image.width // 2), max(1, image.height // 3)),
                "main_content": (0, max(1, image.height // 5), image.width, max(1, image.height // 2)),
                "photo_region": (max(0, image.width // 3), max(0, image.height // 3), max(1, image.width - 20), max(1, image.height - 20)),
            }
            region_features = self.region_extractor.extract_region_features(image, region_map)
            reference_regions = self._build_reference_regions(reference_profile, region_features)
            region_analysis = self.similarity_engine.compare_regions(reference_regions, region_features)
            anomaly = self.anomaly_engine.analyze_features(reference_embedding, uploaded_embedding, deviation=max(0.0, 1.0 - global_match["global_similarity"]))
            explanations = DeepLearningExplainability.explain(global_match["global_similarity"], region_analysis, float(anomaly["anomaly_score"]))
            risk_contribution = int(max(0, min(100, round((1.0 - global_match["global_similarity"]) * 100 * 0.6 + float(anomaly["anomaly_score"]) * 100 * 0.4))))
            return {
                "status": "completed",
                "model_status": "active",
                "global_similarity": float(global_match["global_similarity"]),
                "global_risk": int(global_match["global_risk"]),
                "region_analysis": region_analysis,
                "anomaly_score": float(anomaly["anomaly_score"]),
                "risk_contribution": risk_contribution,
                "explanations": explanations,
                "fallback_used": False,
                "model_name": self.settings.model_name,
                "document_type": document_type,
            }
        except Exception as exc:  # pragma: no cover - this is intentionally graceful fallback
            return {
                "status": "unavailable",
                "reason": f"Deep learning analysis could not complete: {exc}",
                "fallback_used": True,
                "model_status": "unavailable",
                "global_similarity": 0.0,
                "global_risk": 0,
                "region_analysis": [],
                "anomaly_score": 0.0,
                "risk_contribution": 0,
                "explanations": ["Deep learning analysis was unavailable, so the system continued using the rest of the screening layers."],
            }

    def _extract_reference_embedding(self, reference_profile: dict[str, Any] | None, uploaded_embedding: np.ndarray) -> np.ndarray:
        if not reference_profile:
            return np.asarray(np.linspace(0.3, 0.9, num=uploaded_embedding.size, dtype=np.float32), dtype=np.float32)
        profile = reference_profile.get("deep_learning_profile") or reference_profile.get("characteristics", {}).get("deep_learning_profile") or {}
        embedding = profile.get("global_embedding")
        if embedding:
            return np.asarray(embedding, dtype=np.float32)
        summary = reference_profile.get("profile_summary") or {}
        base = [float(summary.get("aspect_ratio", 1.5)), float(summary.get("layout_consistency", 85)) / 100.0, float(summary.get("quality_score", 80)) / 100.0]
        return np.asarray(base + [0.8] * max(0, uploaded_embedding.size - 3), dtype=np.float32)[:uploaded_embedding.size]

    def _build_reference_regions(self, reference_profile: dict[str, Any] | None, uploaded_region_features: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        if not reference_profile:
            return {name: vector.copy() for name, vector in uploaded_region_features.items()}
        profile = reference_profile.get("deep_learning_profile") or reference_profile.get("characteristics", {}).get("deep_learning_profile") or {}
        region_embeddings = profile.get("region_embeddings") or {}
        if not region_embeddings:
            return {name: vector.copy() for name, vector in uploaded_region_features.items()}
        return {name: np.asarray(value, dtype=np.float32) for name, value in region_embeddings.items()}


def analyze_deep_learning_document(image_bytes: bytes, *, document_type: str = "passport", reference_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    return DeepLearningService().analyze_document(image_bytes, document_type=document_type, reference_profile=reference_profile)
