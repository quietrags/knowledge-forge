"""
Server-Sent Events (SSE) streaming utilities.
Provides event emission for real-time updates to the frontend.
"""

from __future__ import annotations

import json
import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Any, Literal
from dataclasses import dataclass, field, asdict


# =============================================================================
# SSE Event Types
# =============================================================================

SSEEventType = Literal[
    # Session lifecycle
    "session.started",
    "session.resumed",
    "session.ended",
    # Agent status
    "agent.thinking",
    "agent.speaking",
    "agent.complete",
    # Research data events
    "data.question.added",
    "data.question.updated",
    "data.question.answered",
    "data.category.added",
    "data.category.insight",
    "data.key_insight.added",
    "data.adjacent_question.added",
    # Understand data events
    "data.assumption.surfaced",
    "data.assumption.discarded",
    "data.concept.added",
    "data.concept.distinguished",
    "data.model.integrated",
    # Build data events
    "data.grounding_concept.added",
    "data.construct.added",
    "data.decision.added",
    "data.capability.added",
    # Shared events
    "narrative.updated",
    "phase.changed",
    "path.updated",
    # Errors
    "error",
]


# =============================================================================
# SSE Event Model
# =============================================================================

@dataclass
class SSEEvent:
    """
    A Server-Sent Event to be streamed to the client.

    Usage:
        event = SSEEvent(type="agent.thinking", payload={"message": "Processing..."})
        yield event.format()
    """
    type: SSEEventType
    payload: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def format(self) -> str:
        """Format as SSE event string."""
        data = json.dumps({
            "type": self.type,
            "timestamp": self.timestamp,
            "payload": self.payload,
        })
        return f"event: {self.type}\ndata: {data}\n\n"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }


# =============================================================================
# Event Factory Functions
# =============================================================================

def session_started(session_id: str, mode: str) -> SSEEvent:
    """Create a session.started event."""
    return SSEEvent(
        type="session.started",
        payload={"sessionId": session_id, "mode": mode},
    )


def session_resumed(session_id: str, mode: str) -> SSEEvent:
    """Create a session.resumed event."""
    return SSEEvent(
        type="session.resumed",
        payload={"sessionId": session_id, "mode": mode},
    )


def agent_thinking(message: str) -> SSEEvent:
    """Create an agent.thinking event."""
    return SSEEvent(
        type="agent.thinking",
        payload={"message": message},
    )


def agent_speaking(delta: str) -> SSEEvent:
    """Create an agent.speaking event (streaming text)."""
    return SSEEvent(
        type="agent.speaking",
        payload={"delta": delta},
    )


def agent_complete(summary: str) -> SSEEvent:
    """Create an agent.complete event."""
    return SSEEvent(
        type="agent.complete",
        payload={"summary": summary},
    )


def narrative_updated(mode: str, narrative: dict, delta: str | None = None) -> SSEEvent:
    """Create a narrative.updated event."""
    payload = {"mode": mode, "narrative": narrative}
    if delta:
        payload["delta"] = delta
    return SSEEvent(type="narrative.updated", payload=payload)


def phase_changed(from_phase: str, to_phase: str) -> SSEEvent:
    """Create a phase.changed event."""
    return SSEEvent(
        type="phase.changed",
        payload={"from": from_phase, "to": to_phase},
    )


def error_event(message: str, code: str | None = None) -> SSEEvent:
    """Create an error event."""
    payload = {"message": message}
    if code:
        payload["code"] = code
    return SSEEvent(type="error", payload=payload)


def data_event(event_type: SSEEventType, **kwargs) -> SSEEvent:
    """Create a generic data event."""
    return SSEEvent(type=event_type, payload=kwargs)


# =============================================================================
# SSE Stream Manager
# =============================================================================

class SSEStreamManager:
    """
    Manages SSE event streams for active sessions.

    Each session can have one active stream. Events are queued
    and delivered to connected clients.
    """

    def __init__(self):
        self._queues: dict[str, asyncio.Queue[SSEEvent | None]] = {}

    def create_stream(self, session_id: str) -> None:
        """Create a new event queue for a session."""
        if session_id not in self._queues:
            self._queues[session_id] = asyncio.Queue()

    def close_stream(self, session_id: str) -> None:
        """Close the stream for a session."""
        if session_id in self._queues:
            # Send None to signal stream end
            self._queues[session_id].put_nowait(None)
            del self._queues[session_id]

    def close_all_streams(self) -> None:
        """Close all active streams (for graceful shutdown)."""
        for session_id in list(self._queues.keys()):
            self._queues[session_id].put_nowait(None)
        self._queues.clear()

    async def emit(self, session_id: str, event: SSEEvent) -> None:
        """Emit an event to a session's stream."""
        if session_id in self._queues:
            await self._queues[session_id].put(event)

    def emit_sync(self, session_id: str, event: SSEEvent) -> None:
        """Emit an event synchronously (for use in non-async contexts)."""
        if session_id in self._queues:
            self._queues[session_id].put_nowait(event)

    async def subscribe(self, session_id: str) -> AsyncGenerator[str, None]:
        """
        Subscribe to a session's event stream.

        Yields SSE-formatted event strings until the stream is closed.
        """
        if session_id not in self._queues:
            self.create_stream(session_id)

        queue = self._queues[session_id]

        try:
            while True:
                try:
                    # Use timeout so we can respond to shutdown signals
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    if event is None:
                        # Stream closed
                        break
                    yield event.format()
                except asyncio.TimeoutError:
                    # Send keepalive comment to maintain connection
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            # Graceful shutdown on Ctrl-C
            pass
        finally:
            # Clean up if we're the last subscriber
            pass

    def has_stream(self, session_id: str) -> bool:
        """Check if a session has an active stream."""
        return session_id in self._queues


# Global stream manager instance
stream_manager = SSEStreamManager()
