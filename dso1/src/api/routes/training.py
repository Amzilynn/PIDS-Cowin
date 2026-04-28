import cv2
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Generator
import json
import asyncio

from session_manager import manager
from session import load_delegues, load_products, load_gammes
from shared.database import SessionLocal
from shared.models import Simulation

router = APIRouter()

class StartRequest(BaseModel):
    delegue_id: int
    product_id: int = None  # Make it optional for backwards compatibility during testing

class SpeechTextRequest(BaseModel):
    text: str
    lang: str = "fr"

@router.get("/delegues")
def get_delegues():
    delegues = load_delegues()
    return delegues

@router.get("/products")
def get_products():
    products = load_products()
    return products

@router.get("/gammes")
def get_gammes():
    gammes = load_gammes()
    return gammes

@router.post("/start")
def start_training(req: StartRequest):
    try:
        res = manager.start_session(req.delegue_id, req.product_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/speech_text")
def speech_text(req: SpeechTextRequest):
    from avatar.stt import set_user_text
    set_user_text(req.text, req.lang)
    return {"status": "text received"}

@router.post("/stop")
def stop_training():
    res = manager.stop_session(discard=False)
    # On attend un peu que le JSON du report soit prêt si le thread se ferme doucement
    import time
    for _ in range(200):  # Attente max 100s
        if not manager.is_active and manager.last_results is not None and manager.last_report is not None:
            break
        time.sleep(0.5)

    return {
        "status": res,
        "results": manager.last_results,
        "report_pdf": manager.last_report
    }

@router.post("/cancel")
def cancel_training():
    res = manager.stop_session(discard=True)
    return {"status": res}

def frame_generator():
    """Generator function that yields JPEG frames from the evaluation thread."""
    import time
    # On reste dans la boucle seulement tant que la session est active
    while manager.is_active:
        frame = manager.get_current_frame()
        if frame is None:
            time.sleep(0.015)
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Limit framerate for the stream to avoid network congestion
        time.sleep(0.015)

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
@router.get("/history/{delegue_id}")
def get_training_history(delegue_id: int):
    db = SessionLocal()
    from shared.models import Evaluation
    try:
        results = db.query(Simulation).filter(
            Simulation.delegate_id == delegue_id
        ).order_by(Simulation.start_time.asc()).all()
        
        history = []
        for r in results:
            eval_data = db.query(Evaluation).filter(Evaluation.simulation_id == r.id).first()
            history.append({
                "id": r.id,
                "date": r.start_time.strftime("%d/%m"),
                "full_date": r.start_time.strftime("%Y-%m-%d"),
                "score": float(r.final_score) if r.final_score else 0.0,
                # Détails si dispos
                "confidence": float(eval_data.confidence_score) * 100 if eval_data and eval_data.confidence_score else 0.0,
                "stress": float(eval_data.stress_score) * 100 if eval_data and eval_data.stress_score else 0.0,
                "engagement": float(eval_data.engagement_score) * 100 if eval_data and eval_data.engagement_score else 0.0,
                "product_knowledge": float(eval_data.product_knowledge_score) * 100 if eval_data and eval_data.product_knowledge_score else 0.0,
            })
        return history
    finally:
        db.close()
