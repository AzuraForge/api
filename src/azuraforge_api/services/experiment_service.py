# ========== GÜNCELLENECEK DOSYA: api/src/azuraforge_api/services/experiment_service.py ==========
import json
import os
import glob
from importlib import resources
from typing import List, Dict, Any, Optional
from celery.result import AsyncResult 

# --- KRİTİK DÜZELTME: Worker'dan gerçek görevi import et ---
# Bu import, 'azuraforge-worker' paketini gerektirir.
from azuraforge_worker.tasks.training_tasks import start_training_pipeline

# Worker projesinden Celery uygulamasını import et
from azuraforge_worker import celery_app

# Rapor Dizini
REPORTS_BASE_DIR = os.path.abspath(os.getenv("REPORTS_DIR", "/app/reports"))

def get_available_pipelines() -> List[Dict[str, Any]]:
    """
    'azuraforge-applications' paketinden resmi uygulama listesini okur.
    Dashboard'un "Yeni Deney Başlat" formundaki seçenekleri doldurmak için kullanılır.
    """
    try:
        # 'azuraforge_applications' paketi içindeki 'official_apps.json' dosyasını oku
        with resources.open_text("azuraforge_applications", "official_apps.json") as f:
            return json.load(f)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"ERROR: Could not find or read the official apps catalog. {e}")
        return []

def list_experiments() -> List[Dict[str, Any]]:
    """
    Diskteki tüm 'results.json' dosyalarını tarayarak deneyleri listeler.
    Dashboard'daki "Deney Listesi" sekmesini doldurur.
    """
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
    """Yeni bir deneyi Celery görevi olarak başlatır."""
    pipeline_name = config.get("pipeline_name", "unknown")
    print(f"Service: Sending task for pipeline '{pipeline_name}' to Celery.")
    # start_training_pipeline görevi Celery'ye gönderilir.
    # config'e sadece pipeline_name ekliyoruz, diğer config bilgileri worker'da varsayılan olarak alınacak.
    task = start_training_pipeline.delay(config) 
    return {"message": "Experiment submitted to worker.", "task_id": task.id}

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Belirli bir Celery görevinin anlık durumunu döndürür."""
    task_result = AsyncResult(task_id, app=celery_app)
    status = task_result.state
    result = task_result.result if task_result.ready() else task_result.info 
    return {"task_id": task_id, "status": status, "result": result}