# api/src/azuraforge_api/routes/experiments.py
import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, Response
from typing import List, Dict, Any

from ..services import experiment_service
from ..schemas import PredictionRequest, PredictionResponse # PredictionResponse import edildi
from ..core.exceptions import AzuraForgeException
from ..core import security
from azuraforge_dbmodels import User

router = APIRouter(tags=["Experiments"])

@router.get("/experiments", response_model=List[Dict[str, Any]])
def get_all_experiments(current_user: User = Depends(security.get_current_user)):
    return experiment_service.list_experiments()

@router.post("/experiments", status_code=202, response_model=Dict[str, Any])
def create_new_experiment(config: Dict[str, Any], current_user: User = Depends(security.get_current_user)):
    return experiment_service.start_experiment(config)

@router.get("/experiments/{experiment_id}/details", response_model=Dict[str, Any])
def read_experiment_details(experiment_id: str, current_user: User = Depends(security.get_current_user)):
    try:
        return experiment_service.get_experiment_details(experiment_id)
    except AzuraForgeException as e:
        raise e

@router.get("/experiments/{experiment_id}/report/content")
def get_experiment_report_content(experiment_id: str, current_user: User = Depends(security.get_current_user)):
    """Bir deneyin Markdown rapor dosyasının içeriğini döndürür."""
    try:
        report_dir = experiment_service.get_experiment_report_path(experiment_id)
        report_file_path = os.path.join(report_dir, "report.md")
        if not os.path.exists(report_file_path):
            raise AzuraForgeException(status_code=404, detail="Markdown report file not found.", error_code="REPORT_FILE_NOT_FOUND")
        
        with open(report_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content=content, media_type="text/markdown")
    except AzuraForgeException as e:
        raise e

@router.get("/experiments/{experiment_id}/report/images/{image_name}")
def get_experiment_report_image(experiment_id: str, image_name: str, current_user: User = Depends(security.get_current_user)):
    """Bir deney raporuna ait bir görseli döndürür."""
    try:
        report_dir = experiment_service.get_experiment_report_path(experiment_id)
        image_path = os.path.join(report_dir, "images", image_name)

        if not os.path.exists(image_path):
            raise AzuraForgeException(status_code=404, detail=f"Image '{image_name}' not found.", error_code="REPORT_IMAGE_NOT_FOUND")
        
        return FileResponse(image_path)
    except AzuraForgeException as e:
        raise e

# === DEĞİŞİKLİK BURADA: response_model genişletildi ve prediction_steps iletiliyor ===
@router.post("/experiments/{experiment_id}/predict", response_model=PredictionResponse) # PredictionResponse kullanıldı
async def predict_from_experiment(experiment_id: str, request: PredictionRequest, current_user: User = Depends(security.get_current_user)):
    try:
        # Servis katmanına prediction_steps'i ilet
        return await experiment_service.predict_with_model(experiment_id, request.data, request.prediction_steps)
    except AzuraForgeException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))