from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..services import experiment_service
from ..schemas import PredictionRequest, PredictionResponse
from ..core.exceptions import AzuraForgeException

router = APIRouter(tags=["Experiments"])

@router.get("/experiments", response_model=List[Dict[str, Any]])
def get_all_experiments():
    return experiment_service.list_experiments()

@router.post("/experiments", status_code=202, response_model=Dict[str, Any])
def create_new_experiment(config: Dict[str, Any]):
    return experiment_service.start_experiment(config)

@router.get("/experiments/{experiment_id}/details", response_model=Dict[str, Any])
def read_experiment_details(experiment_id: str):
    try:
        return experiment_service.get_experiment_details(experiment_id)
    except AzuraForgeException as e:
        raise e

@router.post("/{experiment_id}/predict", response_model=PredictionResponse)
def predict_from_experiment(experiment_id: str, request: PredictionRequest):
    """
    Kaydedilmiş bir deneye ait modeli kullanarak anlık tahmin yapar.
    Girdi verisi, modelin eğitildiği tüm özellikleri içeren ve en az
    'sequence_length' kadar geçmiş veriyi barındıran bir liste olmalıdır.
    """
    try:
        return experiment_service.predict_with_model(experiment_id, request.data)
    except AzuraForgeException as e:
        raise e
    except Exception as e:
        # Beklenmedik diğer hatalar için genel bir hata döndür
        raise HTTPException(status_code=500, detail=str(e))