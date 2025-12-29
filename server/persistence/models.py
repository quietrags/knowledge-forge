"""
Pydantic models for session persistence.
These mirror the TypeScript types in the frontend.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
import uuid


# =============================================================================
# Base Model with camelCase serialization
# =============================================================================

class CamelModel(BaseModel):
    """Base model that serializes to camelCase for frontend compatibility."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,  # Accept both snake_case and camelCase on input
    )


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

class JourneyDesignBrief(CamelModel):
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

class Source(CamelModel):
    """A research source with credibility info."""
    title: str
    url: Optional[str] = None  # Made optional to match frontend
    credibility: Literal["primary", "high", "medium", "low"]
    snippet: Optional[str] = None


class CodeContent(CamelModel):
    """Code displayed in the code panel."""
    file: str
    content: str
    language: Optional[str] = None


class CanvasContent(CamelModel):
    """Content for the canvas panel."""
    summary: Optional[str] = None
    diagram: Optional[str] = None


class Narrative(CamelModel):
    """The evolving knowledge narrative."""
    prior: str = ""
    delta: str = ""
    full: str = ""


class PathNode(CamelModel):
    """A node in the learning path."""
    id: str
    name: str
    status: Literal["solid", "partial", "empty"]  # Changed from "frontier" to match frontend


class PathData(CamelModel):
    """Learning path visualization data."""
    nodes: list[PathNode] = []
    neighbors: list[str] = []


# =============================================================================
# Research Mode Data
# =============================================================================

class Question(CamelModel):
    """A research question."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    status: QuestionStatus = "open"
    answer: Optional[str] = None
    sources: list[Source] = []
    category_id: Optional[str] = None
    code: Optional[CodeContent] = None
    canvas: Optional[CanvasContent] = None


class CategoryQuestion(CamelModel):
    """A category grouping related questions."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    insight: Optional[str] = None
    question_ids: list[str] = []


class KeyInsight(CamelModel):
    """A key insight from research."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    relevance: str = ""


class AdjacentQuestion(CamelModel):
    """An adjacent/frontier question discovered during research."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    discovered_from: str


class ResearchModeData(CamelModel):
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

# SLO Frame types
SLOFrame = Literal["EXPLAIN", "DECIDE", "BUILD", "DEBUG", "COMPARE"]
FacetStatus = Literal["not_tested", "missing", "shaky", "solid"]


class SLO(CamelModel):
    """A Single Learning Objective for the Understand agent."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    statement: str  # One sentence, testable, bounded
    frame: SLOFrame  # EXPLAIN, DECIDE, BUILD, DEBUG, COMPARE
    in_scope: list[str] = []  # 1-2 bullets
    out_of_scope: list[str] = []  # 1-2 bullets
    sample_transfer_check: str = ""  # Question to verify mastery
    estimated_rounds: int = 4  # 2-4 for atomic, 4-7 for complex


class KnowledgeStateFacet(CamelModel):
    """Knowledge state for a single facet."""
    facet: str  # vocabulary, mental_model, practical_grasp, boundary_conditions, transfer
    status: FacetStatus = "not_tested"
    evidence: str = ""
    rounds: int = 0
    last_result: Optional[Literal["pass", "fail"]] = None


class Assumption(CamelModel):
    """An assumption to surface and examine."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assumption: str
    surfaced: str
    status: Literal["active", "discarded"] = "active"


class Concept(CamelModel):
    """A concept that emerges from understanding."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    definition: str
    distinguished_from: Optional[str] = None
    is_threshold: bool = False
    from_assumption_id: Optional[str] = None


class Model(CamelModel):
    """A mental model integrating concepts."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    concept_ids: list[str] = []
    visualization: Optional[str] = None


class UnderstandModeData(CamelModel):
    """Complete understand mode state."""
    essay: Narrative = Field(default_factory=Narrative)
    assumptions: list[Assumption] = []
    concepts: list[Concept] = []
    models: list[Model] = []


# =============================================================================
# Build Mode Data
# =============================================================================

class GroundingConcept(CamelModel):
    """A concept grasped during grounding phase."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    distinction: str
    sufficient: bool = False


class Construct(CamelModel):
    """A building block construct."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    usage: str = ""
    code: Optional[str] = None


class Decision(CamelModel):
    """A trade-off decision."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    choice: str
    alternative: str
    rationale: str = ""
    construct_ids: list[str] = []
    produces_id: Optional[str] = None


class Capability(CamelModel):
    """A capability enabled by constructs/decisions."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    capability: str
    enabled_by: list[str] = []


class BuildModeData(CamelModel):
    """Complete build mode state."""
    narrative: Narrative = Field(default_factory=Narrative)
    constructs: list[Construct] = []
    decisions: list[Decision] = []
    capabilities: list[Capability] = []


# =============================================================================
# Agent State (for persistence)
# =============================================================================

class AgentState(CamelModel):
    """Agent-specific state for persistence across sessions."""
    anchor_map: dict = {}
    slo_progress: list[dict] = []
    memory_layers: dict = {}
    knowledge_state: dict = {}
    counters: dict = {}


# =============================================================================
# Session (Top-Level)
# =============================================================================

class Session(CamelModel):
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
