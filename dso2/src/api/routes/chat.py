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

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to the delegate agent",
    tags=["Chat"],
)
async def chat(body: ChatRequest) -> ChatResponse:
    """Send a user message and receive the agent's French response."""
    try:
        agent = _manager.get_agent(body.session_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found. Call /session/start first.",
            )

        response_text = agent.chat(body.message)
        intent = agent.last_intent

        session = _manager.get_session(body.session_id)

        return ChatResponse(
            session_id=body.session_id,
            persona=session["persona"],
            user_message=body.message,
            agent_response=response_text,
            intent=intent,
            timestamp=datetime.utcnow(),
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
