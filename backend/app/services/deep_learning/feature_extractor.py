from __future__ import annotations

import numpy as np
from PIL import Image

from app.services.deep_learning.model_manager import ModelManager


class FeatureExtractor:
    """CPU-safe feature extractor using a lightweight CNN backbone without the final classifier."""

    def __init__(self, model_name: str = "efficientnet_b0") -> None:
        self.model_name = model_name
        self.model_manager = ModelManager()

    def _to_rgb(self, image: Image.Image) -> Image.Image:
        if image.mode != "RGB":
            return image.convert("RGB")
        return image

    def _preprocess(self, image: Image.Image) -> Image.Image:
        image = self._to_rgb(image)
        max_side = 224
        width, height = image.size
        scale = min(max_side / max(width, height), 1.0)
        resized = image.resize((max(1, int(width * scale)), max(1, int(height * scale))), Image.Resampling.BILINEAR)
        return resized

    def extract_features(self, image: Image.Image | np.ndarray) -> np.ndarray:
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image.astype("uint8"))
        image = self._preprocess(image)
        model = self.model_manager.get_model()
        if model is None:
            array = np.asarray(image, dtype=np.float32)
            grayscale = array.mean(axis=2)
            embedding = np.asarray(grayscale.ravel(), dtype=np.float32)
            return self._normalize(embedding)

        array = np.asarray(image, dtype=np.float32) / 255.0
        if array.ndim == 2:
            array = np.stack([array] * 3, axis=-1)
        tensor = np.transpose(array, (2, 0, 1))
        tensor = tensor.reshape(1, *tensor.shape)
        try:
            import torch

            with torch.no_grad():
                model_output = model(torch.tensor(tensor, dtype=torch.float32))
                if hasattr(model_output, "features"):
                    features = model_output.features
                elif hasattr(model_output, "flatten"):
                    features = model_output.flatten
                else:
                    features = model_output
                embed = features.detach().cpu().numpy().reshape(-1)
                return self._normalize(embed.astype(np.float32))
        except Exception:
            flat = np.asarray(array, dtype=np.float32).reshape(-1)
            return self._normalize(flat)

    def extract_embedding(self, image: Image.Image | np.ndarray) -> np.ndarray:
        features = self.extract_features(image)
        return self._normalize(features)

    @staticmethod
    def _normalize(values: np.ndarray) -> np.ndarray:
        arr = np.asarray(values, dtype=np.float32)
        norm = np.linalg.norm(arr)
        if norm == 0:
            return arr
        return arr / norm
