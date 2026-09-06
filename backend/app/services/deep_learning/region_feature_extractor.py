from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image

from app.services.deep_learning.feature_extractor import FeatureExtractor


class RegionFeatureExtractor:
    def __init__(self, feature_extractor: FeatureExtractor | None = None) -> None:
        self.feature_extractor = feature_extractor or FeatureExtractor()

    def extract_region_features(self, image: Image.Image | np.ndarray, region_map: dict[str, tuple[int, int, int, int]]) -> dict[str, np.ndarray]:
        image_obj = image if isinstance(image, Image.Image) else Image.fromarray(np.asarray(image).astype('uint8'))
        features: dict[str, np.ndarray] = {}
        for region_name, box in region_map.items():
            x1, y1, x2, y2 = box
            region = image_obj.crop((x1, y1, x2, y2))
            features[region_name] = self.feature_extractor.extract_embedding(region)
        return features

    def compare_region_profile(self, reference_features: dict[str, np.ndarray], uploaded_features: dict[str, np.ndarray]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for region_name in sorted(set(reference_features) | set(uploaded_features)):
            ref_vector = reference_features.get(region_name)
            up_vector = uploaded_features.get(region_name)
            if ref_vector is None or up_vector is None:
                continue
            similarity = float(np.dot(ref_vector, up_vector) / (np.linalg.norm(ref_vector) * np.linalg.norm(up_vector))) if np.linalg.norm(ref_vector) and np.linalg.norm(up_vector) else 0.0
            results.append({
                "region": region_name,
                "similarity": max(0.0, min(1.0, similarity)),
                "risk": "LOW" if similarity >= 0.80 else "MODERATE" if similarity >= 0.60 else "HIGH",
                "risk_score": int(max(0, min(100, (1.0 - similarity) * 100))),
            })
        return results
