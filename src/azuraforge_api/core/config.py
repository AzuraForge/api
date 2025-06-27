# ========== DOSYA: src/azuraforge_api/core/config.py ==========
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env dosyasından okunacak değişkenler
    PROJECT_NAME: str = "AzuraForge API"
    API_V1_PREFIX: str = "/api/v1"
    
    # .env dosyasının konumu (opsiyonel)
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

settings = Settings()