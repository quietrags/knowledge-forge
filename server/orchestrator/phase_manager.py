"""
Phase Manager for Knowledge Forge.

Handles Build mode phase transitions between Grounding and Making.
"""

from __future__ import annotations

from typing import Optional, Callable, Awaitable
from dataclasses import dataclass

from server.persistence import Session, BuildPhase, GroundingConcept
from server.api.streaming import SSEEvent, phase_changed


@dataclass
class PhaseTransitionResult:
    """Result of a phase transition attempt."""

    transitioned: bool
    from_phase: Optional[BuildPhase]
    to_phase: Optional[BuildPhase]
    reason: str


class PhaseManager:
    """
    Manages Build mode phase transitions.

    Build has two phases:
    1. GROUNDING: Minimal understanding needed to build well
    2. MAKING: Core build with constructs, decisions, capabilities
    """

    # Minimum concepts needed before transitioning to Making
    MIN_GROUNDING_CONCEPTS = 2

    def __init__(
        self,
        emit_event: Optional[Callable[[str, SSEEvent], Awaitable[None]]] = None,
    ):
        """
        Initialize the phase manager.

        Args:
            emit_event: Async function to emit SSE events (session_id, event)
        """
        self.emit_event = emit_event

    def get_phase(self, session: Session) -> Optional[BuildPhase]:
        """Get the current phase for a session."""
        if session.mode != "build":
            return None
        return session.phase

    def is_grounding_complete(self, session: Session) -> bool:
        """
        Check if grounding phase is complete.

        Grounding is complete when:
        1. User explicitly marked it ready, OR
        2. Sufficient grounding concepts have been grasped
        """
        if session.mode != "build":
            return False

        # User explicitly marked ready
        if session.grounding_ready:
            return True

        # Sufficient concepts grasped
        sufficient_count = sum(
            1 for concept in session.grounding_concepts if concept.sufficient
        )
        return sufficient_count >= self.MIN_GROUNDING_CONCEPTS

    def can_transition_to_making(self, session: Session) -> tuple[bool, str]:
        """
        Check if session can transition to Making phase.

        Returns:
            Tuple of (can_transition, reason)
        """
        if session.mode != "build":
            return False, "Not in build mode"

        if session.phase != "grounding":
            return False, f"Already in {session.phase} phase"

        if not self.is_grounding_complete(session):
            concepts_count = len(session.grounding_concepts)
            sufficient_count = sum(
                1 for c in session.grounding_concepts if c.sufficient
            )
            return False, (
                f"Grounding not complete. "
                f"Have {concepts_count} concepts ({sufficient_count} sufficient). "
                f"Need at least {self.MIN_GROUNDING_CONCEPTS} sufficient concepts, "
                f"or mark grounding as ready."
            )

        return True, "Ready to transition"

    async def transition_to_making(
        self,
        session: Session,
        force: bool = False,
    ) -> PhaseTransitionResult:
        """
        Transition a session from Grounding to Making phase.

        Args:
            session: The session to transition
            force: If True, skip grounding completion check

        Returns:
            PhaseTransitionResult with transition details
        """
        from_phase = session.phase

        if not force:
            can_transition, reason = self.can_transition_to_making(session)
            if not can_transition:
                return PhaseTransitionResult(
                    transitioned=False,
                    from_phase=from_phase,
                    to_phase=None,
                    reason=reason,
                )

        # Perform transition
        session.phase = "making"

        # Emit phase change event
        if self.emit_event:
            event = phase_changed("grounding", "making")
            await self.emit_event(session.id, event)

        return PhaseTransitionResult(
            transitioned=True,
            from_phase="grounding",
            to_phase="making",
            reason="Successfully transitioned to Making phase",
        )

    def add_grounding_concept(
        self,
        session: Session,
        name: str,
        distinction: str,
        sufficient: bool = False,
    ) -> GroundingConcept:
        """
        Add a grounding concept to the session.

        Args:
            session: The session to add to
            name: Concept name
            distinction: What distinguishes this concept
            sufficient: Whether this concept is sufficiently grasped

        Returns:
            The created GroundingConcept
        """
        concept = GroundingConcept(
            name=name,
            distinction=distinction,
            sufficient=sufficient,
        )
        session.grounding_concepts.append(concept)
        return concept

    def mark_concept_sufficient(
        self,
        session: Session,
        concept_id: str,
    ) -> bool:
        """
        Mark a grounding concept as sufficiently grasped.

        Returns:
            True if concept was found and updated
        """
        for concept in session.grounding_concepts:
            if concept.id == concept_id:
                concept.sufficient = True
                return True
        return False

    def mark_grounding_ready(self, session: Session) -> bool:
        """
        Mark grounding as ready to transition to Making.

        This is an explicit user action indicating they're ready to proceed.

        Returns:
            True if successful
        """
        if session.mode != "build":
            return False
        session.grounding_ready = True
        return True

    def get_grounding_summary(self, session: Session) -> dict:
        """
        Get a summary of the grounding phase status.

        Returns:
            Dict with grounding status information
        """
        if session.mode != "build":
            return {"error": "Not in build mode"}

        total_concepts = len(session.grounding_concepts)
        sufficient_concepts = sum(
            1 for c in session.grounding_concepts if c.sufficient
        )
        can_transition, reason = self.can_transition_to_making(session)

        return {
            "phase": session.phase,
            "totalConcepts": total_concepts,
            "sufficientConcepts": sufficient_concepts,
            "minRequired": self.MIN_GROUNDING_CONCEPTS,
            "userMarkedReady": session.grounding_ready,
            "canTransition": can_transition,
            "reason": reason,
        }
