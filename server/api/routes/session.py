"""
Session routes for loading and saving sessions.

Endpoints:
- GET /api/session/{session_id} - Load a session
- POST /api/session/{session_id}/save - Save/checkpoint a session
- GET /api/session - List all sessions
- DELETE /api/session/{session_id} - Delete a session
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.persistence import (
    SessionStore,
    SessionNotFoundError,
    Session,
    Mode,
    BuildPhase,
)


# =============================================================================
# Router
# =============================================================================

router = APIRouter()

# Session store instance
store = SessionStore()


# =============================================================================
# Response Models
# =============================================================================

class SessionSummary(BaseModel):
    """Summary of a session for listing."""
    id: str
    created: str
    updated: str
    mode: Mode
    topic: str


class SessionListResponse(BaseModel):
    """Response with list of sessions."""
    sessions: list[SessionSummary]
    total: int


class SessionSaveRequest(BaseModel):
    """Request to save/checkpoint a session."""
    checkpoint: Optional[str] = None


class SessionSaveResponse(BaseModel):
    """Response confirming save."""
    saved: bool
    session_id: str
    updated: str


class SessionDeleteResponse(BaseModel):
    """Response confirming deletion."""
    deleted: bool
    session_id: str


# =============================================================================
# Routes
# =============================================================================

@router.get("", response_model=SessionListResponse)
async def list_sessions():
    """
    List all sessions with metadata.

    Returns sessions sorted by last updated (most recent first).
    """
    sessions_data = store.list_with_metadata()

    sessions = [
        SessionSummary(
            id=s["id"],
            created=s["created"],
            updated=s["updated"],
            mode=s["mode"],
            topic=s["topic"],
        )
        for s in sessions_data
    ]

    return SessionListResponse(
        sessions=sessions,
        total=len(sessions),
    )


@router.get("/{session_id}")
async def get_session(session_id: str):
    """
    Load a session by ID.

    Returns the full session state for resumption.
    """
    try:
        session = store.get(session_id)
        return session.model_dump(mode="json")
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/save", response_model=SessionSaveResponse)
async def save_session(session_id: str, request: SessionSaveRequest):
    """
    Save/checkpoint a session.

    This triggers an explicit save. Sessions are also auto-saved
    after each agent operation.
    """
    try:
        session = store.get(session_id)

        # Just saving triggers the updated timestamp
        saved = store.save(session)

        return SessionSaveResponse(
            saved=True,
            session_id=saved.id,
            updated=saved.updated.isoformat(),
        )
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.delete("/{session_id}", response_model=SessionDeleteResponse)
async def delete_session(session_id: str):
    """
    Delete a session.

    This permanently removes the session and all its data.
    """
    deleted = store.delete(session_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionDeleteResponse(
        deleted=True,
        session_id=session_id,
    )
