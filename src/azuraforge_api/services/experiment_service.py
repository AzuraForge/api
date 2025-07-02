# api/src/azuraforge_api/services/experiment_service.py

import json
import itertools
import uuid
import os
import redis
from datetime import datetime
from typing import List, Dict, Any, Generator
from fastapi import HTTPException
from celery.result import AsyncResult
from sqlalchemy import desc
from importlib import resources

from ..database import SessionLocal, Experiment
from azuraforge_worker import celery_app

# --- YENİ BÖLÜM: Redis'ten Pipeline Bilgisi Alma ---

REDIS_PIPELINES_KEY = "azuraforge:pipelines_catalog"

def get_pipelines_from_redis() -> List[Dict[str, Any]]:
    """
    Worker tarafından Redis'e kaydedilmiş olan pipeline kataloğunu okur.
    Bu, API'ın Worker'ın iç yapısını bilmesini engeller.
    """
    try:
        redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
        r = redis.from_url(redis_url, decode_responses=True)
        
        official_apps_data = []
        try:
            with resources.open_text("azuraforge_applications", "official_apps.json") as f:
                official_apps_data = json.load(f)
        except (FileNotFoundError, ModuleNotFoundError) as e:
            print(f"Warning: Could not load official_apps.json: {e}")
            official_apps_data = []
        
        official_apps_map = {app['id']: app for app in official_apps_data}

        pipeline_catalog_raw = r.hgetall(REDIS_PIPELINES_KEY)
        
        if not pipeline_catalog_raw:
            print("Warning: Pipeline catalog not found in Redis. Is the worker running?")
            return []

        pipelines = []
        for name, data_str in pipeline_catalog_raw.items():
            pipeline_data = json.loads(data_str)
            official_meta = official_apps_map.get(name, {})
            pipeline_data['name'] = official_meta.get('name', name)
            pipeline_data['description'] = official_meta.get('description', 'No description available.')
            pipeline_data['repository'] = official_meta.get('repository', '')
            pipelines.append(pipeline_data)
            
        return sorted(pipelines, key=lambda p: p.get('name', p['id']))
        
    except redis.exceptions.ConnectionError as e:
        print(f"API Critical Error: Could not connect to Redis to get pipelines: {e}")
        return []
    except Exception as e:
        print(f"API Error: An unexpected error occurred while fetching pipelines from Redis: {e}")
        return []

# --- Helper Fonksiyonlar ---

def _generate_config_combinations(config: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    Konfigürasyon içindeki listeleri tespit eder ve tüm olası kombinasyonları üretir.
    """
    varying_params = {}
    static_params = {}
    
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
        yield config
        return

    param_names = list(varying_params.keys())
    param_values = list(varying_params.values())
    
    for combo in itertools.product(*param_values):
        new_config = {}
        for key_path, value in static_params.items():
            keys = key_path.split('.')
            d = new_config
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            d[keys[-1]] = value
            
        for i, key_path in enumerate(param_names):
            keys = key_path.split('.')
            d = new_config
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            d[keys[-1]] = combo[i]
            
        yield new_config


# --- API Servis Fonksiyonları ---

def get_available_pipelines() -> List[Dict[str, Any]]:
    """Yüklü tüm pipeline eklentilerini Redis üzerinden keşfederek döndürür."""
    pipelines = get_pipelines_from_redis()
    for p in pipelines:
        p.pop('default_config', None)
    return pipelines

def get_default_pipeline_config(pipeline_id: str) -> Dict[str, Any]:
    """Belirli bir pipeline'ın Redis'te kayıtlı olan varsayılan konfigürasyonunu döndürür."""
    pipelines = get_pipelines_from_redis()
    pipeline_info = next((p for p in pipelines if p['id'] == pipeline_id), None)

    if not pipeline_info:
        raise ValueError(f"Pipeline '{pipeline_id}' not found in the Redis catalog.")
    
    return pipeline_info.get('default_config', {"message": "No specific default configuration available."})

def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    """Yeni bir veya birden fazla deney başlatır (batch)."""
    task_ids = []
    batch_id = str(uuid.uuid4())
    batch_name = config.pop("batch_name", f"Batch-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}")
    
    combinations = list(_generate_config_combinations(config))
    num_combinations = len(combinations)

    for single_config in combinations:
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
    """
    Veritabanındaki tüm deneylerin özetini VE TAM DETAYLARINI (config, results)
    en yeniden eskiye doğru listeler.
    """
    db = SessionLocal()
    try:
        experiments_from_db = db.query(Experiment).order_by(desc(Experiment.created_at)).all()
        
        all_experiments_data = []
        for exp in experiments_from_db:
            # Güvenli erişim için bir helper fonksiyon
            def safe_get(d, keys, default=None):
                if not isinstance(d, dict): return default
                for key in keys:
                    if not isinstance(d, dict) or key not in d: return default
                    d = d[key]
                return d

            summary = {
                "experiment_id": exp.id,
                "task_id": exp.task_id,
                "pipeline_name": exp.pipeline_name,
                "status": exp.status,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
                "failed_at": exp.failed_at.isoformat() if exp.failed_at else None,
                "batch_id": exp.batch_id,
                "batch_name": exp.batch_name,
                "config_summary": {
                    "ticker": safe_get(exp.config, ["data_sourcing", "ticker"], "N/A"),
                    "epochs": safe_get(exp.config, ["training_params", "epochs"], "N/A"),
                    "lr": safe_get(exp.config, ["training_params", "lr"], "N/A"),
                },
                "results_summary": {
                    "final_loss": safe_get(exp.results, ["final_loss"]),
                    "r2_score": safe_get(exp.results, ["metrics", "r2_score"]),
                    "mae": safe_get(exp.results, ["metrics", "mae"]),
                },
                "config": exp.config, 
                "results": exp.results, 
                "error": exp.error
            }
            all_experiments_data.append(summary)
        return all_experiments_data
    finally:
        db.close()

def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    """Belirli bir deneyin tüm detaylarını veritabanından çeker."""
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")
        
        return {
            "experiment_id": exp.id, "task_id": exp.task_id, "pipeline_name": exp.pipeline_name,
            "status": exp.status, "config": exp.config, "results": exp.results, "error": exp.error,
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
            "failed_at": exp.failed_at.isoformat() if exp.failed_at else None,
            "batch_id": exp.batch_id, "batch_name": exp.batch_name,
        }
    finally:
        db.close()

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Belirli bir Celery görevinin anlık durumunu döndürür (Celery'den doğrudan sorgu)."""
    task_result = AsyncResult(task_id, app=celery_app)
    return {"status": task_result.state, "details": task_result.info}