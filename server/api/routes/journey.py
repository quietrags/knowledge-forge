"""
Journey routes for question analysis and session initialization.

Endpoints:
- POST /api/journey/analyze - Analyze a question and design journey
- POST /api/journey/confirm - Confirm journey and initialize session
- GET /api/journey/stream - SSE stream for session events
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from server.persistence import (
    SessionStore,
    JourneyDesignBrief,
    Mode,
)
from server.orchestrator import Orchestrator
from ..streaming import stream_manager, session_started


# =============================================================================
# Router
# =============================================================================

router = APIRouter()

# Session store instance (shared across routes)
store = SessionStore()

# Orchestrator instance
orchestrator = Orchestrator(store=store, stream_manager=stream_manager)


# =============================================================================
# Request/Response Models
# =============================================================================

class JourneyAnalyzeRequest(BaseModel):
    """Request to analyze a question."""
    question: str
    learner_context: Optional[str] = None
    use_llm: bool = False  # Default to heuristics for fast response


# Note: analyze endpoint returns JourneyDesignBrief directly per spec


class JourneyConfirmRequest(BaseModel):
    """Request to confirm a journey."""
    brief: JourneyDesignBrief
    confirmed: bool
    alternative_mode: Optional[Mode] = None


class SessionInitResponse(BaseModel):
    """Response with initialized session."""
    session_id: str = Field(alias="sessionId", serialization_alias="sessionId")
    mode: Mode
    # Note: initial_data would be Union type but keeping simple for now

    model_config = {"populate_by_name": True}


# =============================================================================
# Routes
# =============================================================================

@router.post("/analyze", response_model=JourneyDesignBrief)
async def analyze_journey(request: JourneyAnalyzeRequest):
    """
    Analyze a user's question and design their learning journey.

    This endpoint:
    1. Parses the question shape (heuristic routing or LLM-powered)
    2. Works backwards from the ideal answer
    3. Returns a JourneyDesignBrief for confirmation

    Set `use_llm=true` in the request to use LLM-powered analysis
    for more nuanced routing and misalignment detection.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Use orchestrator for analysis
    brief = await orchestrator.analyze_question(
        question=request.question,
        learner_context=request.learner_context,
        use_llm=request.use_llm,
    )

    return brief


@router.post("/confirm", response_model=SessionInitResponse)
async def confirm_journey(request: JourneyConfirmRequest):
    """
    Confirm a journey and initialize a session.

    This endpoint:
    1. Creates a new session with the journey brief
    2. Initializes mode-specific data structures
    3. Sets up SSE stream for the session
    4. Returns the session ID for streaming
    """
    if not request.confirmed:
        raise HTTPException(status_code=400, detail="Journey not confirmed")

    # Use orchestrator to initialize journey
    session = await orchestrator.initialize_journey(
        brief=request.brief,
        alternative_mode=request.alternative_mode,
    )

    return SessionInitResponse(
        session_id=session.id,
        mode=session.mode,
    )


@router.get("/stream")
async def stream_journey(session_id: str = Query(..., alias="sessionId", description="Session ID")):
    """
    SSE stream for session events.

    Connect to this endpoint to receive real-time updates as the
    agent processes your journey.
    """
    # Verify session exists
    session = orchestrator.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Ensure stream exists
    if not orchestrator.has_stream(session_id):
        orchestrator.create_stream(session_id)

    async def event_generator():
        # Send initial session started event
        yield session_started(session.id, session.mode).format()

        # Subscribe to stream and yield events
        async for event in stream_manager.subscribe(session_id):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
