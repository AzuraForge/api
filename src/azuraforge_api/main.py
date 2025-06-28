# ========== GÜNCELLENECEK DOSYA: api/src/azuraforge_api/main.py ==========
import uvicorn
import subprocess
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
# Tüm router modüllerini import et
from .routes import experiments, pipelines, streaming

def create_app() -> FastAPI:
    """FastAPI uygulamasını oluşturur ve yapılandırır."""
    app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Her router'ı kendi mantıksal yoluyla kaydet
    app.include_router(experiments.router, prefix=settings.API_V1_PREFIX)
    app.include_router(pipelines.router, prefix=settings.API_V1_PREFIX)
    # WebSocket router'ını dahil et (genellikle prefix'i olmaz)
    app.include_router(streaming.router)

    @app.get("/", tags=["Root"])
    def read_root():
        return {"message": f"Welcome to {settings.PROJECT_NAME}"}
        
    return app

app = create_app()

def run_server():
    """'start-api' komutu için giriş noktası."""
    print(f"🚀 Starting {settings.PROJECT_NAME}...")
    uvicorn.run("azuraforge_api.main:app", host="0.0.0.0", port=8000, reload=True)