"""Session manager: one VitalAgent instance per active session."""

from __future__ import annotations

import os
import sys
import threading
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "..")
sys.path.insert(0, SRC_DIR)

from llm.llm_agent import VitalAgent


class SessionManager:
    """Thread-safe registry of active VitalAgent sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}
        self._lock = threading.Lock()
        print("SessionManager initialized")

    # ------------------------------------------------------------------
    # Create / retrieve
    # ------------------------------------------------------------------

    def create_session(
        self,
        persona: str,
        session_id: str | None = None,
    ) -> dict:
        """Create a new session with a VitalAgent instance.

        Raises:
            ValueError: if the session_id already exists.
        """
        sid = session_id or str(uuid.uuid4())

        # Create agent BEFORE lock to avoid holding it during slow initialization
        agent = VitalAgent(session_id=sid, persona=persona)

        with self._lock:
            if sid in self._sessions:
                raise ValueError(
                    f"Session '{sid}' already exists. "
                    "Use a different session_id."
                )
            self._sessions[sid] = {
                "agent": agent,
                "persona": persona,
                "created_at": datetime.utcnow(),
                "session_id": sid,
            }

        return self._sessions[sid]

    def get_session(self, session_id: str) -> dict | None:
        """Return the full session dict, or None if not found."""
        with self._lock:
            return self._sessions.get(session_id)

    def get_agent(self, session_id: str) -> VitalAgent | None:
        """Return the VitalAgent for *session_id*, or None."""
        session = self.get_session(session_id)
        return session["agent"] if session else None

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def reset_session(self, session_id: str) -> bool:
        """Clear conversation history for *session_id*.

        Returns:
            True on success, False if the session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                return False
            self._sessions[session_id]["agent"].reset_conversation()
            return True

    def delete_session(self, session_id: str) -> bool:
        """Remove a session from memory.

        Returns:
            True on success, False if the session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                return False
            del self._sessions[session_id]
            return True

    # ------------------------------------------------------------------
    # Listing / counting
    # ------------------------------------------------------------------

    def list_sessions(self) -> list[dict]:
        """Return a summary list of all active sessions."""
        with self._lock:
            return [
                {
                    "session_id": sid,
                    "persona": data["persona"],
                    "created_at": data["created_at"],
                    "turns": data["agent"].get_conversation_summary()["turns"],
                }
                for sid, data in self._sessions.items()
            ]

    def count_sessions(self) -> int:
        """Return the number of currently active sessions."""
        with self._lock:
            return len(self._sessions)
