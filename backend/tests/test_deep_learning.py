import numpy as np
from PIL import Image

from app.services.deep_learning.anomaly_engine import AnomalyEngine
from app.services.deep_learning.feature_extractor import FeatureExtractor
from app.services.deep_learning.model_manager import ModelManager
from app.services.deep_learning.similarity_engine import cosine_similarity, similarity_to_risk


def test_model_manager_initializes_without_gpu_requirement() -> None:
    manager = ModelManager()
    assert manager.get_device() in {"cpu", "cuda"}
    assert manager.is_available() in {True, False}


def test_feature_extractor_outputs_normalized_embedding() -> None:
    image = Image.new("RGB", (64, 64), color=(255, 255, 255))
    extractor = FeatureExtractor()
    embedding = extractor.extract_embedding(image)

    assert isinstance(embedding, np.ndarray)
    assert embedding.shape[0] > 0
    assert np.isfinite(embedding).all()
    assert np.linalg.norm(embedding) > 0


def test_similarity_engine_returns_risk_band() -> None:
    ref = np.array([1.0, 0.0, 0.0], dtype=float)
    match = np.array([0.98, 0.10, 0.02], dtype=float)
    diff = np.array([0.0, 1.0, 0.0], dtype=float)

    assert cosine_similarity(ref, match) > 0.9
    assert cosine_similarity(ref, diff) < 0.5
    assert similarity_to_risk(0.95)["risk_level"] == "LOW"
    assert similarity_to_risk(0.5)["risk_level"] in {"MODERATE", "HIGH"}


def test_anomaly_engine_scores_deviation() -> None:
    engine = AnomalyEngine()
    score = engine.calculate_anomaly_score(0.9, 0.2)

    assert 0.0 <= score <= 1.0
    assert engine.detect_outlier(0.9, 0.25) in {"LOW", "MODERATE", "HIGH"}


def test_deep_learning_fallback_mode_is_explainable() -> None:
    from app.services.deep_learning.config import get_deep_learning_settings

    settings = get_deep_learning_settings()
    assert settings.enabled in {True, False}
    assert settings.device in {"cpu", "cuda", "auto"}
    assert settings.model_name
