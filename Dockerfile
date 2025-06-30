# Base image olarak Python 3.10'un slim versiyonunu kullan
FROM python:3.10-slim-bullseye

# Gerekli sistem paketlerini kur
RUN apt-get update && \
    apt-get install -y git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# === BASİTLEŞTİRİLMİŞ YAPI ===
# Önce projenin TÜM dosyalarını kopyala. Bu, en sağlam yöntemdir.
COPY . .

# Şimdi, tüm dosyalar içerideyken, tek bir komutla her şeyi kur.
# pip, pyproject.toml'u okuyacak ve tüm bağımlılıkları kendisi çözecektir.
RUN pip install --no-cache-dir -e .[dev]
# === BİTTİ ===

# Konteyner başlatıldığında çalıştırılacak komut
CMD ["start-api"]