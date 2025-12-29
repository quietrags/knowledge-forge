"""
Session store for CRUD operations on learning sessions.
Provides high-level API for session management.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
import uuid

from .file_backend import FileBackend
from .models import (
    Session,
    JourneyDesignBrief,
    Mode,
    BuildPhase,
    ResearchModeData,
    UnderstandModeData,
    BuildModeData,
    GroundingConcept,
    AgentState,
)


class SessionNotFoundError(Exception):
    """Raised when a session is not found."""
    pass


class SessionStore:
    """
    High-level session CRUD operations.
    Handles serialization/deserialization of Session models.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.backend = FileBackend(data_dir)

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create(
        self,
        journey_brief: Optional[JourneyDesignBrief] = None,
        mode: Mode = "research",
    ) -> Session:
        """
        Create a new session.

        Args:
            journey_brief: The journey design brief (optional)
            mode: Initial mode (default: research)

        Returns:
            The created Session
        """
        session = Session(
            id=str(uuid.uuid4()),
            created=datetime.now(timezone.utc),
            updated=datetime.now(timezone.utc),
            journey_brief=journey_brief,
            mode=mode,
        )

        # Initialize mode-specific data
        if mode == "research":
            session.research_data = ResearchModeData()
        elif mode == "understand":
            session.understand_data = UnderstandModeData()
        elif mode == "build":
            session.build_data = BuildModeData()
            session.phase = "grounding"

        self._save(session)
        return session

    def get(self, session_id: str) -> Session:
        """
        Get a session by ID.

        Args:
            session_id: The session ID

        Returns:
            The Session

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        data = self.backend.read_session(session_id)
        if data is None:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        return Session.model_validate(data)

    def get_or_none(self, session_id: str) -> Optional[Session]:
        """Get a session by ID, return None if not found."""
        try:
            return self.get(session_id)
        except SessionNotFoundError:
            return None

    def save(self, session: Session) -> Session:
        """
        Save a session (update).

        Args:
            session: The session to save

        Returns:
            The saved Session (with updated timestamp)
        """
        session.updated = datetime.now(timezone.utc)
        self._save(session)
        return session

    def delete(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: The session ID

        Returns:
            True if deleted, False if didn't exist
        """
        return self.backend.delete_session(session_id)

    def list(self) -> list[str]:
        """
        List all session IDs.

        Returns:
            List of session IDs
        """
        return self.backend.list_sessions()

    def list_with_metadata(self) -> list[dict]:
        """
        List all sessions with basic metadata.

        Returns:
            List of dicts with id, created, updated, mode, topic
        """
        sessions = []
        for session_id in self.list():
            try:
                session = self.get(session_id)
                topic = ""
                if session.journey_brief:
                    topic = session.journey_brief.original_question[:50]
                sessions.append({
                    "id": session.id,
                    "created": session.created.isoformat(),
                    "updated": session.updated.isoformat(),
                    "mode": session.mode,
                    "topic": topic,
                })
            except Exception:
                # Skip corrupted sessions
                continue
        return sorted(sessions, key=lambda x: x["updated"], reverse=True)

    def exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return self.backend.session_exists(session_id)

    # =========================================================================
    # Session Updates
    # =========================================================================

    def update_journey_brief(
        self, session_id: str, brief: JourneyDesignBrief
    ) -> Session:
        """Update the journey brief for a session."""
        session = self.get(session_id)
        session.journey_brief = brief
        return self.save(session)

    def update_mode(self, session_id: str, mode: Mode) -> Session:
        """Update the mode for a session."""
        session = self.get(session_id)
        session.mode = mode

        # Initialize mode data if not present
        if mode == "research" and not session.research_data:
            session.research_data = ResearchModeData()
        elif mode == "understand" and not session.understand_data:
            session.understand_data = UnderstandModeData()
        elif mode == "build" and not session.build_data:
            session.build_data = BuildModeData()
            if not session.phase:
                session.phase = "grounding"

        return self.save(session)

    def update_phase(self, session_id: str, phase: BuildPhase) -> Session:
        """Update the build phase for a session."""
        session = self.get(session_id)
        session.phase = phase
        return self.save(session)

    def update_mode_data(
        self,
        session_id: str,
        data: ResearchModeData | UnderstandModeData | BuildModeData,
    ) -> Session:
        """Update the mode-specific data for a session."""
        session = self.get(session_id)

        if isinstance(data, ResearchModeData):
            session.research_data = data
        elif isinstance(data, UnderstandModeData):
            session.understand_data = data
        elif isinstance(data, BuildModeData):
            session.build_data = data

        return self.save(session)

    def update_agent_state(self, session_id: str, state: AgentState) -> Session:
        """Update the agent state for a session."""
        session = self.get(session_id)
        session.agent_state = state
        return self.save(session)

    def add_grounding_concept(
        self, session_id: str, concept: GroundingConcept
    ) -> Session:
        """Add a grounding concept to a build session."""
        session = self.get(session_id)
        session.grounding_concepts.append(concept)
        return self.save(session)

    def mark_grounding_ready(self, session_id: str) -> Session:
        """Mark grounding as complete, transition to making phase."""
        session = self.get(session_id)
        session.grounding_ready = True
        session.phase = "making"
        return self.save(session)

    # =========================================================================
    # Internal
    # =========================================================================

    def _save(self, session: Session) -> None:
        """Save session to backend."""
        self.backend.write_session(
            session.id,
            session.model_dump(mode="json", by_alias=True),
        )
