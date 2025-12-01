from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings and configuration."""

    # Application
    app_name: str = "Cloud Resource Manager"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./cloud_manager.db"

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_cache_ttl: int = 300  # 5 minutes default

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    encryption_key: str = "your-encryption-key-change-in-production"

    # API
    api_v1_prefix: str = "/api"
    cors_origins: list = ["http://localhost:3000", "http://localhost:8000"]

    # AI/ML Configuration
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ai_provider: str = "anthropic"  # "anthropic" or "openai"
    enable_nl_query: bool = True
    enable_anomaly_detection: bool = True
    enable_ml_recommendations: bool = True
    enable_cost_forecasting: bool = True

    # ML Model Settings
    ml_model_retrain_days: int = 7
    anomaly_detection_sensitivity: float = 0.1
    min_training_days: int = 30

    # Background Tasks
    metric_collection_interval: int = 300  # 5 minutes
    cost_update_interval: int = 86400  # 24 hours
    recommendation_interval: int = 3600  # 1 hour

    # Performance
    cache_enabled: bool = True
    api_timeout: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
