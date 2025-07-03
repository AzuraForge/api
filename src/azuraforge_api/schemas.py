# api/src/azuraforge_api/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# === YENİ BÖLÜM: Kullanıcı ve Token Şemaları ===
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserInDB(UserBase):
    id: str
    hashed_password: str
    
    class Config:
        from_attributes = True
# === BİTTİ ===


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