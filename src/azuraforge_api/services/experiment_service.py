# api/src/azuraforge_api/services/experiment_service.py

import json
import os
import glob
from importlib import resources
from typing import List, Dict, Any
from celery.result import AsyncResult 
from fastapi import HTTPException

from azuraforge_worker import celery_app
from azuraforge_worker.tasks.training_tasks import AVAILABLE_PIPELINES_AND_CONFIGS

REPORTS_BASE_DIR = os.path.abspath(os.getenv("REPORTS_DIR", "/app/reports"))

def get_available_pipelines() -> List[Dict[str, Any]]:
    official_apps_data = []
    try:
        with resources.open_text("azuraforge_applications", "official_apps.json") as f:
            official_apps_data = json.load(f)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"ERROR: Could not find or read the official apps catalog. {e}")

    available_pipelines_with_configs = []
    for app_meta in official_apps_data:
        app_id = app_meta.get("id")
        if app_id in AVAILABLE_PIPELINES_AND_CONFIGS:
            available_pipelines_with_configs.append(app_meta)
    
    return available_pipelines_with_configs

def get_default_pipeline_config(pipeline_id: str) -> Dict[str, Any]:
    pipeline_info = AVAILABLE_PIPELINES_AND_CONFIGS.get(pipeline_id)
    if not pipeline_info:
        raise ValueError(f"Pipeline '{pipeline_id}' not found.")
    
    get_config_func = pipeline_info.get('get_config_func')
    if not get_config_func:
        return {}

    return get_config_func()

def list_experiments() -> List[Dict[str, Any]]:
    experiment_files = glob.glob(f"{REPORTS_BASE_DIR}/**/results.json", recursive=True)
    experiments = []
    for f_path in experiment_files:
        try:
            with open(f_path, 'r') as f:
                data = json.load(f)
                experiments.append(data)
        except Exception as e:
            print(f"Warning: Could not read or parse {f_path}: {e}")
            continue
    
    experiments.sort(key=lambda x: x.get('config', {}).get('start_time', ''), reverse=True)
    return experiments

def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    task = celery_app.send_task("start_training_pipeline", args=[config])
    return {"message": "Experiment submitted to worker.", "task_id": task.id}

def get_task_status(task_id: str) -> Dict[str, Any]:
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == 'SUCCESS':
        return task_result.result
    elif task_result.state == 'FAILURE':
        return {"status": "FAILURE", "error": str(task_result.info)}
    else:
        return {"status": task_result.state, "details": task_result.info}

# YENİ FONKSİYON
def get_experiment_report(experiment_id: str) -> str:
    """
    Belirli bir deneye ait report.md dosyasının içeriğini döndürür.
    """
    # Güvenlik: Path traversal saldırılarını önle
    if ".." in experiment_id or "/" in experiment_id or "\\" in experiment_id:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format.")

    # Rapor dosyasını bulmak için tüm alt dizinlerde ara
    report_path_pattern = os.path.join(REPORTS_BASE_DIR, "**", experiment_id, "report.md")
    report_files = glob.glob(report_path_pattern, recursive=True)

    if not report_files:
        raise HTTPException(status_code=404, detail=f"Report for experiment '{experiment_id}' not found.")
    
    # Birden fazla bulunması beklenmez, ama ilkini alalım
    report_path = report_files[0]

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read report file: {e}")