"""
Base Agent for Knowledge Forge.

Defines the phase graph pattern using the Claude Agent SDK.
See docs/agent-architecture.md for full specification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    AsyncGenerator,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Any,
    Awaitable,
)

from server.persistence import JourneyDesignBrief, Session
from server.api.streaming import SSEEvent, agent_thinking, agent_complete, agent_awaiting_input


# =============================================================================
# Phase Transition Definition
# =============================================================================

@dataclass
class PhaseTransition:
    """
    Defines a valid transition between phases.

    Transitions can be forward (normal progression) or backward
    (returning to earlier phase due to discovery/gap).
    """
    from_phase: Enum
    to_phase: Enum
    condition: str  # Human-readable condition name
    is_backward: bool = False
    priority: int = 0  # Higher priority evaluated first

    def __repr__(self) -> str:
        direction = "←" if self.is_backward else "→"
        return f"{self.from_phase.value} {direction} {self.to_phase.value} ({self.condition})"


@dataclass
class TransitionRecord:
    """Record of a phase transition for history tracking."""
    from_phase: str
    to_phase: str
    reason: str
    is_backward: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "fromPhase": self.from_phase,
            "toPhase": self.to_phase,
            "reason": self.reason,
            "isBackward": self.is_backward,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# Base Phase Context
# =============================================================================

@dataclass
class BasePhaseContext:
    """
    Base context that persists across phase visits.

    All agents extend this with phase-specific state.
    """
    # Visit tracking
    phase_visits: dict[str, int] = field(default_factory=dict)

    # Transition history
    transition_history: list[TransitionRecord] = field(default_factory=list)

    # Current backward trigger (if any)
    backward_trigger: Optional[str] = None
    backward_trigger_detail: Optional[str] = None

    # Flag to block phase transitions until user responds
    # When set by a "mark_*_asked" tool, prevents transitions until cleared
    awaiting_user_input: bool = False

    def increment_visit(self, phase: Enum) -> int:
        """Increment and return visit count for a phase."""
        key = phase.value
        self.phase_visits[key] = self.phase_visits.get(key, 0) + 1
        return self.phase_visits[key]

    def get_visit_count(self, phase: Enum) -> int:
        """Get visit count for a phase."""
        return self.phase_visits.get(phase.value, 0)

    def record_transition(
        self,
        from_phase: Enum,
        to_phase: Enum,
        reason: str,
        is_backward: bool,
    ) -> None:
        """Record a phase transition."""
        self.transition_history.append(TransitionRecord(
            from_phase=from_phase.value,
            to_phase=to_phase.value,
            reason=reason,
            is_backward=is_backward,
        ))

        if is_backward:
            self.backward_trigger = reason
        else:
            self.backward_trigger = None
            self.backward_trigger_detail = None


# =============================================================================
# Checkpoint Definition
# =============================================================================

@dataclass
class Checkpoint:
    """
    A blocking checkpoint where user approval is required.
    """
    id: str
    message: str
    options: list[str] = field(default_factory=lambda: ["Proceed", "Modify", "Cancel"])
    requires_approval: bool = True


@dataclass
class CheckpointResponse:
    """Response from a checkpoint."""
    approved: bool
    action: str = "proceed"  # proceed, modify, cancel
    modifications: Optional[dict] = None
    rejection_reason: Optional[str] = None


# =============================================================================
# Type Variables
# =============================================================================

PhaseType = TypeVar("PhaseType", bound=Enum)
ContextType = TypeVar("ContextType", bound=BasePhaseContext)


# =============================================================================
# SSE Event Emitter Protocol
# =============================================================================

class SSEEventEmitter:
    """
    Wrapper for emitting SSE events.

    Used by agents and tools to send real-time updates to the frontend.
    """

    def __init__(self, emit_fn: Callable[[SSEEvent], Awaitable[None]]):
        self._emit = emit_fn
        self._queue: list[SSEEvent] = []

    async def emit(self, event: SSEEvent) -> None:
        """Emit an SSE event."""
        await self._emit(event)

    def emit_sync(self, event: SSEEvent) -> None:
        """Queue an event for later emission (for sync tool handlers)."""
        self._queue.append(event)

    async def flush(self) -> None:
        """Emit all queued events."""
        for event in self._queue:
            await self._emit(event)
        self._queue.clear()


# =============================================================================
# Base Agent
# =============================================================================

class BaseForgeAgent(ABC, Generic[PhaseType, ContextType]):
    """
    Base class for all Knowledge Forge mode agents.

    Uses the Claude Agent SDK for agentic loops with custom tools.

    Implements the phase graph pattern with support for:
    - Forward and backward transitions
    - Phase context persistence
    - Re-entry behavior
    - Checkpoints
    - SSE event emission via custom tools

    Subclasses must implement:
    - Phase enum
    - phase_transitions property
    - _execute_phase() for each phase
    - _evaluate_transition_condition()
    - _get_phase_prompt()
    - _create_phase_context()
    - _create_phase_tools()
    """

    def __init__(
        self,
        session: Session,
        emit_event: Callable[[SSEEvent], Awaitable[None]],
        checkpoint_handler: Optional[Callable[[Checkpoint], Awaitable[CheckpointResponse]]] = None,
    ):
        """
        Initialize the agent.

        Args:
            session: The session this agent is working in
            emit_event: Async callback to emit SSE events
            checkpoint_handler: Async callback to handle checkpoints (blocking)
        """
        self.session = session
        self._emit_fn = emit_event
        self.emitter = SSEEventEmitter(emit_event)
        self._checkpoint_handler = checkpoint_handler

        # State (initialized in initialize())
        self.journey_brief: Optional[JourneyDesignBrief] = None
        self.current_phase: Optional[PhaseType] = None
        self.phase_context: Optional[ContextType] = None
        self._transition_reason: Optional[str] = None

    # =========================================================================
    # Abstract Properties - Must be defined by subclasses
    # =========================================================================

    @property
    @abstractmethod
    def Phase(self) -> type[PhaseType]:
        """The phase enum for this agent."""
        pass

    @property
    @abstractmethod
    def phase_transitions(self) -> list[PhaseTransition]:
        """All valid transitions (forward and backward)."""
        pass

    @property
    @abstractmethod
    def initial_phase(self) -> PhaseType:
        """The starting phase."""
        pass

    @property
    @abstractmethod
    def complete_phase(self) -> PhaseType:
        """The terminal phase."""
        pass

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """The type of agent (research, understand, build)."""
        pass

    # =========================================================================
    # Abstract Methods - Must be implemented by subclasses
    # =========================================================================

    @abstractmethod
    async def _execute_phase(
        self,
        phase: PhaseType,
        message: str,
        context: dict,
    ) -> AsyncGenerator[SSEEvent, None]:
        """
        Execute a single phase, yielding SSE events.

        This is where the agent's main work happens using the Claude Agent SDK.
        Each phase has different behavior and may use different tools.
        """
        pass

    @abstractmethod
    def _evaluate_transition_condition(
        self,
        transition: PhaseTransition,
    ) -> bool:
        """
        Check if a specific transition's condition is met.

        Called after phase execution to determine next phase.
        """
        pass

    @abstractmethod
    def _get_phase_prompt(
        self,
        phase: PhaseType,
        visit_count: int,
    ) -> str:
        """
        Get the prompt for a phase.

        Returns different prompts for initial entry vs re-entry.
        """
        pass

    @abstractmethod
    def _create_phase_context(self) -> ContextType:
        """Create the initial phase context for this agent."""
        pass

    @abstractmethod
    def _generate_completion_summary(self) -> str:
        """Generate a summary when the agent completes."""
        pass

    def _get_awaiting_input_prompt(self) -> str:
        """
        Get a prompt to show when waiting for user input.

        Override in subclasses to provide phase-specific prompts.
        Default returns a generic message.
        """
        return "Please provide your response to continue."

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    async def initialize(self, journey_brief: JourneyDesignBrief) -> None:
        """
        Initialize the agent for a new journey.

        Called when starting a new session.
        """
        self.journey_brief = journey_brief
        self.current_phase = self.initial_phase
        self.phase_context = self._create_phase_context()

        # Record initial phase visit
        self.phase_context.increment_visit(self.current_phase)

    async def restore_state(self, state: dict) -> None:
        """
        Restore agent from persisted state.

        Called when resuming a session.
        """
        # Restore current phase
        self.current_phase = self.Phase(state["current_phase"])

        # Restore phase context (subclasses override for specific fields)
        self._restore_phase_context(state.get("phase_context", {}))

        # Restore transition history
        self._restore_transition_history(state.get("transition_history", []))

    def get_state(self) -> dict:
        """
        Get current state for persistence.

        Returns state that can be serialized and restored.
        """
        return {
            "agent_type": self.agent_type,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "phase_context": self._serialize_phase_context(),
            "transition_history": [
                t.to_dict() for t in self.phase_context.transition_history
            ] if self.phase_context else [],
        }

    def _restore_phase_context(self, state: dict) -> None:
        """Restore phase context from state. Override in subclasses."""
        self.phase_context = self._create_phase_context()
        self.phase_context.phase_visits = state.get("phase_visits", {})
        self.phase_context.backward_trigger = state.get("backward_trigger")
        self.phase_context.backward_trigger_detail = state.get("backward_trigger_detail")

    def _restore_transition_history(self, history: list[dict]) -> None:
        """Restore transition history from state."""
        if self.phase_context:
            self.phase_context.transition_history = [
                TransitionRecord(
                    from_phase=t["fromPhase"],
                    to_phase=t["toPhase"],
                    reason=t["reason"],
                    is_backward=t["isBackward"],
                    timestamp=datetime.fromisoformat(t["timestamp"]),
                )
                for t in history
            ]

    def _serialize_phase_context(self) -> dict:
        """Serialize phase context to dict. Override in subclasses."""
        if not self.phase_context:
            return {}
        return {
            "phase_visits": self.phase_context.phase_visits,
            "backward_trigger": self.phase_context.backward_trigger,
            "backward_trigger_detail": self.phase_context.backward_trigger_detail,
        }

    # =========================================================================
    # Main Processing Loop
    # =========================================================================

    async def process_message(
        self,
        message: str,
        context: Optional[dict] = None,
    ) -> AsyncGenerator[SSEEvent, None]:
        """
        Process a user message through the phase graph.

        This is the main entry point for agent work. It:
        1. Executes the current phase using Claude Agent SDK
        2. Evaluates transitions (forward and backward)
        3. Handles checkpoints if required
        4. Continues until complete phase is reached
        """
        print(f"[DEBUG] BaseForgeAgent.process_message: message={message[:50]}...")
        print(f"[DEBUG] Current phase: {self.current_phase}, Complete phase: {self.complete_phase}")
        context = context or {}

        # Clear the awaiting_user_input flag since user has now responded
        if self.phase_context.awaiting_user_input:
            print(f"[DEBUG] User responded - clearing awaiting_user_input flag")
            self.phase_context.awaiting_user_input = False

        iteration = 0
        while self.current_phase != self.complete_phase:
            iteration += 1
            print(f"[DEBUG] Phase loop iteration #{iteration}, current_phase={self.current_phase}")
            # Announce current phase (for debugging, not shown to user)
            visit_count = self.phase_context.get_visit_count(self.current_phase)

            if visit_count > 1:
                # Re-entry
                yield agent_thinking(
                    f"Returning to {self.current_phase.value}: "
                    f"{self.phase_context.backward_trigger}"
                )

            # Execute current phase
            async for event in self._execute_phase(
                self.current_phase,
                message,
                context,
            ):
                yield event

            # Flush any queued events from tools
            await self.emitter.flush()

            # Evaluate transitions
            next_phase = self._evaluate_transitions()

            if next_phase != self.current_phase:
                is_backward = self._is_backward_transition(
                    self.current_phase,
                    next_phase,
                )

                # Record transition
                self.phase_context.record_transition(
                    self.current_phase,
                    next_phase,
                    self._transition_reason or "unknown",
                    is_backward,
                )

                # Emit phase change event
                yield SSEEvent(
                    type="phase.changed",
                    payload={
                        "fromPhase": self.current_phase.value,
                        "toPhase": next_phase.value,
                        "isBackward": is_backward,
                        "reason": self._transition_reason,
                    },
                )

                # Update phase and increment visit count
                self.current_phase = next_phase
                self.phase_context.increment_visit(next_phase)

                # Clear transition reason
                self._transition_reason = None
            else:
                # No transition occurred - the agent is likely waiting for user input
                # Break the loop to allow user interaction, next process_message()
                # call will continue from the same phase
                print(f"[DEBUG] No transition from {self.current_phase}, breaking to wait for user input")

                # Emit awaiting_input event so frontend knows it's user's turn
                input_prompt = self._get_awaiting_input_prompt()
                yield agent_awaiting_input(
                    prompt=input_prompt,
                    phase=self.current_phase.value,
                )
                break

        # Only emit completion if we reached the complete phase
        if self.current_phase == self.complete_phase:
            yield agent_complete(self._generate_completion_summary())

    # =========================================================================
    # Transition Evaluation
    # =========================================================================

    def _evaluate_transitions(self) -> PhaseType:
        """
        Evaluate all possible transitions from current phase.

        Returns the next phase (may be same as current if no transition).
        """
        # If awaiting user input, block all transitions
        # This prevents the agent from proceeding before user responds
        if self.phase_context.awaiting_user_input:
            print(f"[DEBUG] Blocking transitions - awaiting user input in {self.current_phase}")
            return self.current_phase

        # Get transitions from current phase
        current_transitions = [
            t for t in self.phase_transitions
            if t.from_phase == self.current_phase
        ]

        # Sort: backward first (higher priority), then by priority value
        sorted_transitions = sorted(
            current_transitions,
            key=lambda t: (-int(t.is_backward), -t.priority),
        )

        print(f"[DEBUG] Evaluating {len(sorted_transitions)} transitions from {self.current_phase}")

        for transition in sorted_transitions:
            result = self._evaluate_transition_condition(transition)
            print(f"[DEBUG]   {transition.condition}: {result}")
            if result:
                self._transition_reason = transition.condition
                print(f"[DEBUG] Transitioning to {transition.to_phase}")
                return transition.to_phase

        print(f"[DEBUG] No transition triggered, staying in {self.current_phase}")
        return self.current_phase

    def _is_backward_transition(
        self,
        from_phase: PhaseType,
        to_phase: PhaseType,
    ) -> bool:
        """Check if a transition is backward."""
        for t in self.phase_transitions:
            if t.from_phase == from_phase and t.to_phase == to_phase:
                return t.is_backward
        return False

    # =========================================================================
    # Checkpoint Handling
    # =========================================================================

    async def _handle_checkpoint(
        self,
        checkpoint: Checkpoint,
    ) -> CheckpointResponse:
        """
        Handle a blocking checkpoint.

        If no checkpoint handler is configured, auto-approves.
        """
        if self._checkpoint_handler:
            return await self._checkpoint_handler(checkpoint)

        # Default: auto-approve
        return CheckpointResponse(approved=True)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _emit_data_event(
        self,
        event_type: str,
        **kwargs,
    ) -> SSEEvent:
        """Create a data event."""
        return SSEEvent(type=event_type, payload=kwargs)
