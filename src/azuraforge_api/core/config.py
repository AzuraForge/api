# api/src/azuraforge_api/core/config.py

import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

def get_secret_key() -> str:
    """
    SECRET_KEY'i önce ortam değişkeni olarak arar,
    bulamazsa Docker sır dosyasından okumaya çalışır.
    """
    # 1. Öncelik: Ortam değişkeni (en esnek yöntem)
    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        return secret_key

    # 2. Öncelik: Docker sır dosyası
    secret_key_file = "/run/secrets/secret_key"
    if os.path.exists(secret_key_file):
        with open(secret_key_file, 'r') as f:
            return f.read().strip()
    
    # 3. Geliştirme için uyarı ve güvensiz varsayılan
    #    Eğer bu satırı görüyorsanız, konfigürasyonunuz eksik demektir.
    print("WARNING: SECRET_KEY not found in environment or secrets. Using a default, insecure key for development.")
    return "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"


class Settings(BaseSettings):
    PROJECT_NAME: str = "AzuraForge API"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "*"
    
    # DİKKAT: Field(default_factory=...) kullanarak fonksiyon çağrısını Pydantic'e yaptırıyoruz.
    SECRET_KEY: str = Field(default_factory=get_secret_key)
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()