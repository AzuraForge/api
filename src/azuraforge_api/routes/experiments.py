# api/src/azuraforge_api/routes/experiments.py

from fastapi import APIRouter, HTTPException, Response
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
    return experiment_service.get_task_status(task_id)

# YENİ ENDPOINT
@router.get("/experiments/{experiment_id}/report")
def read_experiment_report(experiment_id: str):
    """
    Belirli bir deneyin Markdown raporunu metin olarak döndürür.
    """
    try:
        report_content = experiment_service.get_experiment_report(experiment_id)
        # Markdown içeriğini düz metin olarak, text/markdown content type ile döndür
        return Response(content=report_content, media_type="text/markdown")
    except HTTPException as e:
        # Servis katmanından gelen HTTPException'ı doğrudan yükselt
        raise e