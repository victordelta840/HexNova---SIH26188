from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image

from app.services.deep_learning.feature_extractor import FeatureExtractor


class DocumentEmbedding:
    def __init__(self, feature_extractor: FeatureExtractor | None = None) -> None:
        self.feature_extractor = feature_extractor or FeatureExtractor()

    def build_embedding(self, image: Image.Image | np.ndarray, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        embedding = self.feature_extractor.extract_embedding(image)
        return {
            "embedding": embedding.tolist(),
            "embedding_version": "deep-feature-v1",
            "model_name": self.feature_extractor.model_name,
            "shape": list(embedding.shape),
            "metadata": metadata or {},
            "vector_norm": float(np.linalg.norm(embedding)),
        }
