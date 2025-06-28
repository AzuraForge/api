# ========== GÜNCELLENECEK DOSYA: api/src/azuraforge_api/services/experiment_service.py ==========
import json
from importlib import resources # Paket kaynaklarını okumak için en doğru yöntem
from typing import List, Dict, Any

def get_available_pipelines() -> List[Dict[str, Any]]:
    """
    Kurulu 'azuraforge-applications' paketinden resmi uygulama listesini okur.
    """
    try:
        with resources.open_text("azuraforge_applications", "official_apps.json") as f:
            return json.load(f)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"ERROR: Could not find or read the official apps catalog. {e}")
        return []
    
def list_experiments() -> List[Dict[str, Any]]:
    # ... (bu fonksiyon aynı kalabilir)
    return [{"id": "exp_123", "name": "dummy_experiment", "status": "completed"}]

def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    """Yeni bir deneyi başlatır ve bir görev ID'si döndürür."""
    pipeline_name = config.get("pipeline_name", "unknown")
    print(f"Service: Sending task for pipeline '{pipeline_name}' to Celery.")
    
    # .delay() ile gerçek Celery görevini tetikliyoruz
    task = start_training_pipeline.delay(config)
    
    return {"message": "Experiment submitted to worker.", "task_id": task.id}