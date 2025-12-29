"""
Chat routes for processing user messages.

Endpoints:
- POST /api/chat - Send a message to the agent
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from server.persistence import SessionStore, SessionNotFoundError
from ..streaming import (
    stream_manager,
    agent_thinking,
    agent_speaking,
    agent_complete,
    error_event,
)


# =============================================================================
# Router
# =============================================================================

router = APIRouter()

# Session store instance
store = SessionStore()


# =============================================================================
# Request/Response Models
# =============================================================================

class ChatContext(BaseModel):
    """Context for the chat message."""
    selected_question_id: Optional[str] = None
    active_tab: Optional[int] = None


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    session_id: str
    message: str
    context: Optional[ChatContext] = None


class ChatResponse(BaseModel):
    """Response acknowledging message received."""
    accepted: bool
    message: str


# =============================================================================
# Background Processing
# =============================================================================

async def process_chat_message(
    session_id: str,
    message: str,
    context: Optional[ChatContext],
):
    """
    Process a chat message in the background.

    This is where the agent logic will be invoked.
    Currently a placeholder that echoes the message.

    TODO: Integrate with Orchestrator and Mode agents.
    """
    try:
        # Get session
        session = store.get(session_id)

        # Emit thinking event
        await stream_manager.emit(
            session_id,
            agent_thinking(f"Processing your message in {session.mode} mode..."),
        )

        # TODO: Route to appropriate agent based on mode
        # For now, just echo the message back

        # Simulate streaming response
        response_parts = [
            f"I received your message: \"{message}\"\n\n",
            f"You are currently in **{session.mode}** mode. ",
        ]

        if session.mode == "build" and session.phase:
            response_parts.append(f"(Phase: {session.phase})\n\n")
        else:
            response_parts.append("\n\n")

        response_parts.append(
            "This is a placeholder response. "
            "The real agent integration will process your message and update the session state."
        )

        # Stream the response
        for part in response_parts:
            await stream_manager.emit(session_id, agent_speaking(part))

        # Emit completion
        await stream_manager.emit(
            session_id,
            agent_complete("Message processed (placeholder)"),
        )

    except SessionNotFoundError:
        await stream_manager.emit(
            session_id,
            error_event("Session not found", code="SESSION_NOT_FOUND"),
        )
    except Exception as e:
        await stream_manager.emit(
            session_id,
            error_event(f"Error processing message: {str(e)}", code="PROCESSING_ERROR"),
        )


# =============================================================================
# Routes
# =============================================================================

@router.post("", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
):
    """
    Send a message to the agent.

    This endpoint accepts the message and processes it asynchronously.
    Results are streamed via the /api/journey/stream SSE endpoint.

    Returns 202 Accepted immediately, actual results via SSE.
    """
    # Validate session exists
    if not store.exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate message
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Ensure stream exists for this session
    if not stream_manager.has_stream(request.session_id):
        stream_manager.create_stream(request.session_id)

    # Process message in background
    background_tasks.add_task(
        process_chat_message,
        request.session_id,
        request.message,
        request.context,
    )

    return ChatResponse(
        accepted=True,
        message="Message accepted for processing",
    )
