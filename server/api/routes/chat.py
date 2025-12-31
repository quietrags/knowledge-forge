"""
Chat routes for processing user messages.

Endpoints:
- POST /api/chat - Send a message to the agent
"""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from server.persistence import SessionStore, SessionNotFoundError
from ..streaming import (
    stream_manager,
    agent_thinking,
    agent_speaking,
    agent_complete,
    error_event,
)

logger = logging.getLogger(__name__)


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
    selected_question_id: Optional[str] = Field(default=None, alias="selectedQuestionId")
    active_tab: Optional[int] = Field(default=None, alias="activeTab")

    model_config = {"populate_by_name": True}


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    session_id: str = Field(alias="sessionId")
    message: str
    context: Optional[ChatContext] = None

    model_config = {"populate_by_name": True}


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

    This routes to the appropriate mode agent (Research, Understand, Build)
    and streams SSE events back to the client.
    """
    print(f"[DEBUG] process_chat_message started: session_id={session_id}")

    # Import here to avoid circular imports
    from server.agents import get_or_create_agent, save_agent_state

    try:
        # Get session
        session = store.get(session_id)
        print(f"[DEBUG] Session loaded: mode={session.mode}, has_brief={session.journey_brief is not None}")

        # Validate we have a journey brief
        if not session.journey_brief:
            print(f"[DEBUG] No journey brief found!")
            await stream_manager.emit(
                session_id,
                error_event(
                    "Session has no journey brief. Please start a new journey first.",
                    code="NO_JOURNEY_BRIEF",
                ),
            )
            return

        # Create emit callback for the agent
        async def emit_event(event):
            print(f"[DEBUG] Emitting SSE event: type={event.type}")
            await stream_manager.emit(session_id, event)

        # Emit initial thinking event
        print(f"[DEBUG] Emitting initial agent.thinking event")
        await emit_event(agent_thinking(f"Processing in {session.mode} mode..."))

        # Get or create the appropriate agent
        print(f"[DEBUG] Getting or creating agent for mode: {session.mode}")
        agent = await get_or_create_agent(
            session=session,
            journey_brief=session.journey_brief,
            emit_event=emit_event,
            checkpoint_handler=None,  # TODO: Add checkpoint support
        )
        print(f"[DEBUG] Agent created/retrieved: {type(agent).__name__}")

        # Convert context to dict if provided
        ctx = {}
        if context:
            if context.selected_question_id:
                ctx["selected_question_id"] = context.selected_question_id
            if context.active_tab is not None:
                ctx["active_tab"] = context.active_tab

        # Process message through agent
        print(f"[DEBUG] Starting agent.process_message...")
        try:
            event_count = 0
            async for event in agent.process_message(message, ctx):
                event_count += 1
                print(f"[DEBUG] Agent yielded event #{event_count}: type={event.type}")
                await emit_event(event)
            print(f"[DEBUG] Agent finished processing, total events: {event_count}")
        except Exception as agent_error:
            print(f"[DEBUG] Agent error: {agent_error}")
            logger.exception(f"Agent error processing message: {agent_error}")
            await emit_event(
                error_event(
                    f"Agent error: {str(agent_error)}",
                    code="AGENT_ERROR",
                )
            )
            return

        # Save agent state back to session
        print(f"[DEBUG] Saving agent state")
        save_agent_state(session, agent)

        # Update session timestamp and save
        from datetime import datetime
        session.updated = datetime.utcnow()
        store.save(session)

        print(f"[DEBUG] Message processing complete for session {session_id}")
        logger.info(f"Processed message for session {session_id} in {session.mode} mode")

    except SessionNotFoundError:
        print(f"[DEBUG] SessionNotFoundError for {session_id}")
        await stream_manager.emit(
            session_id,
            error_event("Session not found", code="SESSION_NOT_FOUND"),
        )
    except Exception as e:
        print(f"[DEBUG] Exception in process_chat_message: {e}")
        logger.exception(f"Error processing chat message: {e}")
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
    print(f"[DEBUG] POST /api/chat received: session_id={request.session_id}, message={request.message[:50]}...")

    # Validate session exists
    if not store.exists(request.session_id):
        print(f"[DEBUG] Session not found: {request.session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate message
    if not request.message.strip():
        print(f"[DEBUG] Empty message rejected")
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Ensure stream exists for this session
    if not stream_manager.has_stream(request.session_id):
        print(f"[DEBUG] Creating stream for session: {request.session_id}")
        stream_manager.create_stream(request.session_id)

    print(f"[DEBUG] Queueing background task for message processing")

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
