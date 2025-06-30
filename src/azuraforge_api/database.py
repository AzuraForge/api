# api/src/azuraforge_api/database.py

import os
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("API: DATABASE_URL ortam değişkeni ayarlanmamış!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# === YENİ BÖLÜM: Model tanımını buraya ekliyoruz ===
Base = declarative_base()

class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, index=True, nullable=False)
    batch_id = Column(String, index=True, nullable=True)
    batch_name = Column(String, nullable=True)
    pipeline_name = Column(String, index=True, nullable=False)
    status = Column(String, index=True, default="PENDING")
    config = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    error = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
# === DEĞİŞİKLİK SONU ===