from fastapi import APIRouter
from typing import List, Dict, Any
from ..services import experiment_service
from ..core.exceptions import ConfigNotFoundException

router = APIRouter(tags=["Pipelines"])

@router.get("/pipelines", response_model=List[Dict[str, Any]])
def get_all_available_pipelines():
    return experiment_service.get_available_pipelines()

@router.get("/pipelines/{pipeline_id}/config", response_model=Dict[str, Any])
def get_pipeline_default_config(pipeline_id: str):
    try:
        return experiment_service.get_default_pipeline_config(pipeline_id)
    except ConfigNotFoundException as e:
        raise e