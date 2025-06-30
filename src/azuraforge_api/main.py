# api/src/azuraforge_api/main.py

import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import settings
from .routes import experiments, pipelines, streaming
# === DEĞİŞİKLİK BURADA: Kendi veritabanı modülümüzden import ediyoruz ===
from .database import Base, engine 
# === DEĞİŞİKLİK SONU ===

def init_db():
    """Veritabanı tablolarını oluşturur."""
    Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API: Veritabanı tabloları kontrol ediliyor/oluşturuluyor...")
    init_db()
    print("API: Veritabanı hazır.")
    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME, 
        version="0.1.0",
        lifespan=lifespan
    )
    
    if settings.CORS_ORIGINS == "*":
        allowed_origins = ["*"]
    else:
        allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(',')]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_router = APIRouter()
    api_router.include_router(experiments.router)
    api_router.include_router(pipelines.router)
    
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(streaming.router)
    
    @app.get("/", tags=["Root"])
    def read_root():
        return {"message": f"Welcome to {settings.PROJECT_NAME}"}
        
    return app

app = create_app()

def run_server():
    print(f"🚀 Starting {settings.PROJECT_NAME}...")
    uvicorn.run("azuraforge_api.main:app", host="0.0.0.0", port=8000, reload=True)