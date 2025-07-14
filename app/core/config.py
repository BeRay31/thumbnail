# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

"""
Manages application-wide settings loaded from environment variables.
"""
class Settings(BaseSettings):
    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_DB: str
    DATABASE_URL: str = ""

    # Redis settings for Celery broker
    REDIS_HOST: str
    REDIS_PORT: int = 6379

    # MinIO settings for object storage
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_ORIGINALS_BUCKET: str = "raws"
    MINIO_THUMBNAILS_BUCKET: str = "thumbnails"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra="ignore")

    def __init__(self, **values):
        super().__init__(**values)
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+psycopg3://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
            )

# Singleton instance of Settings
settings = Settings()