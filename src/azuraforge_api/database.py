# api/src/azuraforge_api/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- DEĞİŞİKLİK: Veritabanı modeli tanımını buradan kaldırıyoruz ---
# Artık tüm modeller `azuraforge-dbmodels` paketinden gelecek.
# Bu, tüm servislerin aynı veritabanı şemasına sahip olmasını garanti eder
# ve "tek doğruluk kaynağı" ilkesini korur.

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("API: DATABASE_URL ortam değişkeni ayarlanmamış!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# `Base` ve `Experiment` sınıfının tanımı buradan kaldırıldı.
# `init_db` fonksiyonu da artık merkezi paketten çağrılacak.