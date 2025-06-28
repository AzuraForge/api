# ========== YENİ DOSYA: api/src/azuraforge_api/routes/pipelines.py ==========
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

# Servis katmanından ilgili fonksiyonu import et
from ..services import experiment_service

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
def get_all_available_pipelines():
    """
    Kurulu ve resmi olarak listelenen tüm uygulama pipeline'larını döndürür.
    Bu endpoint, Dashboard'un "Yeni Deney Başlat" sayfasındaki dropdown'ı doldurmak için kullanılır.
    """
    try:
        return experiment_service.get_available_pipelines()
    except Exception as e:
        # Hata durumunda sunucunun çökmemesi için hatayı yakala ve HTTP hatası olarak döndür
        raise HTTPException(
            status_code=500, 
            detail=f"Pipeline listesi alınırken bir hata oluştu: {e}"
        )