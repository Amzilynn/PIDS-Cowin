import cv2
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Generator
import json
import asyncio

from session_manager import manager
from session import load_delegues, load_products

router = APIRouter()

class StartRequest(BaseModel):
    delegue_id: int
    product_id: int = None  # Make it optional for backwards compatibility during testing

class SpeechControlRequest(BaseModel):
    action: str  # "start" or "stop"

@router.get("/delegues")
def get_delegues():
    delegues = load_delegues()
    return delegues

@router.get("/products")
def get_products():
    products = load_products()
    return products

@router.post("/start")
def start_training(req: StartRequest):
    try:
        res = manager.start_session(req.delegue_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/speech_control")
def speech_control(req: SpeechControlRequest):
    from avatar.stt import recording_start_event, recording_stop_event
    if req.action == "start":
        recording_stop_event.clear()
        recording_start_event.set()
        return {"status": "recording started"}
    elif req.action == "stop":
        recording_stop_event.set()
        return {"status": "recording stopped"}
    else:
        raise HTTPException(status_code=400, detail="Action invalide")

@router.post("/stop")
def stop_training():
    res = manager.stop_session()
    # On attend un peu que le JSON du report soit prêt si le thread se ferme doucement
    # Mais stop_session ne bloque pas s'il délègue l'arrêt.
    # Pour faire simple on retourne manager.last_results s'ils ont été calculés, sinon le front devra interroger
    # Dans notre cas, manager._run_conversation va set last_results.
    import time
    for _ in range(10):  # Attente max 5 secondes
        if not manager.is_active:
            break
        time.sleep(0.5)

    return {
        "status": res,
        "results": manager.last_results,
        "report_pdf": manager.last_report
    }

def frame_generator():
    """Generator function that yields JPEG frames from the evaluation thread."""
    import time
    while True:
        if not manager.is_active:
            time.sleep(0.1)
            continue
            
        frame = manager.get_current_frame()
        if frame is None:
            time.sleep(0.05)
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Limit framerate for the stream to avoid network congestion
        time.sleep(0.05)

@router.get("/video_feed")
def video_feed():
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

@router.get("/chat_feed")
async def chat_feed():
    async def event_generator():
        while True:
            # Polling la queue
            try:
                msg = manager.message_queue.get_nowait()
                yield f"data: {json.dumps(msg)}\n\n"
            except Exception:
                await asyncio.sleep(0.2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
