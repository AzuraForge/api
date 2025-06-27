# ========== DOSYA: src/azuraforge_api/main.py ==========
import uvicorn
import subprocess
import sys
from fastapi import FastAPI
from .core.config import settings
from .routes import experiments

def create_app() -> FastAPI:
    """FastAPI uygulamasını oluşturur ve yapılandırır."""
    app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")
    
    # CORS (Cross-Origin Resource Sharing)
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API Rotalarını dahil et
    app.include_router(experiments.router, prefix=settings.API_V1_PREFIX, tags=["Experiments"])

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

def run_celery_worker():
    """'start-worker' komutu için giriş noktası."""
    print("👷‍♂️ Worker servisi henüz bu repoda tanımlanmadı. Lütfen AzuraForge/worker'ı kullanın.")
    # Şimdilik bu komut bir şey yapmayacak, çünkü worker ayrı bir repo olacak.
    pass