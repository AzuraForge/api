from typing import Any
from fastapi import HTTPException, status

class AzuraForgeException(HTTPException):
    """
    Proje genelinde kullanılacak temel hata sınıfı.
    Frontend'in yorumlayabilmesi için standart bir formatta hata döndürür.
    """
    def __init__(self, status_code: int, detail: Any, error_code: str):
        # Hata detayını her zaman bir sözlük olarak yapılandırıyoruz
        super().__init__(
            status_code=status_code, 
            detail={"error_code": error_code, "message": str(detail)}
        )

# --- Spesifik Hata Sınıfları ---

class PipelineNotFoundException(AzuraForgeException):
    def __init__(self, pipeline_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline '{pipeline_id}' not found in the catalog.",
            error_code="PIPELINE_NOT_FOUND"
        )

class ConfigNotFoundException(AzuraForgeException):
    def __init__(self, pipeline_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Default config for pipeline '{pipeline_id}' could not be loaded.",
            error_code="CONFIG_NOT_FOUND"
        )

class ExperimentNotFoundException(AzuraForgeException):
    def __init__(self, experiment_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID '{experiment_id}' not found.",
            error_code="EXPERIMENT_NOT_FOUND"
        )