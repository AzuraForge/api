# api/src/azuraforge_api/services/experiment_service.py

import json
from importlib import resources
from typing import List, Dict, Any
from fastapi import HTTPException
from celery.result import AsyncResult
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Worker'dan veritabanı modelini ve oturumunu import ediyoruz
# Bu, 'azuraforge-worker' paketinin kurulu olmasına bağlıdır.
from azuraforge_worker.database import SessionLocal, Experiment
from azuraforge_worker import celery_app
from azuraforge_worker.tasks.training_tasks import AVAILABLE_PIPELINES_AND_CONFIGS

def get_db():
    """Dependency Injection için veritabanı oturumu sağlar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pipeline Fonksiyonları (Değişiklik Yok) ---
def get_available_pipelines() -> List[Dict[str, Any]]:
    official_apps_data = []
    try:
        with resources.open_text("azuraforge_applications", "official_apps.json") as f:
            official_apps_data = json.load(f)
    except (FileNotFoundError, ModuleNotFoundError):
        pass
    
    available_pipelines = [app for app in official_apps_data if app.get("id") in AVAILABLE_PIPELINES_AND_CONFIGS]
    return available_pipelines

def get_default_pipeline_config(pipeline_id: str) -> Dict[str, Any]:
    pipeline_info = AVAILABLE_PIPELINES_AND_CONFIGS.get(pipeline_id)
    if not pipeline_info:
        raise ValueError(f"Pipeline '{pipeline_id}' not found.")
    
    get_config_func = pipeline_info.get('get_config_func')
    if not get_config_func:
        return {"message": "No specific default configuration available."}
    return get_config_func()

# --- Deney Fonksiyonları (Tamamen Yenilendi) ---

def list_experiments() -> List[Dict[str, Any]]:
    """Veritabanındaki tüm deneyleri en yeniden eskiye doğru listeler."""
    with SessionLocal() as db:
        # JSON alanlarının tamamını çekmek yerine sadece gerekli alanları çekmek daha performanslı olabilir
        # ama şimdilik her şeyi çekmek daha kolay.
        experiments = db.query(Experiment).order_by(desc(Experiment.created_at)).all()
        # SQLAlchemy nesnelerini Pydantic veya dict'e dönüştürmek gerekir. Şimdilik manuel yapalım.
        return [
            {
                "experiment_id": exp.id, "task_id": exp.task_id, "pipeline_name": exp.pipeline_name,
                "status": exp.status, "config": exp.config, "results": exp.results, "error": exp.error,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
                "failed_at": exp.failed_at.isoformat() if exp.failed_at else None,
            } for exp in experiments
        ]

def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    """Yeni bir deneyi başlatmak için Celery'ye bir görev gönderir."""
    task = celery_app.send_task("start_training_pipeline", args=[config])
    return {"message": "Experiment submitted to worker.", "task_id": task.id}

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Celery görevinin durumunu döndürür."""
    task_result = AsyncResult(task_id, app=celery_app)
    return {"status": task_result.state, "details": task_result.info}

def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    """Belirli bir deneyin tüm detaylarını veritabanından çeker."""
    with SessionLocal() as db:
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")
        
        return {
            "experiment_id": exp.id, "task_id": exp.task_id, "pipeline_name": exp.pipeline_name,
            "status": exp.status, "config": exp.config, "results": exp.results, "error": exp.error,
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
            "failed_at": exp.failed_at.isoformat() if exp.failed_at else None,
        }