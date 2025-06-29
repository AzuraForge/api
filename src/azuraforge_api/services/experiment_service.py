import json
import os
import glob
from importlib import resources
from importlib.metadata import entry_points
from typing import List, Dict, Any, Optional
from celery.result import AsyncResult 

from azuraforge_worker import celery_app
from azuraforge_worker.tasks.training_tasks import start_training_pipeline
from azuraforge_worker.tasks.training_tasks import AVAILABLE_PIPELINES_AND_CONFIGS

REPORTS_BASE_DIR = os.path.abspath(os.getenv("REPORTS_DIR", "/app/reports"))

def get_available_pipelines() -> List[Dict[str, Any]]:
    # Mevcut kodunuzu kullanarak resmi uygulamalar kataloğunu çekmeye devam edin
    # Bu, dashboard'daki "pipeline adı" ve "açıklama" gibi meta verileri sağlar.
    official_apps_data = []
    try:
        with resources.open_text("azuraforge_applications", "official_apps.json") as f:
            official_apps_data = json.load(f)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"ERROR: Could not find or read the official apps catalog. {e}")
        # Hata durumunda boş liste döndürmek yerine hata fırlatılabilir veya varsayılan bir şey sağlanabilir.

    # Şimdi worker'dan keşfedilen pipeline'lar ile bu meta veriyi birleştir.
    # Sadece worker'ın gerçekten keşfettiği pipeline'ları sun.
    available_pipelines_with_configs = []
    for app_meta in official_apps_data:
        app_id = app_meta.get("id")
        if app_id in AVAILABLE_PIPELINES_AND_CONFIGS:
            # Sadece keşfedilenleri ekle
            available_pipelines_with_configs.append(app_meta)
    
    return available_pipelines_with_configs

# Yeni fonksiyon: Belirli bir pipeline'ın varsayılan konfigürasyonunu döndürür
def get_default_pipeline_config(pipeline_id: str) -> Dict[str, Any]:
    """Belirli bir pipeline'ın varsayılan konfigürasyonunu döndürür."""
    pipeline_info = AVAILABLE_PIPELINES_AND_CONFIGS.get(pipeline_id)
    if not pipeline_info:
        raise ValueError(f"Pipeline '{pipeline_id}' not found or its config function is missing.")
    
    get_config_func = pipeline_info.get('get_config_func')
    if not get_config_func:
        return {"message": "No specific default configuration available for this pipeline. Worker will use its internal defaults.", "pipeline_name": pipeline_id}

    return get_config_func()


def list_experiments() -> List[Dict[str, Any]]:
    """
    DÜZELTME: Artık her deney için results.json dosyasının tamamını döndürüyor.
    Bu, UI'ın genişletilebilir satırlarda tüm detayları göstermesini sağlar.
    """
    experiment_files = glob.glob(f"{REPORTS_BASE_DIR}/**/results.json", recursive=True)
    experiments = []
    for f_path in experiment_files:
        try:
            with open(f_path, 'r') as f:
                data = json.load(f)
                # Direkt olarak dosyanın içeriğini listeye ekle
                experiments.append(data)
        except Exception as e:
            print(f"Warning: Could not read results.json from {f_path}: {e}")
            continue
    
    # Sıralama: Önce çalışanlar, sonra en yeni tamamlananlar
    def sort_key(exp):
        status_order = {'STARTED': 1, 'PROGRESS': 2, 'PENDING': 3, 'UNKNOWN': 4, 'DISCONNECTED': 5, 'FAILURE': 6, 'ERROR': 7, 'SUCCESS': 8}
        status = exp.get('status', 'UNKNOWN')
        # Eğer canlı bir görevse, Celery'den anlık durumunu al. Bu, PENDING'den STARTED'a geçişi yakalar.
        if status in ['STARTED', 'PROGRESS', 'PENDING']:
             task = AsyncResult(exp.get('task_id'), app=celery_app)
             status = task.state
             exp['status'] = status # Deney objesini de anlık durumla güncelle
        
        timestamp = exp.get('completed_at') or exp.get('failed_at') or exp.get('config', {}).get('start_time', '1970-01-01T00:00:00')
        return (status_order.get(status, 99), timestamp)

    experiments.sort(key=sort_key, reverse=False) # Status'e göre artan, tarihe göre azalan sıralama için
    # reverse=False olacak ama sıralama anahtarını (timestamp) negatif yapmak aynı etkiyi verir.
    # En basit yol:
    experiments.sort(key=lambda x: x.get('config', {}).get('start_time', ''), reverse=True)
    
    return experiments


