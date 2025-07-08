FROM python:3.10-slim-bullseye

RUN apt-get update && \
    apt-get install -y git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Başlangıç script'lerini kopyala ve çalıştırılabilir yap
COPY ./scripts/wait-for-it.sh /usr/local/bin/wait-for-it.sh
COPY ./scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh /usr/local/bin/entrypoint.sh

# === YENİ VE DAHA SAĞLAM YAPI ===
# Önce projenin TÜM dosyalarını kopyala.
# Bu, kardeş repolardaki (dbmodels, learner vb.) değişikliklerin de
# Docker tarafından algılanmasını ve cache'in kırılmasını sağlar.
COPY . .

# Şimdi bağımlılıkları kur. Bu katman, kaynak kodundaki herhangi bir
# değişiklikte yeniden çalışacaktır.
RUN pip install --no-cache-dir -e .[dev]
# === YAPI SONU ===

# Konteynerin giriş noktası
ENTRYPOINT ["entrypoint.sh"]

# Varsayılan komut
CMD ["uvicorn", "azuraforge_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]