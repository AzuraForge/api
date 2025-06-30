# Base image olarak Python 3.10'un slim versiyonunu kullan
FROM python:3.10-slim-bullseye

# Gerekli sistem paketlerini kur
RUN apt-get update && \
    apt-get install -y git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# Önce projenin TÜM dosyalarını kopyala.
COPY . .

# Tüm bağımlılıkları ve projeyi kur.
# -e modu artık CMD için gerekli değil, ancak geliştirme sırasında
# konteynere bağlanıp değişiklik yapmak için yararlı olabilir.
RUN pip install --no-cache-dir -e .[dev]

# === NİHAİ DEĞİŞİKLİK BURADA ===
# Projenin ana giriş modülünü doğrudan Python ile çalıştırıyoruz.
CMD ["python", "-m", "azuraforge_api.main"]
# === DEĞİŞİKLİK SONU ===