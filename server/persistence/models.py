"""
Pydantic models for session persistence.
These mirror the TypeScript types in the frontend.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
import uuid


# =============================================================================
# Enums / Literals
# =============================================================================

Mode = Literal["build", "understand", "research"]
AnswerType = Literal["facts", "understanding", "skill"]
BuildPhase = Literal["grounding", "making"]
QuestionStatus = Literal["open", "investigating", "answered"]


# =============================================================================
# Journey Design Brief
# =============================================================================

class JourneyDesignBrief(BaseModel):
    """The result of analyzing a user's question and designing their journey."""
    original_question: str
    ideal_answer: str
    answer_type: AnswerType
    primary_mode: Mode
    secondary_mode: Optional[Literal["research"]] = None
    implicit_question: Optional[str] = None
    confirmation_message: str


# =============================================================================
# Shared Content Types
# =============================================================================

class Source(BaseModel):
    """A research source with credibility info."""
    title: str
    url: str
    credibility: Literal["primary", "high", "medium", "low"]
    snippet: Optional[str] = None


class CodeContent(BaseModel):
    """Code displayed in the code panel."""
    file: str
    content: str
    language: Optional[str] = None


class CanvasContent(BaseModel):
    """Content for the canvas panel."""
    summary: Optional[str] = None
    diagram: Optional[str] = None


class Narrative(BaseModel):
    """The evolving knowledge narrative."""
    prior: str = ""
    delta: str = ""
    full: str = ""


class PathNode(BaseModel):
    """A node in the learning path."""
    id: str
    name: str
    status: Literal["solid", "partial", "frontier"]


class PathData(BaseModel):
    """Learning path visualization data."""
    nodes: list[PathNode] = []
    neighbors: list[str] = []


# =============================================================================
# Research Mode Data
# =============================================================================

class Question(BaseModel):
    """A research question."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    status: QuestionStatus = "open"
    answer: Optional[str] = None
    sources: list[Source] = []
    category_id: Optional[str] = None
    code: Optional[CodeContent] = None
    canvas: Optional[CanvasContent] = None


class CategoryQuestion(BaseModel):
    """A category grouping related questions."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    insight: Optional[str] = None
    question_ids: list[str] = []


class KeyInsight(BaseModel):
    """A key insight from research."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    relevance: str = ""


class AdjacentQuestion(BaseModel):
    """An adjacent/frontier question discovered during research."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    discovered_from: str


class ResearchModeData(BaseModel):
    """Complete research mode state."""
    topic: str = ""
    meta: str = ""
    essay: Narrative = Field(default_factory=Narrative)
    categories: list[CategoryQuestion] = []
    questions: list[Question] = []
    key_insights: list[KeyInsight] = []
    adjacent_questions: list[AdjacentQuestion] = []


# =============================================================================
# Understand Mode Data
# =============================================================================

class Assumption(BaseModel):
    """An assumption to surface and examine."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assumption: str
    surfaced: str
    status: Literal["active", "discarded"] = "active"


class Concept(BaseModel):
    """A concept that emerges from understanding."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    definition: str
    distinguished_from: Optional[str] = None
    is_threshold: bool = False
    from_assumption_id: Optional[str] = None


class Model(BaseModel):
    """A mental model integrating concepts."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    concept_ids: list[str] = []
    visualization: Optional[str] = None


class UnderstandModeData(BaseModel):
    """Complete understand mode state."""
    essay: Narrative = Field(default_factory=Narrative)
    assumptions: list[Assumption] = []
    concepts: list[Concept] = []
    models: list[Model] = []


# =============================================================================
# Build Mode Data
# =============================================================================

class GroundingConcept(BaseModel):
    """A concept grasped during grounding phase."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    distinction: str
    sufficient: bool = False


class Construct(BaseModel):
    """A building block construct."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    usage: str = ""
    code: Optional[str] = None


class Decision(BaseModel):
    """A trade-off decision."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    choice: str
    alternative: str
    rationale: str = ""
    construct_ids: list[str] = []
    produces_id: Optional[str] = None


class Capability(BaseModel):
    """A capability enabled by constructs/decisions."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    capability: str
    enabled_by: list[str] = []


class BuildModeData(BaseModel):
    """Complete build mode state."""
    narrative: Narrative = Field(default_factory=Narrative)
    constructs: list[Construct] = []
    decisions: list[Decision] = []
    capabilities: list[Capability] = []


# =============================================================================
# Agent State (for persistence)
# =============================================================================

class AgentState(BaseModel):
    """Agent-specific state for persistence across sessions."""
    anchor_map: dict = {}
    slo_progress: list[dict] = []
    memory_layers: dict = {}
    knowledge_state: dict = {}
    counters: dict = {}


# =============================================================================
# Session (Top-Level)
# =============================================================================

class Session(BaseModel):
    """Complete session state for persistence."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created: datetime = Field(default_factory=datetime.utcnow)
    updated: datetime = Field(default_factory=datetime.utcnow)

    # Journey
    journey_brief: Optional[JourneyDesignBrief] = None

    # Current state
    mode: Mode = "research"
    phase: Optional[BuildPhase] = None

    # Mode-specific data (only one is active at a time)
    research_data: Optional[ResearchModeData] = None
    understand_data: Optional[UnderstandModeData] = None
    build_data: Optional[BuildModeData] = None

    # Grounding concepts for build mode
    grounding_concepts: list[GroundingConcept] = []
    grounding_ready: bool = False

    # Agent state for resumption
    agent_state: AgentState = Field(default_factory=AgentState)

    # Learning path
    path: PathData = Field(default_factory=PathData)

    def get_mode_data(self):
        """Get the active mode's data."""
        if self.mode == "research":
            return self.research_data
        elif self.mode == "understand":
            return self.understand_data
        elif self.mode == "build":
            return self.build_data
        return None

    def set_mode_data(self, data):
        """Set the active mode's data."""
        if self.mode == "research":
            self.research_data = data
        elif self.mode == "understand":
            self.understand_data = data
        elif self.mode == "build":
            self.build_data = data
