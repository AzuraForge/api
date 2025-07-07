FROM python:3.10-slim-bullseye

RUN apt-get update && \
    apt-get install -y git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Önce sadece bağımlılık tanımlarını kopyala
COPY pyproject.toml setup.py ./

# Bağımlılıkları kur. Bu katman sadece toml/setup değiştiğinde yeniden çalışır.
# .[dev] ile geliştirme bağımlılıklarını da kuruyoruz.
RUN pip install --no-cache-dir -e .[dev]

# Şimdi geri kalan tüm kodları ve scriptleri kopyala
COPY . .

# Başlangıç script'lerini kopyala ve çalıştırılabilir yap
# Bu scriptler artık /app içinde olacak.
COPY ./scripts/wait-for-it.sh /usr/local/bin/wait-for-it.sh
COPY ./scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh /usr/local/bin/entrypoint.sh

# Konteynerin giriş noktası
ENTRYPOINT ["entrypoint.sh"]

# Varsayılan komut
CMD ["uvicorn", "azuraforge_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]