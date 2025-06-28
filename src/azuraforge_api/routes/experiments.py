# ========== GÜNCELLENECEK DOSYA: api/src/azuraforge_api/routes/experiments.py ==========
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

# Servis katmanından ilgili fonksiyonları import et
from ..services import experiment_service

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
def get_all_experiments():
    """
    Başlatılmış tüm deneylerin (çalışan veya tamamlanmış) bir listesini döndürür.
    """
    try:
        return experiment_service.list_experiments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", status_code=202, response_model=Dict[str, Any])
def create_new_experiment(config: Dict[str, Any]):
    """
    Verilen konfigürasyon ile yeni bir deneyi arka planda çalışması için Worker'a gönderir.
    """
    try:
        return experiment_service.start_experiment(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}/status", response_model=Dict[str, Any])
def get_experiment_status(task_id: str):
    """
    Belirli bir görevin (deneyin) anlık durumunu döndürür.
    Dashboard tarafından canlı takip için kullanılır.
    """
    try:
        return experiment_service.get_task_status(task_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))