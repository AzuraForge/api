import asyncio
import logging
import json
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as redis

router = APIRouter()

async def redis_listener(websocket: WebSocket, task_id: str):
    """Redis Pub/Sub kanalını dinler ve gelen mesajları WebSocket'e iletir."""
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    r = await redis.from_url(redis_url)
    pubsub = r.pubsub()
    channel = f"task-progress:{task_id}"
    await pubsub.subscribe(channel)
    
    try:
        while True:
            # `listen` bir coroutine'dir, bu yüzden `await` edilmelidir.
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                # Gelen veri bytes, string'e çevirip JSON olarak parse et.
                data_str = message['data'].decode('utf-8')
                progress_data = json.loads(data_str)
                # UI'ın beklediği formatla gönder
                await websocket.send_json({
                    "state": "PROGRESS",
                    "details": progress_data
                })
            # WebSocket bağlantısı hala açık mı kontrol et
            # Bu, istemci bağlantıyı kapattığında döngüden çıkmayı sağlar.
            await asyncio.sleep(0.1) # CPU'yu yormamak için kısa bir bekleme
    except asyncio.CancelledError:
        logging.info(f"Redis listener for task {task_id} cancelled.")
    except Exception as e:
        logging.error(f"Redis listener error for task {task_id}: {e}")
    finally:
        await pubsub.unsubscribe(channel)
        await r.close()
        logging.info(f"Redis listener for task {task_id} cleaned up.")

@router.websocket("/ws/task_status/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    await websocket.accept()
    logging.info(f"WebSocket connection accepted for task: {task_id}")
    
    # Redis dinleyicisini bir arka plan görevi olarak başlat
    listener_task = asyncio.create_task(redis_listener(websocket, task_id))
    
    try:
        # İstemcinin bağlantıyı kapatmasını bekle
        # Bu döngü, bağlantı açık olduğu sürece çalışır.
        while True:
            await websocket.receive_text() # Bu satır aslında istemciden mesaj beklemez,
                                           # sadece bağlantının kopup kopmadığını kontrol eder.
    except WebSocketDisconnect:
        logging.warning(f"WebSocket disconnected by client for task: {task_id}")
    finally:
        # İstemci bağlantıyı kapattığında, arka plandaki Redis dinleyicisini iptal et
        listener_task.cancel()
        # Görevin bitmesini bekle (kaynakların temizlenmesi için)
        await listener_task
        logging.info(f"Closing WebSocket connection for task {task_id}")