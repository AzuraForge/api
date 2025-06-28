# ========== GÜNCELLENECEK DOSYA: api/src/azuraforge_api/main.py ==========
import uvicorn
import subprocess
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
# Her iki router modülünü de import et
from .routes import experiments, pipelines

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
    app.include_router(
        experiments.router, 
        prefix=f"{settings.API_V1_PREFIX}/experiments", 
        tags=["Experiments"]
    )
    app.include_router(
        pipelines.router, 
        prefix=f"{settings.API_V1_PREFIX}/pipelines", # <-- Pipelines için ayrı prefix
        tags=["Pipelines"]
    )

    @app.get("/", tags=["Root"])
    def read_root():
        return {"message": f"Welcome to {settings.PROJECT_NAME}"}
        
    return app

app = create_app()

# --- Komut Satırı Giriş Noktaları ---
def run_server():
    """'start-api' komutu için giriş noktası."""
    print(f"🚀 Starting {settings.PROJECT_NAME}...")
    uvicorn.run("azuraforge_api.main:app", host="0.0.0.0", port=8000, reload=True)

# Worker artık kendi reposunda olduğu için bu fonksiyon burada olmamalı.
# Ama test kolaylığı için bırakabiliriz veya silebiliriz. En temizi silmek.
# def run_celery_worker(): ...