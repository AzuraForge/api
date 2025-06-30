# Base image olarak Python 3.10'un slim versiyonunu kullan
FROM python:3.10-slim-bullseye

# Gerekli sistem paketlerini kur
RUN apt-get update && \
    apt-get install -y git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# Önce projenin TÜM dosyalarını kopyala
COPY . .

# Tüm bağımlılıkları ve projeyi kur
RUN pip install --no-cache-dir .[dev]

# Konteyner başlatıldığında çalıştırılacak komut (en sağlam yöntem)
CMD ["python", "-m", "azuraforge_api.main"]