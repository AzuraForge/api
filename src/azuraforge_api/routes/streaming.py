# ========== YENİ DOSYA: api/src/azuraforge_api/routes/streaming.py ==========
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from celery.result import AsyncResult
from azuraforge_worker import celery_app

router = APIRouter()

@router.websocket("/ws/task_status/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    print(f"WebSocket connection established for task: {task_id}")
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    try:
        while not task_result.ready():
            if task_result.state == 'PROGRESS':
                await websocket.send_json({
                    "state": task_result.state,
                    "details": task_result.info,
                })
            # Daha sık güncelleme için kısa bir bekleme
            await asyncio.sleep(0.5)
        
        # Görev bittiğinde son durumu gönder
        await websocket.send_json({
            "state": task_result.state,
            "details": task_result.result,
        })
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for task: {task_id}")
    except Exception as e:
        print(f"An error occurred in WebSocket for task {task_id}: {e}")
    finally:
        print(f"Closing WebSocket for task {task_id}")
        await websocket.close()