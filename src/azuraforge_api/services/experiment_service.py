# ========== GÜNCELLENECEK DOSYA: api/src/azuraforge_api/services/experiment_service.py ==========
import json
from importlib import resources
from typing import List, Dict, Any

# --- KRİTİK DÜZELTME: Worker'dan gerçek görevi import et ---
from azuraforge_worker.tasks.training_tasks import start_training_pipeline

def get_available_pipelines() -> List[Dict[str, Any]]:
    """'applications' paketinden resmi uygulama listesini okur."""
    try:
        with resources.open_text("azuraforge_applications", "official_apps.json") as f:
            return json.load(f)
    except (FileNotFoundError, ModuleNotFoundError):
        return []

def list_experiments() -> List[Dict[str, Any]]:
    """
    Bu fonksiyon ileride gerçek bir veritabanından veya Redis'ten görev durumlarını okuyacak.
    Şimdilik, dashboard'un çökmemesi için boş bir liste döndürüyor.
    """
    return []

def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    """Yeni bir deneyi Celery görevi olarak başlatır."""
    pipeline_name = config.get("pipeline_name", "unknown")
    print(f"Service: Sending task for pipeline '{pipeline_name}' to Celery.")
    task = start_training_pipeline.delay(config)
    return {"message": "Experiment submitted to worker.", "task_id": task.id}

def get_task_status(task_id: str) -> Dict[str, Any]:
    # ... (Bu fonksiyon daha sonra implemente edilecek)
    pass