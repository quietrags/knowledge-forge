"""
Main Orchestrator for Knowledge Forge.

Coordinates question routing, journey design, and phase management.
This is the main interface used by the API layer.
"""

from __future__ import annotations

from typing import Optional, Callable, Awaitable, AsyncGenerator
from anthropic import Anthropic

from server.persistence import (
    JourneyDesignBrief,
    Session,
    SessionStore,
    Mode,
)
from server.api.streaming import (
    SSEEvent,
    SSEStreamManager,
    agent_thinking,
    agent_speaking,
    agent_complete,
    session_started,
    narrative_updated,
    data_event,
)
from .router import QuestionRouter
from .journey_designer import JourneyDesigner
from .phase_manager import PhaseManager


class Orchestrator:
    """
    Main orchestrator for Knowledge Forge.

    Provides a unified interface for:
    - Question analysis and routing
    - Journey initialization
    - Phase management (Build mode)
    - Event emission to SSE streams

    This class is designed to be used by the API layer and provides
    all the high-level operations needed for journey orchestration.
    """

    def __init__(
        self,
        store: Optional[SessionStore] = None,
        stream_manager: Optional[SSEStreamManager] = None,
        client: Optional[Anthropic] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            store: Session store for persistence
            stream_manager: Manager for SSE event streams
            client: Anthropic client for LLM operations
        """
        self.store = store or SessionStore()
        self.stream_manager = stream_manager
        self._client = client

        # Initialize sub-components
        self.journey_designer = JourneyDesigner(self.store, self._client)
        self.phase_manager = PhaseManager(self._emit_event)

    @property
    def client(self) -> Anthropic:
        """Lazy-load Anthropic client."""
        if self._client is None:
            self._client = Anthropic()
        return self._client

    async def _emit_event(self, session_id: str, event: SSEEvent) -> None:
        """Emit an SSE event to the session's stream."""
        if self.stream_manager:
            await self.stream_manager.emit(session_id, event)

    # =========================================================================
    # Question Analysis
    # =========================================================================

    async def analyze_question(
        self,
        question: str,
        learner_context: Optional[str] = None,
        use_llm: bool = True,
    ) -> JourneyDesignBrief:
        """
        Analyze a question and return a journey design brief.

        This is the first step in any journey - understanding what the user
        really needs and how to route them.

        Args:
            question: The user's question
            learner_context: Optional context about the learner
            use_llm: Whether to use LLM for deep analysis

        Returns:
            JourneyDesignBrief with routing decision and confirmation
        """
        return await self.journey_designer.analyze_question(
            question, learner_context, use_llm
        )

    def analyze_question_sync(self, question: str) -> JourneyDesignBrief:
        """
        Synchronous version of analyze_question using heuristics only.

        This is used for quick routing when async is not available.
        """
        return self.journey_designer.router.analyze_quick(question)

    # =========================================================================
    # Journey Initialization
    # =========================================================================

    async def initialize_journey(
        self,
        brief: JourneyDesignBrief,
        alternative_mode: Optional[Mode] = None,
    ) -> Session:
        """
        Initialize a new journey session.

        This creates the session with mode-specific data structures
        and prepares it for agent interaction.

        Args:
            brief: The journey design brief from analysis
            alternative_mode: Override mode if user selected different

        Returns:
            Initialized Session ready for use
        """
        # Create session
        session = self.journey_designer.initialize_session(brief, alternative_mode)

        # Create SSE stream for this session
        if self.stream_manager:
            self.stream_manager.create_stream(session.id)

        return session

    # =========================================================================
    # Phase Management (Build Mode)
    # =========================================================================

    def get_phase_status(self, session: Session) -> dict:
        """
        Get the current phase status for a Build session.

        Returns detailed information about grounding progress
        and transition readiness.
        """
        return self.phase_manager.get_grounding_summary(session)

    async def transition_to_making(
        self,
        session: Session,
        force: bool = False,
    ) -> bool:
        """
        Transition a Build session from Grounding to Making phase.

        Args:
            session: The session to transition
            force: Skip grounding completion check

        Returns:
            True if transition was successful
        """
        result = await self.phase_manager.transition_to_making(session, force)
        if result.transitioned:
            self.store.save(session)
        return result.transitioned

    def add_grounding_concept(
        self,
        session: Session,
        name: str,
        distinction: str,
        sufficient: bool = False,
    ):
        """Add a grounding concept to a Build session."""
        concept = self.phase_manager.add_grounding_concept(
            session, name, distinction, sufficient
        )
        self.store.save(session)
        return concept

    def mark_grounding_ready(self, session: Session) -> bool:
        """Mark grounding as ready for transition."""
        result = self.phase_manager.mark_grounding_ready(session)
        if result:
            self.store.save(session)
        return result

    # =========================================================================
    # Agent Communication
    # =========================================================================

    def get_initial_prompt(
        self,
        session: Session,
        brief: JourneyDesignBrief,
    ) -> str:
        """
        Get the initial prompt to send to an agent for a session.

        This prompt gives the agent context about the user's goal
        and how to proceed.
        """
        return self.journey_designer.get_initial_agent_prompt(session, brief)

    async def process_message(
        self,
        session: Session,
        message: str,
        context: Optional[dict] = None,
    ) -> AsyncGenerator[SSEEvent, None]:
        """
        Process a user message in the context of a session.

        This is a stub that will be expanded when agents are implemented.
        For now, it emits placeholder events.

        Args:
            session: The active session
            message: User's message
            context: Optional UI context (selected question, active tab, etc.)

        Yields:
            SSE events as the agent processes the message
        """
        # Emit thinking event
        yield agent_thinking(f"Processing your message...")

        # TODO: Route to appropriate agent based on session.mode
        # For now, emit a placeholder response

        yield agent_speaking("I understand your question. ")
        yield agent_speaking(f"You asked about: {message}. ")
        yield agent_speaking("Agent integration is coming in Phase 3.")

        yield agent_complete("Message processed")

    # =========================================================================
    # Session Management
    # =========================================================================

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self.store.get_or_none(session_id)

    def save_session(self, session: Session) -> str:
        """Save a session and return the file path."""
        return self.store.save(session)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        return self.store.delete(session_id)

    def list_sessions(self) -> list[dict]:
        """List all sessions with metadata."""
        return self.store.list_with_metadata()

    # =========================================================================
    # Stream Management
    # =========================================================================

    def create_stream(self, session_id: str) -> None:
        """Create an SSE stream for a session."""
        if self.stream_manager:
            self.stream_manager.create_stream(session_id)

    def close_stream(self, session_id: str) -> None:
        """Close an SSE stream for a session."""
        if self.stream_manager:
            self.stream_manager.close_stream(session_id)

    def has_stream(self, session_id: str) -> bool:
        """Check if a session has an active stream."""
        if self.stream_manager:
            return self.stream_manager.has_stream(session_id)
        return False
