# api/src/azuraforge_api/services/experiment_service.py

import json
import os
import glob
from importlib import resources
from typing import List, Dict, Any
from celery.result import AsyncResult 
from fastapi import HTTPException

from azuraforge_worker import celery_app
# Bu importun çalışması için worker'ın -e ile kurulmuş olması gerekir.
# Docker build sırasında bu sağlanır.
from azuraforge_worker.tasks.training_tasks import AVAILABLE_PIPELINES_AND_CONFIGS

REPORTS_BASE_DIR = os.path.abspath(os.getenv("REPORTS_DIR", "/app/reports"))

def get_available_pipelines() -> List[Dict[str, Any]]:
    """
    Sisteme kurulu ve "resmi" olarak listelenmiş pipeline'ları döndürür.
    """
    official_apps_data = []
    try:
        # Uygulama katalogunu oku
        with resources.open_text("azuraforge_applications", "official_apps.json") as f:
            official_apps_data = json.load(f)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"ERROR: Could not find or read the official apps catalog. {e}")

    # Sadece worker tarafından gerçekten keşfedilen pipeline'ları filtrele
    available_pipelines_with_configs = []
    for app_meta in official_apps_data:
        app_id = app_meta.get("id")
        if app_id in AVAILABLE_PIPELINES_AND_CONFIGS:
            available_pipelines_with_configs.append(app_meta)
    
    return available_pipelines_with_configs

def get_default_pipeline_config(pipeline_id: str) -> Dict[str, Any]:
    """
    Belirli bir pipeline'ın varsayılan konfigürasyonunu döndürür.
    """
    pipeline_info = AVAILABLE_PIPELINES_AND_CONFIGS.get(pipeline_id)
    if not pipeline_info:
        raise ValueError(f"Pipeline '{pipeline_id}' not found or its config function is missing.")
    
    get_config_func = pipeline_info.get('get_config_func')
    if not get_config_func:
        return {"message": "No specific default configuration available for this pipeline."}

    return get_config_func()

def list_experiments() -> List[Dict[str, Any]]:
    """
    Raporlar dizinindeki tüm deneylerin `results.json` dosyalarını okur ve
    bir liste olarak döndürür.
    """
    experiment_files = glob.glob(f"{REPORTS_BASE_DIR}/**/results.json", recursive=True)
    experiments = []
    for f_path in experiment_files:
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                experiments.append(data)
        except Exception as e:
            print(f"Warning: Could not read or parse {f_path}: {e}")
            continue
    
    # En yeniden en eskiye doğru sırala
    experiments.sort(key=lambda x: x.get('config', {}).get('start_time', ''), reverse=True)
    return experiments

def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Yeni bir deneyi başlatmak için Celery'ye bir görev gönderir.
    """
    # Celery görevinin adını doğrudan belirtmek daha güvenilirdir.
    task = celery_app.send_task("start_training_pipeline", args=[config])
    return {"message": "Experiment submitted to worker.", "task_id": task.id}

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Belirli bir Celery görevinin anlık durumunu döndürür.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == 'SUCCESS':
        # Başarılı görevlerde sonuç (result) genellikle büyük olabilir,
        # bu yüzden doğrudan sonucu döndürmek yerine sadece durumu bildirebiliriz.
        # /details endpoint'i tam sonucu almak için kullanılmalıdır.
        return {"status": "SUCCESS"}
    elif task_result.state == 'FAILURE':
        return {"status": "FAILURE", "error": str(task_result.info)}
    else: # PENDING, PROGRESS, etc.
        return {"status": task_result.state, "details": task_result.info}

# YENİ FONKSİYON (get_experiment_report yerine)
def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    """
    Belirli bir deneye ait results.json dosyasının tüm içeriğini döndürür.
    Bu, UI'da dinamik rapor oluşturmak için kullanılır.
    """
    # Güvenlik: Path traversal saldırılarını önle
    if ".." in experiment_id or "/" in experiment_id or "\\" in experiment_id:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format.")

    # Rapor dosyasını bulmak için tüm alt dizinlerde ara
    report_path_pattern = os.path.join(REPORTS_BASE_DIR, "**", experiment_id, "results.json")
    report_files = glob.glob(report_path_pattern, recursive=True)

    if not report_files:
        raise HTTPException(status_code=404, detail=f"Details for experiment '{experiment_id}' not found.")
    
    report_path = report_files[0]

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read details file: {e}")