# ========== DOSYA: src/azuraforge_api/routes/experiments.py ==========
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from azuraforge_api.services import experiment_service # Mutlak import

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
def get_all_experiments():
    """Tüm deneylerin listesini almak için endpoint."""
    try:
        return experiment_service.list_experiments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", status_code=202, response_model=Dict[str, Any])
def create_experiment(config: Dict[str, Any]):
    """Yeni bir deney başlatmak için endpoint."""
    try:
        return experiment_service.start_experiment(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))