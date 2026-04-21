"""Chat router — all /session/* and /chat endpoints."""

from __future__ import annotations

import os
import sys
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "..", "..")
sys.path.insert(0, SRC_DIR)

from api.models import (
    ChatRequest,
    ChatResponse,
    SessionResetResponse,
    SessionStartRequest,
    SessionStartResponse,
    SessionSummaryResponse,
)
from api.session_manager import SessionManager

router = APIRouter()

# Injected at startup by main.py via set_manager()
_manager: SessionManager | None = None


def set_manager(manager: SessionManager) -> None:
    """Inject the shared SessionManager instance into this module."""
    global _manager
    _manager = manager


# ──────────────────────────────────────────────────────────────────────
# POST /session/start
# ──────────────────────────────────────────────────────────────────────

@router.post(
    "/session/start",
    response_model=SessionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new delegate session",
    tags=["Sessions"],
)
async def start_session(body: SessionStartRequest) -> SessionStartResponse:
    """Create a new VitalAgent session with the chosen persona."""
    try:
        session = _manager.create_session(
            persona=body.persona,
            session_id=body.session_id,
        )
        return SessionStartResponse(
            session_id=session["session_id"],
            persona=session["persona"],
            message=(
                f"Session started with persona '{session['persona']}'. "
                "Ready to chat."
            ),
            created_at=session["created_at"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {exc}",
        ) from exc


# ──────────────────────────────────────────────────────────────────────
# POST /chat
# ──────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
import asyncio
import uuid
import os
import sys

# Safe imports — if these packages are missing the router still loads
try:
    import edge_tts
    EDGE_TTS_OK = True
except ImportError:
    EDGE_TTS_OK = False
    print("[WARNING] edge_tts not installed — avatar generation disabled.")

try:
    import requests as http_requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False
    print("[WARNING] requests not installed — avatar generation disabled.")


AVATAR_SERVICE = "http://127.0.0.1:8001"


def trigger_avatar_streaming(text: str, video_filename: str, job_id: str):
    """
    Background task: synthesise speech then POST to the avatar
    streaming service so chunks are written as fast as the GPU can render.
    """
    if not (EDGE_TTS_OK and REQUESTS_OK):
        print("[AVATAR] Skipping render — missing dependencies.")
        return
    try:
        temp_audio = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "..", "dso_avatar", "temp_musetalk", "data", "audio",
            f"{job_id}_tts.wav"
        )
        os.makedirs(os.path.dirname(temp_audio), exist_ok=True)

        # Synthesise English speech
        async def _synth():
            comm = edge_tts.Communicate(text, "en-US-AvaMultilingualNeural")
            await comm.save(temp_audio)

        asyncio.run(_synth())

        # Send to avatar service with the pre-agreed job_id
        with open(temp_audio, "rb") as fh:
            http_requests.post(
                f"{AVATAR_SERVICE}/render/stream",
                files={"file": (f"{job_id}.wav", fh, "audio/wav")},
                data={"filename": video_filename, "job_id": job_id},
                timeout=10,
            )

        if os.path.exists(temp_audio):
            os.remove(temp_audio)

    except Exception as e:
        print(f"[AVATAR ERROR] {e}")


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to the delegate agent",
    tags=["Chat"],
)
async def chat(body: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
    """Send a user message and receive the agent's English response."""
    try:
        agent = _manager.get_agent(body.session_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found. Call /session/start first.",
            )

        response_text = agent.chat(body.message)
        intent        = agent.last_intent
        session       = _manager.get_session(body.session_id)

        # Pre-compute job_id so we can return the manifest URL immediately,
        # before the background task even starts.
        job_id       = str(uuid.uuid4())
        video_file   = f"{job_id}.mp4"
        manifest_url = f"{AVATAR_SERVICE}/stream/{job_id}/manifest"
        video_url    = f"/assets/videos/{video_file}"

        background_tasks.add_task(trigger_avatar_streaming, response_text, video_file, job_id)

        return ChatResponse(
            session_id    = body.session_id,
            persona       = session["persona"],
            user_message  = body.message,
            agent_response= response_text,
            video_url     = video_url,
            manifest_url  = manifest_url,
            intent        = intent,
            timestamp     = datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {exc}",
        ) from exc


# ──────────────────────────────────────────────────────────────────────
# GET /session/{session_id}
# ──────────────────────────────────────────────────────────────────────

@router.get(
    "/session/{session_id}",
    response_model=SessionSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get session summary",
    tags=["Sessions"],
)
async def get_session(session_id: str) -> SessionSummaryResponse:
    """Return the current summary for a session."""
    try:
        session = _manager.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found.",
            )

        summary = session["agent"].get_conversation_summary()
        return SessionSummaryResponse(
            session_id=session_id,
            persona=session["persona"],
            turns=summary["turns"],
            last_intent=summary["last_intent"],
            created_at=session["created_at"],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching session: {exc}",
        ) from exc


# ──────────────────────────────────────────────────────────────────────
# POST /session/{session_id}/reset
# ──────────────────────────────────────────────────────────────────────

@router.post(
    "/session/{session_id}/reset",
    response_model=SessionResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset conversation history",
    tags=["Sessions"],
)
async def reset_session(session_id: str) -> SessionResetResponse:
    """Clear the conversation history for a session without deleting it."""
    try:
        success = _manager.reset_session(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found.",
            )
        return SessionResetResponse(
            session_id=session_id,
            message="Conversation history cleared.",
            reset_at=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting session: {exc}",
        ) from exc


# ──────────────────────────────────────────────────────────────────────
# DELETE /session/{session_id}
# ──────────────────────────────────────────────────────────────────────

@router.delete(
    "/session/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a session",
    tags=["Sessions"],
)
async def delete_session(session_id: str) -> dict:
    """Remove a session and free its memory."""
    try:
        success = _manager.delete_session(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found.",
            )
        return {"message": "Session deleted", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting session: {exc}",
        ) from exc


# ──────────────────────────────────────────────────────────────────────
# GET /sessions
# ──────────────────────────────────────────────────────────────────────

@router.get(
    "/sessions",
    status_code=status.HTTP_200_OK,
    summary="List all active sessions",
    tags=["Sessions"],
)
async def list_sessions() -> dict:
    """Return a summary of every currently active session."""
    try:
        sessions = _manager.list_sessions()
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing sessions: {exc}",
        ) from exc
