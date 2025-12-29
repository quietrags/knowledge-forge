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
from pydantic import BaseModel

from server.persistence import (
    SessionStore,
    JourneyDesignBrief,
    Mode,
    ResearchModeData,
    UnderstandModeData,
    BuildModeData,
)
from ..streaming import stream_manager, session_started


# =============================================================================
# Router
# =============================================================================

router = APIRouter()

# Session store instance
store = SessionStore()


# =============================================================================
# Request/Response Models
# =============================================================================

class JourneyAnalyzeRequest(BaseModel):
    """Request to analyze a question."""
    question: str
    learner_context: Optional[str] = None


class JourneyAnalyzeResponse(BaseModel):
    """Response with journey design brief."""
    brief: JourneyDesignBrief


class JourneyConfirmRequest(BaseModel):
    """Request to confirm a journey."""
    brief: JourneyDesignBrief
    confirmed: bool
    alternative_mode: Optional[Mode] = None


class SessionInitResponse(BaseModel):
    """Response with initialized session."""
    session_id: str
    mode: Mode
    # Note: initial_data would be Union type but keeping simple for now


# =============================================================================
# Question Analysis (Mock Implementation)
# =============================================================================

def analyze_question_heuristic(question: str) -> JourneyDesignBrief:
    """
    Analyze a question using heuristics.

    TODO: Replace with LLM-powered analysis via Orchestrator agent.
    """
    question_lower = question.lower()

    # Heuristic routing based on question patterns
    if any(phrase in question_lower for phrase in ["how do i", "how can i", "help me", "create", "build", "make"]):
        mode: Mode = "build"
        answer_type = "skill"
        ideal_answer = "Step-by-step guidance to build this capability with concrete techniques you can apply."
        confirmation = f"It sounds like you want to learn how to do something practical. I'll help you build this skill step by step."
    elif any(phrase in question_lower for phrase in ["why", "what's the difference", "how does", "explain", "understand"]):
        mode = "understand"
        answer_type = "understanding"
        ideal_answer = "A clear mental model with key distinctions and examples that transform how you think about this."
        confirmation = f"It sounds like you want to deeply understand this concept. I'll help you build a clear mental model."
    else:
        mode = "research"
        answer_type = "facts"
        ideal_answer = "Well-sourced answers to your questions with key insights synthesized from reliable sources."
        confirmation = f"It sounds like you want to research this topic. I'll help you find and synthesize reliable information."

    return JourneyDesignBrief(
        original_question=question,
        ideal_answer=ideal_answer,
        answer_type=answer_type,
        primary_mode=mode,
        confirmation_message=confirmation,
    )


# =============================================================================
# Routes
# =============================================================================

@router.post("/analyze", response_model=JourneyAnalyzeResponse)
async def analyze_journey(request: JourneyAnalyzeRequest):
    """
    Analyze a user's question and design their learning journey.

    This endpoint:
    1. Parses the question shape (heuristic routing)
    2. Works backwards from the ideal answer
    3. Returns a JourneyDesignBrief for confirmation
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # TODO: Use Orchestrator agent for real analysis
    brief = analyze_question_heuristic(request.question)

    return JourneyAnalyzeResponse(brief=brief)


@router.post("/confirm", response_model=SessionInitResponse)
async def confirm_journey(request: JourneyConfirmRequest):
    """
    Confirm a journey and initialize a session.

    This endpoint:
    1. Creates a new session with the journey brief
    2. Initializes mode-specific data
    3. Returns the session ID for streaming
    """
    if not request.confirmed:
        raise HTTPException(status_code=400, detail="Journey not confirmed")

    # Use alternative mode if provided
    mode = request.alternative_mode or request.brief.primary_mode

    # Create session
    session = store.create(journey_brief=request.brief, mode=mode)

    # Initialize stream for this session
    stream_manager.create_stream(session.id)

    return SessionInitResponse(
        session_id=session.id,
        mode=session.mode,
    )


@router.get("/stream")
async def stream_journey(session_id: str = Query(..., description="Session ID")):
    """
    SSE stream for session events.

    Connect to this endpoint to receive real-time updates as the
    agent processes your journey.
    """
    # Verify session exists
    if not store.exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Ensure stream exists
    if not stream_manager.has_stream(session_id):
        stream_manager.create_stream(session_id)

    # Get session for initial event
    session = store.get(session_id)

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
