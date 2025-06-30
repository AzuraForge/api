# Base image olarak Python 3.10'un slim versiyonunu kullan
FROM python:3.10-slim-bullseye

# Gerekli sistem paketlerini kur
RUN apt-get update && \
    apt-get install -y git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# === BASİT VE GARANTİ YÖNTEM ===
# Önce projenin TÜM dosyalarını kopyala
COPY . .

# Şimdi, tüm dosyalar içerideyken, tek bir komutla her şeyi kur.
# -e modu sayesinde scriptler PATH'e eklenir ve bağımlılıklar çözülür.
RUN pip install --no-cache-dir -e .[dev]
# === BİTTİ ===

# Konteyner başlatıldığında çalıştırılacak komut
CMD ["start-api"]