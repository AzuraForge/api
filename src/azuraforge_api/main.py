# api/src/azuraforge_api/main.py

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import settings
from .routes import experiments, pipelines, streaming, auth
from .services import user_service
from .database import SessionLocal

# --- DEĞİŞİKLİK: init_db fonksiyonunu merkezi paketten import ediyoruz ---
from azuraforge_dbmodels import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API: Veritabanı tabloları kontrol ediliyor/oluşturuluyor...")
    # --- DEĞİŞİKLİK: Merkezi init_db fonksiyonu çağrılıyor ---
    init_db()
    print("API: Veritabanı hazır.")
    
    db = SessionLocal()
    try:
        user_service.create_default_user_if_not_exists(db)
    finally:
        db.close()
    
    print("API: Uygulama başlangıcı tamamlandı. İstekler kabul ediliyor.")
    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME, 
        version="0.1.0",
        lifespan=lifespan,
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc"
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
    api_router.include_router(auth.router)
    api_router.include_router(experiments.router)
    api_router.include_router(pipelines.router)
    
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(streaming.router)
    
    @app.get("/", tags=["Root"])
    def read_root():
        return {"message": f"Welcome to {settings.PROJECT_NAME}"}
        
    return app

app = create_app()