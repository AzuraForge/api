# api/src/azuraforge_api/routes/experiments.py

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..services import experiment_service

router = APIRouter(tags=["Experiments"])

@router.get("/experiments", response_model=List[Dict[str, Any]])
def get_all_experiments():
    return experiment_service.list_experiments()

@router.post("/experiments", status_code=202, response_model=Dict[str, Any])
def create_new_experiment(config: Dict[str, Any]):
    return experiment_service.start_experiment(config)

@router.get("/experiments/{task_id}/status", response_model=Dict[str, Any])
def get_experiment_status(task_id: str):
    # Bu endpoint artık çok gerekli değil ama kalabilir.
    return experiment_service.get_task_status(task_id)

# YENİ ENDPOINT (read_experiment_report yerine)
@router.get("/experiments/{experiment_id}/details", response_model=Dict[str, Any])
def read_experiment_details(experiment_id: str):
    """
    Belirli bir deneyin tüm detaylarını (config, results, metrics, history)
     içeren JSON verisini döndürür.
    """
    try:
        return experiment_service.get_experiment_details(experiment_id)
    except HTTPException as e:
        raise e