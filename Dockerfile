# Base image olarak Python 3.10'un slim versiyonunu kullan
FROM python:3.10-slim-bullseye

# Gerekli sistem paketlerini kur
# DİKKAT: Artık 'nc' (netcat) kurmamıza gerek yok.
RUN apt-get update && \
    apt-get install -y git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# === YENİ ADIM: Bekleme scriptini kopyala ve çalıştırılabilir yap ===
COPY ./scripts/wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh
# === YENİ ADIM SONU ===

# Önce projenin TÜM dosyalarını kopyala
COPY . .

# Şimdi, tüm dosyalar içerideyken, tek bir komutla her şeyi kur.
RUN pip install --no-cache-dir -e .[dev]

# Konteyner başlatıldığında çalıştırılacak komut
# Artık docker-compose.yml tarafından yönetiliyor, bu satır sadece referans.
CMD ["uvicorn", "azuraforge_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]