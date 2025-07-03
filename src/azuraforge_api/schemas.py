from pydantic import BaseModel
from typing import List, Dict, Any

class PredictionRequest(BaseModel):
    """
    Tahmin isteği için veri yapısı.
    Veri, sütun odaklı bir formatta gönderilir.
    """
    # Örnek: {"Date": ["2023-01-01"], "Close": [150.0], "Volume": [10000]}
    # Not: Sütun isimleri ve veri tipleri, pipeline'ın beklediği ile eşleşmelidir.
    data: List[Dict[str, Any]]

class PredictionResponse(BaseModel):
    """Tahmin yanıtı için veri yapısı."""
    prediction: float
    experiment_id: str