# api/src/azuraforge_api/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "AzuraForge API"
    API_V1_PREFIX: str = "/api/v1"
    
    CORS_ORIGINS: str = "*" 
    
    # === YENİ AYARLAR: JWT için ===
    # Bu anahtar, `openssl rand -hex 32` komutu ile oluşturulabilir.
    # Güvenlik için .env dosyasından okunmalıdır.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 gün
    ALGORITHM: str = "HS256"
    # === YENİ AYARLAR SONU ===

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

settings = Settings()