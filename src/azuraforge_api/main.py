import uvicorn
from fastapi import FastAPI, APIRouter # DÜZELTME: APIRouter'ı import et
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
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # DÜZELTME: İç içe FastAPI uygulaması yerine tek bir APIRouter kullanıyoruz.
    # Bu, "AttributeError: 'FastAPI' object has no attribute 'default_response_class'"
    # hatasını çözer.
    api_router = APIRouter()
    api_router.include_router(experiments.router)
    api_router.include_router(pipelines.router)
    
    # Şimdi bu birleştirilmiş router'ı tek bir prefix ile ana uygulamaya ekliyoruz.
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    # WebSocket router'ı prefix dışında, doğrudan ana uygulamaya ekleniyor.
    app.include_router(streaming.router)
    
    @app.get("/", tags=["Root"])
    def read_root():
        return {"message": f"Welcome to {settings.PROJECT_NAME}"}
        
    return app

app = create_app()

def run_server():
    print(f"🚀 Starting {settings.PROJECT_NAME}...")
    uvicorn.run("azuraforge_api.main:app", host="0.0.0.0", port=8000, reload=True)