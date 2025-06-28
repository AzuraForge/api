# ========== GÜNCELLENECEK DOSYA: api/src/azuraforge_api/services/experiment_service.py ==========
import json
import os
import glob
from importlib import resources
from typing import List, Dict, Any, Optional
from celery.result import AsyncResult 

from azuraforge_worker import celery_app
from azuraforge_worker.tasks.training_tasks import start_training_pipeline # Görevi import et

REPORTS_BASE_DIR = os.path.abspath(os.getenv("REPORTS_DIR", "/app/reports"))

def get_available_pipelines() -> List[Dict[str, Any]]:
    try:
        with resources.open_text("azuraforge_applications", "official_apps.json") as f:
            return json.load(f)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"ERROR: Could not find or read the official apps catalog. {e}")
        return []

def list_experiments() -> List[Dict[str, Any]]:
    experiment_files = glob.glob(f"{REPORTS_BASE_DIR}/**/results.json", recursive=True)
    experiments = []
    for f_path in experiment_files:
        try:
            with open(f_path, 'r') as f:
                data = json.load(f)
                experiments.append({
                    "id": data.get("experiment_id", os.path.basename(os.path.dirname(f_path))),
                    "status": data.get("status", "UNKNOWN"),
                    "pipeline_name": data.get("config", {}).get("pipeline_name", "N/A"),
                    "ticker": data.get("config", {}).get("data_sourcing", {}).get("ticker", "N/A"),
                    "final_loss": data.get("results", {}).get("final_loss"),
                })
        except Exception as e:
            print(f"Warning: Could not read results.json from {f_path}: {e}")
            continue
    experiments.sort(key=lambda x: x.get('id', ''), reverse=True)
    return experiments

def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    pipeline_name = config.get("pipeline_name", "unknown")
    print(f"Service: Sending task for pipeline '{pipeline_name}' to Celery.")
    task = start_training_pipeline.delay(config) 
    return {"message": "Experiment submitted to worker.", "task_id": task.id}

def get_task_status(task_id: str) -> Dict[str, Any]:
    task_result = AsyncResult(task_id, app=celery_app)
    status = task_result.state
    
    # --- KRİTİK DÜZELTME: Exception objesini string'e çevir ---
    details = task_result.info 
    if isinstance(details, Exception): # Eğer gelen bir hata objesiyse
        details = str(details) # Onu string'e çevirerek JSON serileştirme hatasını önle
    
    return {"task_id": task_id, "status": status, "result": details}