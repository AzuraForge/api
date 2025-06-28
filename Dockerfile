# ========== DOSYA: api/Dockerfile ==========
FROM python:3.10-slim-bullseye

# Konteyner içinde uygulama kodu için bir çalışma dizini belirle
WORKDIR /app

# pyproject.toml ve setup.py'ı kopyala (bağımlılıkları kurmak için)
COPY pyproject.toml .
COPY setup.py .

# Bağımlılıkları kur. Bu komut, smart-learner, learner, applications ve worker'ı da Gitten çekecek.
# "--no-cache-dir" ile pip cache'ini kullanma, her zaman güncel indir.
RUN pip install --no-cache-dir .

# Uygulamanın kalan kodunu kopyala
COPY src ./src

# Konteyner başlatıldığında çalışacak varsayılan komut
# Bu, docker-compose.yml'da ezilir.
CMD ["start-api"]