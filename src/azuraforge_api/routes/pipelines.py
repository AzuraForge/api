from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..services import experiment_service

router = APIRouter(tags=["Pipelines"])

@router.get("/pipelines", response_model=List[Dict[str, Any]])
def get_all_available_pipelines():
    return experiment_service.get_available_pipelines()

@router.get("/pipelines/{pipeline_id}/config", response_model=Dict[str, Any])
def get_pipeline_default_config(pipeline_id: str):
    try:
        return experiment_service.get_default_pipeline_config(pipeline_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))