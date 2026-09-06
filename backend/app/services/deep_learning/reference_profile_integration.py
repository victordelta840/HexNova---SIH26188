from __future__ import annotations

from typing import Any

from app.services.deep_learning.feature_extractor import FeatureExtractor
from app.services.deep_learning.region_feature_extractor import RegionFeatureExtractor


class ReferenceProfileDeepLearningIntegration:
    def __init__(self) -> None:
        self.feature_extractor = FeatureExtractor()
        self.region_extractor = RegionFeatureExtractor(self.feature_extractor)

    def build_reference_profile(self, image, *, profile_summary: dict[str, Any] | None = None) -> dict[str, Any]:
        embedding = self.feature_extractor.extract_embedding(image)
        region_map = {
            "header": (0, 0, 200, 100),
            "main_content": (0, 100, 300, 300),
            "photo_region": (120, 120, 220, 220),
        }
        region_embeddings = self.region_extractor.extract_region_features(image, region_map)
        return {
            "deep_learning_profile": {
                "model_name": self.feature_extractor.model_name,
                "embedding_version": "deep-feature-v1",
                "global_embedding": embedding.tolist(),
                "region_embeddings": {name: values.tolist() for name, values in region_embeddings.items()},
                "created_at": "now",
                "model_available": True,
            },
            "profile_summary": profile_summary or {},
        }
