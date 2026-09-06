from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.core.config import get_settings


@dataclass(frozen=True)
class DeepLearningSettings:
    enabled: bool = True
    model_name: str = "efficientnet_b0"
    device: str = "cpu"
    global_similarity_threshold: float = 0.75
    region_similarity_threshold: float = 0.70
    anomaly_threshold: float = 0.60
    autoencoder_enabled: bool = False
    demo_mode: bool = True

    @classmethod
    def from_environment(cls) -> "DeepLearningSettings":
        settings = get_settings()
        return cls(
            enabled=str(getattr(settings, "deep_learning_enabled", "true")).lower() in {"1", "true", "yes", "on"},
            model_name=getattr(settings, "deep_model_name", "efficientnet_b0") or "efficientnet_b0",
            device=getattr(settings, "deep_device", "cpu") or "cpu",
            global_similarity_threshold=float(getattr(settings, "deep_global_similarity_threshold", 0.75) or 0.75),
            region_similarity_threshold=float(getattr(settings, "deep_region_similarity_threshold", 0.70) or 0.70),
            anomaly_threshold=float(getattr(settings, "deep_anomaly_threshold", 0.60) or 0.60),
            autoencoder_enabled=str(getattr(settings, "autoencoder_enabled", "false")).lower() in {"1", "true", "yes", "on"},
            demo_mode=str(getattr(settings, "demo_mode", "true")).lower() in {"1", "true", "yes", "on"},
        )


@lru_cache
def get_deep_learning_settings() -> DeepLearningSettings:
    return DeepLearningSettings.from_environment()
