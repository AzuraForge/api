# ========== GÜNCELLENECEK DOSYA: api/src/azuraforge_api/services/experiment_service.py ==========
from typing import List, Dict, Any
import numpy as np

# Artık doğrudan worker paketinden gerçek görevi import ediyoruz!
from azuraforge_worker.tasks.training_tasks import start_training_pipeline

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