"""Pydantic request and response models for the VITAL AI Delegate API."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SessionStartRequest(BaseModel):
    persona: str = Field(
        ...,
        description="Delegate persona: 'medical' or 'commercial'",
        pattern="^(medical|commercial)$"
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional custom session ID. Auto-generated if not provided."
    )


class SessionStartResponse(BaseModel):
    session_id: str
    persona: str
    message: str
    created_at: datetime


class ChatRequest(BaseModel):
    session_id: str = Field(
        ...,
        description="Session ID returned from /session/start"
    )
    message: str = Field(
        ...,
        description="User message in French",
        min_length=1,
        max_length=2000
    )


class ChatResponse(BaseModel):
    session_id: str
    persona: str
    user_message: str
    agent_response: str
    intent: str
    timestamp: datetime


class SessionSummaryResponse(BaseModel):
    session_id: str
    persona: str
    turns: int
    last_intent: str
    created_at: datetime


class SessionResetResponse(BaseModel):
    session_id: str
    message: str
    reset_at: datetime


class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime


class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    active_sessions: int
    timestamp: datetime
