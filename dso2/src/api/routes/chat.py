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

import requests as http_requests
import asyncio
import tempfile
import io
import uuid

# Avatar rendering service (wav2lip offline render, port 8011)
AVATAR_SERVICE = "http://127.0.0.1:8011"
# Edge TTS server (local, port 5500)
EDGE_TTS_URL   = "http://127.0.0.1:5500/tts"
# Voice to use (French female)
TTS_VOICE      = "fr-FR-DeniseNeural"


def generate_tts_wav(text: str) -> bytes | None:
    """Call the local Edge TTS server and return raw MP3/WAV bytes."""
    try:
        resp = http_requests.get(
            EDGE_TTS_URL,
            params={"text": text, "voice": TTS_VOICE},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.content  # MP3 bytes
    except Exception as e:
        print(f"[WARNING] Edge TTS call failed: {e}")
        return None


def submit_avatar_render(audio_bytes: bytes, job_id: str) -> dict | None:
    """
    Send MP3 audio bytes to avatar_service /render/stream.
    Returns the manifest info dict or None on failure.
    """
    try:
        resp = http_requests.post(
            f"{AVATAR_SERVICE}/render/stream",
            files={"file": (f"{job_id}.mp3", io.BytesIO(audio_bytes), "audio/mpeg")},
            data={"job_id": job_id},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()  # {job_id, manifest_url, video_url}
    except Exception as e:
        print(f"[WARNING] Avatar render submit failed: {e}")
        return None


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to the delegate agent",
    tags=["Chat"],
)
async def chat(body: ChatRequest) -> ChatResponse:
    """Send a user message and receive the agent's English response."""
    try:
        agent = _manager.get_agent(body.session_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found. Call /session/start first.",
            )

        try:
            response_text = agent.chat(body.message)
        except Exception as chat_err:
            print(f"[WARNING] LLM Generation failed: {chat_err}. Using fallback.")
            response_text = "Je m'excuse, j'ai une petite perturbation de connexion. Pouvez-vous répéter ?"
            
        intent = agent.last_intent
        session = _manager.get_session(body.session_id)

        # ── Avatar Rendering Pipeline ───────────────────────────────────
        avatar_job_id    = str(uuid.uuid4())
        manifest_url     = None
        video_url        = None
        avatar_status    = None

        # 1. Generate TTS audio from the agent response
        audio_bytes = generate_tts_wav(response_text)
        if audio_bytes:
            # 2. Submit to avatar_service for Wav2Lip rendering
            render_info = submit_avatar_render(audio_bytes, avatar_job_id)
            if render_info:
                manifest_url  = render_info.get("manifest_url")
                video_url     = render_info.get("video_url")
                avatar_status = "rendering"
                print(f"[INFO] Avatar render job submitted: {avatar_job_id[:8]}")
            else:
                avatar_status = "avatar_error"
        else:
            avatar_status = "tts_error"

        return ChatResponse(
            session_id=body.session_id,
            persona=session["persona"],
            user_message=body.message,
            agent_response=response_text,
            avatar_session_id=avatar_job_id,
            avatar_status=avatar_status,
            manifest_url=manifest_url,
            video_url=video_url,
            intent=intent,
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] Chat Route Failure:\n{error_detail}")
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
