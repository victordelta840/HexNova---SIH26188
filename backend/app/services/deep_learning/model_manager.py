from __future__ import annotations

from functools import lru_cache
from typing import Any


class ModelManager:
    """Singleton-style model manager for optional CPU-safe deep learning components."""

    _model: Any = None
    _device: str = "cpu"
    _available: bool = False
    _last_error: str | None = None

    @classmethod
    def get_device(cls) -> str:
        if cls._device == "cpu":
            return "cpu"
        return cls._device

    @classmethod
    def is_available(cls) -> bool:
        return cls._available

    @classmethod
    def get_model(cls) -> Any:
        if cls._model is not None:
            return cls._model
        cls._model = cls._load_model()
        return cls._model

    @classmethod
    def unload_model(cls) -> None:
        cls._model = None

    @classmethod
    def get_last_error(cls) -> str | None:
        return cls._last_error

    @classmethod
    def _load_model(cls) -> Any:
        try:
            import torch
            from torchvision import models

            cls._device = "cuda" if torch.cuda.is_available() else "cpu"
            model = models.efficientnet_b0(weights=None)
            model.eval()
            model.to(cls._device)
            cls._available = True
            cls._last_error = None
            return model
        except Exception as exc:  # pragma: no cover - intentionally graceful fallback
            cls._device = "cpu"
            cls._available = False
            cls._last_error = f"Deep learning model unavailable on this environment: {exc}"
            return None
