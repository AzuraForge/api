# ========== GÜNCELLENECEK DOSYA: api/src/azuraforge_api/services/experiment_service.py ==========
from typing import List, Dict, Any
import numpy as np

from importlib.metadata import entry_points

# Artık doğrudan worker paketinden gerçek görevi import ediyoruz!
from azuraforge_worker.tasks.training_tasks import start_training_pipeline

def get_available_pipelines():
    """Kurulu tüm pipeline eklentilerini ve varsayılan konfigürasyonlarını keşfeder."""
    pipelines = {}
    pipeline_eps = entry_points(group='azuraforge.pipelines')
    config_eps = {ep.name: ep for ep in entry_points(group='azuraforge.configs')}
    
    for ep in pipeline_eps:
        pipelines[ep.name] = {
            "pipeline_class": ep.value,
            # İlgili konfigürasyon fonksiyonunu yükle ve çağır
            "default_config": config_eps[ep.name].load()() if ep.name in config_eps else {}
        }
    return pipelines
    
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