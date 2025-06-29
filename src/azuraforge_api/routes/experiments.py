from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..services import experiment_service

# DÜZELTME: tags'i buraya al, prefix'i ana dosyada bırak
router = APIRouter(tags=["Experiments"])

@router.get("/experiments", response_model=List[Dict[str, Any]])
def get_all_experiments():
    return experiment_service.list_experiments()

@router.post("/experiments", status_code=202, response_model=Dict[str, Any])
def create_new_experiment(config: Dict[str, Any]):
    return experiment_service.start_experiment(config)

@router.get("/experiments/{task_id}/status", response_model=Dict[str, Any])
def get_experiment_status(task_id: str):
    return experiment_service.get_task_status(task_id)