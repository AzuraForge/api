# api/src/azuraforge_api/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Uygulama genelindeki tüm konfigürasyonları ve ortam değişkenlerini yönetir.
    Pydantic, .env dosyasını otomatik olarak okur ve değişkenleri doğrular.
    """
    PROJECT_NAME: str = "AzuraForge API"
    API_V1_PREFIX: str = "/api/v1"
    
    CORS_ORIGINS: str = "*" 
    
    # --- JWT Ayarları ---
    # Bu değişkenler, .env dosyasından veya doğrudan ortam değişkeni olarak
    # sağlanmalıdır. Eğer sağlanmazsa, Pydantic bir hata fırlatacaktır.
    # Bu, uygulamanın güvensiz bir anahtarla çalışmasını engeller.
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 gün varsayılan
    ALGORITHM: str = "HS256" # Algoritma sabit

    # model_config, Pydantic'e ayarlarını nereden okuyacağını söyler.
    # .env dosyasını okumak için env_file ayarını kullanıyoruz.
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        extra='ignore' # .env dosyasındaki ekstra alanları görmezden gel
    )

# Ayarları tek bir yerden import etmek için bir 'settings' nesnesi oluşturuyoruz.
settings = Settings()