def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    pipeline_name = config.get("pipeline_name", "unknown")
    print(f"Service: Sending task for pipeline '{pipeline_name}' to Celery with config: {config}") # Logu güncellendi
    task = start_training_pipeline.delay(config) 
    return {"message": "Experiment submitted to worker.", "task_id": task.id}

def get_task_status(task_id: str) -> Dict[str, Any]:
    # Artık /experiments endpoint'i tüm veriyi döndürdüğü için bu endpoint'e olan ihtiyaç azalıyor.
    # Ama WebSocket'in ilk veri çekişi için hala değerli olabilir.
    task_result = AsyncResult(task_id, app=celery_app)
    status = task_result.state
    
    details = task_result.info 
    
    # Başarı durumunda, Celery result.result'ı doğrudan alıp gönder
    if status == 'SUCCESS':
        # Başarılı biten görevlerin rapor dosyasından okunmasını sağla
        # Bu, sayfa yenilense bile tüm verinin (özellikle loss geçmişinin) görünmesini garanti eder.
        matching_experiments = list_experiments()
        for exp in matching_experiments:
            if exp.get('task_id') == task_id: # task_id'yi de almanız gerekebilir list_experiments içinde
                return exp # Zaten gerekli tüm verileri içeren objeyi döndür

        # Eğer rapor dosyasından bulunamazsa, Celery sonucunu döndür
        return {"task_id": task_id, "status": status, "result": task_result.result}
    
    elif status == 'FAILURE':
        error_message = details.get('error_message', 'Bilinmeyen bir hata oluştu.')
        traceback_info = details.get('traceback', 'Detaylı hata izleme bilgisi yok.')
        
        # Kullanıcı dostu hata mesajı üretimi (örnek)
        user_friendly_message = "Deney eğitimi sırasında bir hata oluştu. Lütfen yapılandırmanızı kontrol edin veya AI modelinde bir sorun olabilir."
        if "yfinance.download" in error_message or "No data downloaded" in error_message:
            user_friendly_message = "Veri çekilirken bir sorun oluştu. Ticker sembolünü veya başlangıç tarihini kontrol edin."
        elif "Not enough data" in error_message:
            user_friendly_message = "Eğitim için yeterli veri bulunamadı. Lütfen daha uzun bir tarih aralığı seçin."
        elif "Pipeline execution failed" in error_message:
            user_friendly_message = "Pipeline'ın kendisi çalışırken bir hata ile karşılaştı. Detaylar için aşağıdaki teknik hata mesajını inceleyin."


        # Eğer rapor dosyasından bulunursa, hata bilgilerini oradan al.
        # Bu bölüm, önceki get_task_status'taki mantıkla çakışmaması için biraz daha dikkatli ele alınmalı.
        # En iyisi, task_id'ye göre rapor dosyasından full veriyi çekip, Celery'den sadece canlı durumu almak.
        # Şimdilik direkt Celery sonucunu zenginleştirelim.
        
        # Buradaki return, direkt Celery'den alınan 'FAILURE' state'indeki veriyi döndürür.
        # Rapor dosyasındaki "error" alanını burada "user_friendly_error" olarak ekleyebiliriz.
        return {
            "task_id": task_id, 
            "status": status, 
            "result": details, # Celery meta verisi (error_message, traceback içerir)
            "user_friendly_error": user_friendly_message
        }
    
    # PROGRESS, PENDING, STARTED gibi durumlar için
    return {"task_id": task_id, "status": status, "details": details}