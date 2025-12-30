"""
Research Agent Phases and Transitions.

Defines the phase graph for the research pipeline:
DECOMPOSE → ANSWER → RISE_ABOVE → EXPAND → COMPLETE

With backward transitions for:
- Discovery of new categories during answering
- Need for more answers during synthesis
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

from server.agents.base import BasePhaseContext, PhaseTransition
from server.persistence import (
    CategoryQuestion,
    Question,
    KeyInsight,
    AdjacentQuestion,
    Source,
)


# =============================================================================
# Research Phases
# =============================================================================

class ResearchPhase(Enum):
    """Phases of the research pipeline."""
    DECOMPOSE = "decompose"      # Break topic into question categories
    ANSWER = "answer"            # Research and answer each question
    RISE_ABOVE = "rise_above"    # Synthesize category insights
    EXPAND = "expand"            # Discover adjacent questions
    COMPLETE = "complete"        # Research complete


# =============================================================================
# Phase Transitions
# =============================================================================

RESEARCH_TRANSITIONS = [
    # Forward transitions
    PhaseTransition(
        from_phase=ResearchPhase.DECOMPOSE,
        to_phase=ResearchPhase.ANSWER,
        condition="question_tree_approved",
        is_backward=False,
        priority=0,
    ),
    PhaseTransition(
        from_phase=ResearchPhase.ANSWER,
        to_phase=ResearchPhase.RISE_ABOVE,
        condition="high_priority_questions_answered",
        is_backward=False,
        priority=0,
    ),
    PhaseTransition(
        from_phase=ResearchPhase.RISE_ABOVE,
        to_phase=ResearchPhase.EXPAND,
        condition="category_insights_generated",
        is_backward=False,
        priority=0,
    ),
    PhaseTransition(
        from_phase=ResearchPhase.EXPAND,
        to_phase=ResearchPhase.COMPLETE,
        condition="frontier_populated",
        is_backward=False,
        priority=0,
    ),

    # Backward transitions (checked first due to is_backward=True)
    PhaseTransition(
        from_phase=ResearchPhase.ANSWER,
        to_phase=ResearchPhase.DECOMPOSE,
        condition="new_category_discovered",
        is_backward=True,
        priority=10,
    ),
    PhaseTransition(
        from_phase=ResearchPhase.RISE_ABOVE,
        to_phase=ResearchPhase.ANSWER,
        condition="synthesis_requires_more_answers",
        is_backward=True,
        priority=10,
    ),
    PhaseTransition(
        from_phase=ResearchPhase.RISE_ABOVE,
        to_phase=ResearchPhase.DECOMPOSE,
        condition="synthesis_reveals_missing_category",
        is_backward=True,
        priority=5,
    ),
]


# =============================================================================
# Research Phase Context
# =============================================================================

@dataclass
class ResearchPhaseContext(BasePhaseContext):
    """
    State that persists across phase visits in Research mode.

    Accumulates work from each phase and enables intelligent
    re-entry behavior.
    """

    # DECOMPOSE phase state
    categories: list[CategoryQuestion] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    question_tree_presented: bool = False  # Track if question tree was shown to user
    question_tree_approved: bool = False

    # ANSWER phase state
    answered_question_ids: set[str] = field(default_factory=set)
    skipped_question_ids: set[str] = field(default_factory=set)
    sources_by_question: dict[str, list[Source]] = field(default_factory=dict)
    high_priority_complete: bool = False

    # RISE_ABOVE phase state
    category_insights: dict[str, str] = field(default_factory=dict)  # category_id -> insight
    insights_complete: bool = False

    # EXPAND phase state
    adjacent_questions: list[AdjacentQuestion] = field(default_factory=list)
    frontier_populated: bool = False

    # Flags for backward transitions
    new_category_pending: Optional[str] = None  # Category name to add
    unanswered_for_synthesis: list[str] = field(default_factory=list)  # Question IDs

    def add_category(self, category: CategoryQuestion) -> None:
        """Add a category to the context."""
        self.categories.append(category)

    def add_question(self, question: Question) -> None:
        """Add a question to the context."""
        self.questions.append(question)

    def mark_question_answered(self, question_id: str) -> None:
        """Mark a question as answered."""
        self.answered_question_ids.add(question_id)

    def get_unanswered_questions(self) -> list[Question]:
        """Get all unanswered questions."""
        return [
            q for q in self.questions
            if q.id not in self.answered_question_ids
            and q.id not in self.skipped_question_ids
        ]

    def get_questions_by_category(self, category_id: str) -> list[Question]:
        """Get all questions in a category."""
        return [q for q in self.questions if q.category_id == category_id]

    def should_trigger_backward_to_decompose(self) -> bool:
        """Check if we need to go back to DECOMPOSE."""
        return self.new_category_pending is not None

    def should_trigger_backward_to_answer(self) -> bool:
        """Check if we need to go back to ANSWER."""
        return len(self.unanswered_for_synthesis) > 0

    def clear_backward_triggers(self) -> None:
        """Clear backward transition triggers."""
        self.new_category_pending = None
        self.unanswered_for_synthesis = []

    def to_dict(self) -> dict:
        """Serialize to dictionary for persistence."""
        return {
            "phase_visits": self.phase_visits,
            "backward_trigger": self.backward_trigger,
            "backward_trigger_detail": self.backward_trigger_detail,
            "categories": [c.model_dump(by_alias=True) for c in self.categories],
            "questions": [q.model_dump(by_alias=True) for q in self.questions],
            "question_tree_presented": self.question_tree_presented,
            "question_tree_approved": self.question_tree_approved,
            "answered_question_ids": list(self.answered_question_ids),
            "skipped_question_ids": list(self.skipped_question_ids),
            "high_priority_complete": self.high_priority_complete,
            "category_insights": self.category_insights,
            "insights_complete": self.insights_complete,
            "adjacent_questions": [aq.model_dump(by_alias=True) for aq in self.adjacent_questions],
            "frontier_populated": self.frontier_populated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchPhaseContext":
        """Restore from dictionary."""
        ctx = cls()
        ctx.phase_visits = data.get("phase_visits", {})
        ctx.backward_trigger = data.get("backward_trigger")
        ctx.backward_trigger_detail = data.get("backward_trigger_detail")
        ctx.categories = [
            CategoryQuestion(**c) for c in data.get("categories", [])
        ]
        ctx.questions = [
            Question(**q) for q in data.get("questions", [])
        ]
        ctx.question_tree_presented = data.get("question_tree_presented", False)
        ctx.question_tree_approved = data.get("question_tree_approved", False)
        ctx.answered_question_ids = set(data.get("answered_question_ids", []))
        ctx.skipped_question_ids = set(data.get("skipped_question_ids", []))
        ctx.high_priority_complete = data.get("high_priority_complete", False)
        ctx.category_insights = data.get("category_insights", {})
        ctx.insights_complete = data.get("insights_complete", False)
        ctx.adjacent_questions = [
            AdjacentQuestion(**aq) for aq in data.get("adjacent_questions", [])
        ]
        ctx.frontier_populated = data.get("frontier_populated", False)
        return ctx
