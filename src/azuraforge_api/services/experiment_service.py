# api/src/azuraforge_api/services/experiment_service.py

import json
import itertools
import uuid
from datetime import datetime
from importlib import resources
from typing import List, Dict, Any, Generator
from fastapi import HTTPException
from celery.result import AsyncResult
from sqlalchemy import desc

from azuraforge_worker.database import SessionLocal, Experiment
from azuraforge_worker import celery_app
from azuraforge_worker.tasks.training_tasks import AVAILABLE_PIPELINES_AND_CONFIGS

# --- Helper Fonksiyonlar ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _generate_config_combinations(config: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    Konfigürasyon içindeki listeleri tespit eder ve tüm olası kombinasyonları üretir.
    Örn: {'lr': [0.1, 0.01], 'epochs': [50]} -> {'lr': 0.1, 'epochs': 50}, {'lr': 0.01, 'epochs': 50}
    """
    # Değişken parametreleri (değeri liste olanlar) bul
    varying_params = {}
    # Sabit parametreleri (değeri liste olmayanlar) bul
    static_params = {}
    
    # JSON içinde gezinmek için iç içe bir fonksiyon
    def _traverse_and_split(conf, path=""):
        for key, value in conf.items():
            new_path = f"{path}.{key}" if path else key
            if isinstance(value, list):
                varying_params[new_path] = value
            elif isinstance(value, dict):
                _traverse_and_split(value, new_path)
            else:
                static_params[new_path] = value

    _traverse_and_split(config)

    if not varying_params:
        # Değişken parametre yoksa, orijinal config'i tek bir eleman olarak döndür
        yield config
        return

    # Kombinasyonları oluştur
    param_names = list(varying_params.keys())
    param_values = list(varying_params.values())
    
    for combo in itertools.product(*param_values):
        new_config = {}
        # Önce tüm statik parametreleri kopyala
        for key_path, value in static_params.items():
            keys = key_path.split('.')
            d = new_config
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            d[keys[-1]] = value
            
        # Sonra bu kombinasyondaki değişken parametreleri ekle
        for i, key_path in enumerate(param_names):
            keys = key_path.split('.')
            d = new_config
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            d[keys[-1]] = combo[i]
            
        yield new_config

# --- API Servis Fonksiyonları ---

# ... get_available_pipelines ve get_default_pipeline_config aynı kalıyor ...
def get_available_pipelines() -> List[Dict[str, Any]]:
    #... (kod değişmedi)
    official_apps_data = []
    try:
        with resources.open_text("azuraforge_applications", "official_apps.json") as f:
            official_apps_data = json.load(f)
    except (FileNotFoundError, ModuleNotFoundError):
        pass
    
    available_pipelines = [app for app in official_apps_data if app.get("id") in AVAILABLE_PIPELINES_AND_CONFIGS]
    return available_pipelines

def get_default_pipeline_config(pipeline_id: str) -> Dict[str, Any]:
    #... (kod değişmedi)
    pipeline_info = AVAILABLE_PIPELINES_AND_CONFIGS.get(pipeline_id)
    if not pipeline_info:
        raise ValueError(f"Pipeline '{pipeline_id}' not found.")
    
    get_config_func = pipeline_info.get('get_config_func')
    if not get_config_func:
        return {"message": "No specific default configuration available."}
    return get_config_func()


def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Yeni bir deneyi veya deney grubunu başlatmak için Celery'ye görev(ler) gönderir.
    """
    task_ids = []
    # Batch ID ve Adı (eğer bir grup deneyi ise)
    batch_id = str(uuid.uuid4())
    batch_name = config.pop("batch_name", f"Batch-{datetime.now().strftime('%Y-%m-%d-%H%M')}")
    
    combinations = list(_generate_config_combinations(config))
    num_combinations = len(combinations)

    for single_config in combinations:
        # Eğer tek bir deney ise batch_id ve name'i null yap
        if num_combinations > 1:
            single_config['batch_id'] = batch_id
            single_config['batch_name'] = batch_name
        else:
            single_config['batch_id'] = None
            single_config['batch_name'] = None
            
        task = celery_app.send_task("start_training_pipeline", args=[single_config])
        task_ids.append(task.id)

    if num_combinations > 1:
        return {
            "message": f"{num_combinations} experiments submitted as a batch.",
            "batch_id": batch_id,
            "task_ids": task_ids
        }
    else:
        return {"message": "Experiment submitted to worker.", "task_id": task_ids[0]}

def list_experiments() -> List[Dict[str, Any]]:
    # ... (kod aynı, yeni alanlar otomatik gelecek şekilde güncellenmeli) ...
    with SessionLocal() as db:
        experiments = db.query(Experiment).order_by(desc(Experiment.created_at)).all()
        return [
            {
                "experiment_id": exp.id, "task_id": exp.task_id, "pipeline_name": exp.pipeline_name,
                "status": exp.status, "config": exp.config, "results": exp.results, "error": exp.error,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
                "failed_at": exp.failed_at.isoformat() if exp.failed_at else None,
                # YENİ ALANLAR
                "batch_id": exp.batch_id,
                "batch_name": exp.batch_name
            } for exp in experiments
        ]

def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    # ... (kod aynı, yeni alanlar otomatik gelecek şekilde güncellenmeli) ...
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
            # YENİ ALANLAR
            "batch_id": exp.batch_id,
            "batch_name": exp.batch_name
        }

def get_task_status(task_id: str) -> Dict[str, Any]:
    #... (kod değişmedi)
    task_result = AsyncResult(task_id, app=celery_app)
    return {"status": task_result.state, "details": task_result.info}