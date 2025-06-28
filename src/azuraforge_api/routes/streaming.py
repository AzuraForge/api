# ========== YENİ DOSYA: api/src/azuraforge_api/routes/streaming.py ==========
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from celery.result import AsyncResult

# Worker projesinden celery_app'i import etmemiz gerekiyor.
# Bu, api projesinin worker'a bağımlı olmasını gerektirir.
from azuraforge_worker import celery_app

router = APIRouter()

@router.websocket("/ws/task_status/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    """
    Bir Celery görevinin durumunu bir WebSocket üzerinden anlık olarak yayınlar.
    """
    await websocket.accept()
    logging.info(f"WebSocket connection accepted for task: {task_id}")
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    try:
        # Görev tamamlanana kadar döngüde kal
        while not task_result.ready():
            # Sadece PROGRESS durumundaki ara bilgileri gönder
            if task_result.state == 'PROGRESS':
                await websocket.send_json({
                    "state": task_result.state,
                    "details": task_result.info, # .info, update_state ile gönderilen meta verisini içerir
                })
            # Çok sık kontrol etmemek için kısa bir bekleme
            await asyncio.sleep(1)
        
        # Görev bittiğinde (SUCCESS, FAILURE vb.) son durumu ve sonucu gönder
        await websocket.send_json({
            "state": task_result.state,
            "details": task_result.result,
        })

    except WebSocketDisconnect:
        logging.warning(f"WebSocket disconnected for task: {task_id}")
    except Exception as e:
        logging.error(f"An error occurred in WebSocket for task {task_id}: {e}")
    finally:
        logging.info(f"Closing WebSocket for task {task_id}")
        # Bağlantıyı her durumda kapat
        await websocket.close()