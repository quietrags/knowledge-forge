"""
Persistence layer for Knowledge Forge sessions.

Usage:
    from server.persistence import SessionStore, Session

    store = SessionStore()
    session = store.create(mode="research")
    session = store.get(session_id)
    store.save(session)
"""

from .models import (
    # Core types
    Mode,
    AnswerType,
    BuildPhase,
    QuestionStatus,
    # Journey
    JourneyDesignBrief,
    # Shared
    Source,
    CodeContent,
    CanvasContent,
    Narrative,
    PathNode,
    PathData,
    # Research
    Question,
    CategoryQuestion,
    KeyInsight,
    AdjacentQuestion,
    ResearchModeData,
    # Understand
    SLOFrame,
    FacetStatus,
    SLO,
    KnowledgeStateFacet,
    Assumption,
    Concept,
    Model,
    UnderstandModeData,
    # Build
    GroundingConcept,
    Construct,
    Decision,
    Capability,
    BuildModeData,
    # Session
    AgentState,
    Session,
)

from .file_backend import FileBackend
from .session_store import SessionStore, SessionNotFoundError

__all__ = [
    # Core types
    "Mode",
    "AnswerType",
    "BuildPhase",
    "QuestionStatus",
    # Journey
    "JourneyDesignBrief",
    # Shared
    "Source",
    "CodeContent",
    "CanvasContent",
    "Narrative",
    "PathNode",
    "PathData",
    # Research
    "Question",
    "CategoryQuestion",
    "KeyInsight",
    "AdjacentQuestion",
    "ResearchModeData",
    # Understand
    "SLOFrame",
    "FacetStatus",
    "SLO",
    "KnowledgeStateFacet",
    "Assumption",
    "Concept",
    "Model",
    "UnderstandModeData",
    # Build
    "GroundingConcept",
    "Construct",
    "Decision",
    "Capability",
    "BuildModeData",
    # Session
    "AgentState",
    "Session",
    # Store
    "FileBackend",
    "SessionStore",
    "SessionNotFoundError",
]
