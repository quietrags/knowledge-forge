"""
Agent Factory for Knowledge Forge.

Creates the appropriate agent based on session mode.
"""

from __future__ import annotations

from typing import Callable, Awaitable, Optional

from server.persistence import Session, JourneyDesignBrief, Mode
from server.api.streaming import SSEEvent
from .base import BaseForgeAgent, Checkpoint, CheckpointResponse
from .research import ResearchAgent
from .understand import UnderstandAgent
from .build import BuildAgent


def create_agent(
    session: Session,
    emit_event: Callable[[SSEEvent], Awaitable[None]],
    checkpoint_handler: Optional[Callable[[Checkpoint], Awaitable[CheckpointResponse]]] = None,
) -> BaseForgeAgent:
    """
    Create the appropriate agent for a session's mode.

    Args:
        session: The active session
        emit_event: Async callback to emit SSE events
        checkpoint_handler: Optional async callback for checkpoints

    Returns:
        The appropriate mode agent (Research, Understand, or Build)

    Raises:
        ValueError: If session.mode is invalid
    """
    mode = session.mode

    if mode == "research":
        return ResearchAgent(session, emit_event, checkpoint_handler)
    elif mode == "understand":
        return UnderstandAgent(session, emit_event, checkpoint_handler)
    elif mode == "build":
        return BuildAgent(session, emit_event, checkpoint_handler)
    else:
        raise ValueError(f"Unknown mode: {mode}")


async def get_or_create_agent(
    session: Session,
    journey_brief: JourneyDesignBrief,
    emit_event: Callable[[SSEEvent], Awaitable[None]],
    checkpoint_handler: Optional[Callable[[Checkpoint], Awaitable[CheckpointResponse]]] = None,
) -> BaseForgeAgent:
    """
    Get an agent for a session, initializing or restoring state as needed.

    This is the main entry point for getting a ready-to-use agent.

    Args:
        session: The active session
        journey_brief: The journey design brief
        emit_event: Async callback to emit SSE events
        checkpoint_handler: Optional async callback for checkpoints

    Returns:
        An initialized agent ready to process messages
    """
    agent = create_agent(session, emit_event, checkpoint_handler)

    # Check if we have existing agent state to restore
    agent_state = get_agent_state_for_restore(session)

    if agent_state.get("current_phase"):
        # Restore from existing state
        await agent.restore_state(agent_state)
    else:
        # Initialize fresh
        await agent.initialize(journey_brief)

    return agent


def save_agent_state(session: Session, agent: BaseForgeAgent) -> None:
    """
    Save agent state back to the session.

    Call this after processing messages to persist agent progress.

    Args:
        session: The session to update
        agent: The agent whose state to save
    """
    state = agent.get_state()

    # Store the complete agent state in the counters dict
    # This maps the agent's internal state to the session's AgentState model
    session.agent_state.counters = {
        "current_phase": state.get("current_phase"),
        "agent_type": state.get("agent_type"),
        "phase_context": state.get("phase_context", {}),
        "transition_history": state.get("transition_history", []),
    }

    # Mode-specific state (anchor_map for Build, slo_progress for Understand, etc.)
    # is stored in the phase_context by the agent's _serialize_phase_context method


def get_agent_state_for_restore(session: Session) -> dict:
    """
    Get the agent state from session in the format expected by restore_state.

    Args:
        session: The session to extract state from

    Returns:
        Dict with current_phase, phase_context, transition_history
    """
    counters = session.agent_state.counters if session.agent_state else {}

    return {
        "current_phase": counters.get("current_phase"),
        "phase_context": counters.get("phase_context", {}),
        "transition_history": counters.get("transition_history", []),
    }
