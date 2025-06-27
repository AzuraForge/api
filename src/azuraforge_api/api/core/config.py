# ========== DOSYA: src/azuraforge/core/config.py ==========
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    PROJECT_NAME: str = "AzuraForge API"
    API_V1_PREFIX: str = "/api/v1"
    REDIS_URL: str = "redis://localhost:6379/0"
settings = Settings()