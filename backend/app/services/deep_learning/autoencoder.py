from __future__ import annotations


class DocumentAutoencoder:
    """Optional interface for future autoencoder-based anomaly modeling."""

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self.model = None

    def load_model(self):
        if not self.enabled:
            return None
        return self.model

    def reconstruct(self, data):
        if not self.enabled or self.model is None:
            return data
        return data

    def calculate_reconstruction_error(self, data):
        if not self.enabled or self.model is None:
            return 0.0
        return 0.0
