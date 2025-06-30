# Base image olarak Python 3.10'un slim versiyonunu kullan
FROM python:3.10-slim-bullseye

# Gerekli sistem paketlerini kur
RUN apt-get update && \
    apt-get install -y git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# Önce SADECE bağımlılık dosyalarını kopyala
COPY pyproject.toml .
COPY setup.py .

# SADECE dış bağımlılıkları kur
RUN pip install --no-cache-dir -r <(grep -E '^[a-zA-Z]' pyproject.toml | sed -e 's/\[.*\]//' -e "s/ //g" -e "s/==.*//")

# Şimdi kaynak kodunu kopyala
COPY src ./src

# Son olarak projenin kendisini "düzenlenebilir" modda kur
RUN pip install --no-cache-dir -e .

# Konteyner başlatıldığında çalıştırılacak komut
CMD ["start-api"]