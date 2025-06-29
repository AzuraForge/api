import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from celery.result import AsyncResult

from azuraforge_worker import celery_app

router = APIRouter()

@router.websocket("/ws/task_status/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    await websocket.accept()
    logging.info(f"WebSocket connection accepted for task: {task_id}")
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    try:
        initial_status = {
            "state": task_result.state,
            "details": task_result.info, # DÜZELTME: Gelen bilgiyi doğrudan 'details' olarak ata
            "result": task_result.result if task_result.ready() else None
        }
        await websocket.send_json(initial_status)

        while not task_result.ready():
            if task_result.state == 'PROGRESS':
                await websocket.send_json({
                    "state": task_result.state,
                    "details": task_result.info, # DÜZELTME: Gelen bilgiyi olduğu gibi gönder
                })
            await asyncio.sleep(1)
        
        await websocket.send_json({
            "state": task_result.state,
            "result": task_result.result,
        })

    except WebSocketDisconnect:
        logging.warning(f"WebSocket disconnected for task: {task_id}")
    except Exception as e:
        logging.error(f"An error occurred in WebSocket for task {task_id}: {e}")
        try:
            await websocket.send_json({"state": "ERROR", "details": {"message": str(e)}})
        except Exception:
            pass 
    finally:
        logging.info(f"Closing WebSocket for task {task_id}")
        if websocket.client_state.name != 'DISCONNECTED':
             await websocket.close()