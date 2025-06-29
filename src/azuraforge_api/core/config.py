# ========== DOSYA: src/azuraforge_api/core/config.py ==========
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AzuraForge API"
    API_V1_PREFIX: str = "/api/v1"
    
    # Yeni CORS ayarı
    # Virgülle ayrılmış URL'ler veya tümüne izin vermek için "*"
    CORS_ORIGINS: str = "*" # Varsayılan olarak tümüne izin ver (geliştirme için)
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

settings = Settings()