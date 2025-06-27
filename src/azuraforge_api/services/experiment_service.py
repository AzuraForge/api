# ========== DOSYA: src/azuraforge_api/services/experiment_service.py ==========
from typing import List, Dict, Any

# Bu import, 'azuraforge-learner' paketi kurulduktan sonra çalışacaktır.
# from azuraforge_learner import Learner 

def list_experiments() -> List[Dict[str, Any]]:
    """Tüm deneylerin bir listesini döndürür (şimdilik sahte veri)."""
    print("Service: `list_experiments` called.")
    return [
        {"id": "exp_123", "name": "stock_predictor_run_1", "status": "completed"},
        {"id": "exp_456", "name": "weather_forecaster_run_1", "status": "running"},
    ]

def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    """Yeni bir deneyi başlatır ve bir görev ID'si döndürür (şimdilik sahte)."""
    pipeline_name = config.get("pipeline_name", "unknown_pipeline")
    print(f"Service: `start_experiment` called for pipeline: {pipeline_name}")
    # Gerçekte burada bir Celery görevi tetiklenecek
    task_id = f"task_{np.random.randint(1000, 9999)}"
    return {"message": "Experiment submitted to worker.", "task_id": task_id}

# Bu import'u fonksiyonun içine koyarak, celery worker olmadan da test etmemizi kolaylaştırırız.
import numpy as np 