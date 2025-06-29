# ========== GÜNCELLENECEK DOSYA: api/src/azuraforge_api/main.py ==========
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .routes import experiments, pipelines, streaming

def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")
    
    # CORS ayarlarını dinamik olarak belirle
    if settings.CORS_ORIGINS == "*":
        allowed_origins = ["*"]
    else:
        allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(',')]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins, # <-- Burası değişti
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- KRİTİK DÜZELTME: Prefix'i geri ekliyoruz ---
    app.include_router(experiments.router, prefix=settings.API_V1_PREFIX)
    app.include_router(pipelines.router, prefix=settings.API_V1_PREFIX)
    app.include_router(streaming.router) # WebSocket router'ı eklendi
    
    @app.get("/", tags=["Root"])
    def read_root():
        return {"message": f"Welcome to {settings.PROJECT_NAME}"}
        
    return app

app = create_app()

def run_server():
    print(f"🚀 Starting {settings.PROJECT_NAME}...")
    uvicorn.run("azuraforge_api.main:app", host="0.0.0.0", port=8000, reload=True)