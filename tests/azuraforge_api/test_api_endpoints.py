import pytest
from httpx import AsyncClient
from unittest.mock import patch

# Test edilecek FastAPI uygulamasını import et
from azuraforge_api.main import app

# pytest'in asenkron testleri çalıştırmasını sağlar
pytestmark = pytest.mark.asyncio

# API'ye yapılan tüm çağrılar için bir istemci oluşturalım
# 'app' argümanı, istemcinin doğrudan uygulama ile konuşmasını sağlar, ağ üzerinden değil.
@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

async def test_read_root(async_client: AsyncClient):
    """Kök endpoint'in doğru mesajı döndürdüğünü test eder."""
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to AzuraForge API"}

@patch('azuraforge_api.services.experiment_service.get_available_pipelines')
async def test_get_all_pipelines(mock_get_pipelines, async_client: AsyncClient):
    """/pipelines endpoint'inin doğru veriyi ve 200 kodunu döndürdüğünü test eder."""
    # Servis katmanını mock'layarak veritabanı veya dosya sistemi bağımlılığını ortadan kaldırıyoruz.
    mock_pipelines_data = [
        {"id": "stock_predictor", "name": "Hisse Senedi Fiyat Tahmini"},
        {"id": "weather_forecaster", "name": "Hava Durumu Tahmini"}
    ]
    mock_get_pipelines.return_value = mock_pipelines_data

    response = await async_client.get("/api/v1/pipelines")
    
    assert response.status_code == 200
    assert response.json() == mock_pipelines_data
    # Servis fonksiyonunun çağrıldığını doğrula
    mock_get_pipelines.assert_called_once()


@patch('azuraforge_api.services.experiment_service.start_experiment')
async def test_create_experiment_success(mock_start_experiment, async_client: AsyncClient):
    """Bir deney başarıyla gönderildiğinde 202 kodunu ve task_id'yi döndürdüğünü test eder."""
    test_config = {"pipeline_name": "stock_predictor", "data_sourcing": {"ticker": "GOOG"}}
    mock_start_experiment.return_value = {"message": "Experiment submitted", "task_id": "fake-task-id-123"}

    response = await async_client.post("/api/v1/experiments", json=test_config)
    
    assert response.status_code == 202 # Accepted
    assert response.json()["task_id"] == "fake-task-id-123"
    mock_start_experiment.assert_called_once_with(test_config)