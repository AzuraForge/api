FROM python:3.10-slim-bullseye

RUN apt-get update && \
    apt-get install -y git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Başlangıç script'lerini kopyala ve çalıştırılabilir yap
COPY ./scripts/wait-for-it.sh /usr/local/bin/wait-for-it.sh
COPY ./scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh /usr/local/bin/entrypoint.sh

COPY . .

RUN pip install --no-cache-dir -e .[dev]

# Konteynerin giriş noktası
ENTRYPOINT ["entrypoint.sh"]

# Varsayılan komut
CMD ["uvicorn", "azuraforge_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]