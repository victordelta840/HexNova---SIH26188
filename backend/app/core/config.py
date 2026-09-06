import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Identity Screening System API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://screening:change-me@localhost:5432/screening"
    max_upload_size_bytes: int = 10 * 1024 * 1024
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    demo_officer_password: str | None = None
    demo_admin_password: str | None = None
    reference_profile_lock_secret: str | None = None
    deep_learning_enabled: bool = True
    deep_model_name: str = "efficientnet_b0"
    deep_device: str = "cpu"
    deep_global_similarity_threshold: float = 0.75
    deep_region_similarity_threshold: float = 0.70
    deep_anomaly_threshold: float = 0.60
    autoencoder_enabled: bool = False
    demo_mode: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SCREENING_",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def deep_learning_settings(self) -> dict[str, object]:
        fallback = {
            "enabled": os.getenv("DEEP_LEARNING_ENABLED", str(self.deep_learning_enabled)).lower() in {"1", "true", "yes", "on"},
            "model_name": os.getenv("DEEP_MODEL_NAME") or self.deep_model_name,
            "device": os.getenv("DEEP_DEVICE") or self.deep_device,
            "global_similarity_threshold": float(os.getenv("DEEP_GLOBAL_SIMILARITY_THRESHOLD", str(self.deep_global_similarity_threshold))),
            "region_similarity_threshold": float(os.getenv("DEEP_REGION_SIMILARITY_THRESHOLD", str(self.deep_region_similarity_threshold))),
            "anomaly_threshold": float(os.getenv("DEEP_ANOMALY_THRESHOLD", str(self.deep_anomaly_threshold))),
        }
        return fallback


@lru_cache
def get_settings() -> Settings:
    return Settings()