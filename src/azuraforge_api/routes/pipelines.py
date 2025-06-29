from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..services import experiment_service

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])

@router.get("/", response_model=List[Dict[str, Any]])
def get_all_available_pipelines():
    """Tüm mevcut AI pipeline eklentilerinin listesini döndürür."""
    return experiment_service.get_available_pipelines()

@router.get("/{pipeline_id}/config", response_model=Dict[str, Any])
def get_pipeline_default_config(pipeline_id: str):
    """Belirli bir pipeline'ın varsayılan konfigürasyonunu döndürür."""
    try:
        return experiment_service.get_default_pipeline_config(pipeline_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))