FROM python:3.10-slim-bullseye

RUN apt-get update && \
    apt-get install -y git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Başlangıç script'lerini kopyala ve çalıştırılabilir yap
COPY ./scripts/wait-for-it.sh /usr/local/bin/wait-for-it.sh
COPY ./scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh /usr/local/bin/entrypoint.sh

# === YENİ VE DOĞRU YAPI ===
# 1. Önce kaynak kodunu ve bağımlılık dosyalarını kopyala
COPY src ./src
COPY pyproject.toml setup.py ./

# 2. Şimdi bağımlılıkları kur. pip artık 'src' klasörünü bulabilir.
# Bu katman, sadece pyproject.toml veya setup.py değiştiğinde yeniden çalışır.
RUN pip install --no-cache-dir -e .[dev]

# 3. Geliştirme sırasında anında yansıma için geri kalan her şeyi kopyala
# (Dockerfile'lar, .env.example vs. gibi dosyalar)
COPY . .
# === YAPI SONU ===

# Konteynerin giriş noktası
ENTRYPOINT ["entrypoint.sh"]

# Varsayılan komut
CMD ["uvicorn", "azuraforge_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]