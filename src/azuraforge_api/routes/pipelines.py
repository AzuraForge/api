# ========== GÜNCELLENECEK DOSYA: api/src/azuraforge_api/routes/pipelines.py ==========
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..services import experiment_service

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])

@router.get("/", response_model=List[Dict[str, Any]])
def get_all_available_pipelines():
    return experiment_service.get_available_pipelines()