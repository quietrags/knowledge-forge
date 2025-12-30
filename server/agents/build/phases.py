"""
Build Agent Phases and Transitions.

Defines the phase graph for the Constructivist tutoring system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Literal

from server.agents.base import BasePhaseContext, PhaseTransition


class BuildPhase(Enum):
    """Phases for the Build agent."""

    # Phase 0: Anchor Discovery [PLAN]
    ANCHOR_DISCOVERY = "anchor_discovery"

    # Phase 1: Topic Classification + MLO Breakdown [PLAN]
    CLASSIFY = "classify"

    # Phase 2: Construction Sequence Design [PLAN]
    SEQUENCE_DESIGN = "sequence_design"

    # Phase 3: Construction Loop [REACT]
    CONSTRUCTION = "construction"

    # Phase 4: SLO Completion
    SLO_COMPLETE = "slo_complete"

    # Phase 5: Session Consolidation [REFLECT]
    CONSOLIDATION = "consolidation"

    # Phase 6: Artifact Generation [MEMORY]
    COMPLETE = "complete"


# =============================================================================
# Phase Transitions
# =============================================================================

BUILD_TRANSITIONS: list[PhaseTransition] = [
    # Forward transitions
    PhaseTransition(
        from_phase=BuildPhase.ANCHOR_DISCOVERY,
        to_phase=BuildPhase.CLASSIFY,
        condition="anchors_confirmed",
    ),
    PhaseTransition(
        from_phase=BuildPhase.CLASSIFY,
        to_phase=BuildPhase.SEQUENCE_DESIGN,
        condition="slos_selected",
    ),
    PhaseTransition(
        from_phase=BuildPhase.SEQUENCE_DESIGN,
        to_phase=BuildPhase.CONSTRUCTION,
        condition="sequence_designed",
    ),
    PhaseTransition(
        from_phase=BuildPhase.CONSTRUCTION,
        to_phase=BuildPhase.SLO_COMPLETE,
        condition="construction_verified",
    ),
    # SLO_COMPLETE can go back to construction for next SLO or forward to consolidation
    PhaseTransition(
        from_phase=BuildPhase.SLO_COMPLETE,
        to_phase=BuildPhase.CONSTRUCTION,
        condition="next_slo_available",
        is_backward=True,
    ),
    PhaseTransition(
        from_phase=BuildPhase.SLO_COMPLETE,
        to_phase=BuildPhase.CONSOLIDATION,
        condition="all_slos_complete",
    ),
    PhaseTransition(
        from_phase=BuildPhase.CONSOLIDATION,
        to_phase=BuildPhase.COMPLETE,
        condition="consolidation_complete",
    ),

    # Backward transitions for surrender recovery
    PhaseTransition(
        from_phase=BuildPhase.CONSTRUCTION,
        to_phase=BuildPhase.ANCHOR_DISCOVERY,
        condition="anchor_gap_detected",
        is_backward=True,
    ),
]


# =============================================================================
# Supporting Types
# =============================================================================

@dataclass
class Anchor:
    """An anchor point from learner's existing knowledge."""
    id: str
    description: str
    strength: Literal["strong", "medium", "weak"]
    evidence: str


@dataclass
class ConstructionSLO:
    """A Build-mode SLO focused on construction."""
    id: str
    statement: str
    frame: Literal["BUILD", "CONNECT", "TRANSFER", "DISTINGUISH", "DEBUG"]
    anchor_id: str  # Which anchor connects to this SLO
    in_scope: list[str]
    out_of_scope: list[str]
    code_mode_likely: bool = False
    estimated_rounds: int = 5


@dataclass
class ConstructionRound:
    """Record of a single construction round."""
    round_num: int
    scaffold_type: Literal["question", "scenario", "code", "partial_answer"]
    scaffold_content: str
    learner_response: str
    outcome: Literal["constructed", "partial", "stuck", "surrendered", "unexpected"]
    notes: str = ""


# =============================================================================
# Phase Context
# =============================================================================

@dataclass
class BuildPhaseContext(BasePhaseContext):
    """
    Context for the Build agent that persists across phases.

    Tracks:
    - Discovered anchors and anchor map
    - SLOs and construction sequences
    - Construction state per SLO
    - Surrender patterns and effective strategies
    - Memory layers
    """

    # Phase 0: Anchor Discovery
    anchors: list[Anchor] = field(default_factory=list)
    primary_anchor_id: Optional[str] = None
    anchor_questions_asked: bool = False  # Track if we've asked anchor questions
    anchors_confirmed: bool = False

    # Phase 1: Classification and SLOs
    topic_type: str = "ATOMIC"  # ATOMIC, COMPOSITE, SYSTEM, FIELD
    slos: list[ConstructionSLO] = field(default_factory=list)
    selected_slo_ids: list[str] = field(default_factory=list)
    slos_presented: bool = False  # Track if we've presented SLOs to user
    slos_confirmed: bool = False

    # Phase 2: Sequence Design
    construction_sequences: dict[str, dict] = field(default_factory=dict)  # slo_id -> sequence
    sequences_designed: bool = False

    # Phase 3: Construction Loop State
    current_slo_index: int = 0
    current_scaffold_level: str = "medium"  # heavy, medium, light, none
    current_mode: str = "normal"  # normal, surrender_recovery, code
    construction_rounds: dict[str, list[ConstructionRound]] = field(default_factory=dict)  # slo_id -> rounds

    # Per-SLO construction status
    slo_status: dict[str, str] = field(default_factory=dict)  # slo_id -> constructed/partial/not_started

    # Surrender tracking
    consecutive_surrenders: int = 0
    effective_strategies: list[str] = field(default_factory=list)

    # Phase 4: Completion tracking
    completed_slo_ids: list[str] = field(default_factory=list)
    skipped_slo_ids: list[str] = field(default_factory=list)

    # Phase 5: Consolidation
    consolidation_complete: bool = False
    session_insights: list[str] = field(default_factory=list)

    # ==========================================================================
    # Anchor Management
    # ==========================================================================

    def add_anchor(self, anchor: Anchor) -> None:
        """Add an anchor to the list."""
        self.anchors.append(anchor)

    def get_anchor(self, anchor_id: str) -> Optional[Anchor]:
        """Get an anchor by ID."""
        return next((a for a in self.anchors if a.id == anchor_id), None)

    def get_strong_anchors(self) -> list[Anchor]:
        """Get all strong anchors."""
        return [a for a in self.anchors if a.strength == "strong"]

    # ==========================================================================
    # SLO Management
    # ==========================================================================

    def add_slo(self, slo: ConstructionSLO) -> None:
        """Add a construction SLO."""
        self.slos.append(slo)
        self.slo_status[slo.id] = "not_started"
        self.construction_rounds[slo.id] = []

    def get_current_slo(self) -> Optional[ConstructionSLO]:
        """Get the currently active SLO."""
        if not self.selected_slo_ids:
            return None
        if self.current_slo_index >= len(self.selected_slo_ids):
            return None
        slo_id = self.selected_slo_ids[self.current_slo_index]
        return next((s for s in self.slos if s.id == slo_id), None)

    def get_current_rounds(self) -> list[ConstructionRound]:
        """Get construction rounds for current SLO."""
        slo = self.get_current_slo()
        if slo:
            return self.construction_rounds.get(slo.id, [])
        return []

    def add_construction_round(self, round_data: ConstructionRound) -> None:
        """Add a construction round for current SLO."""
        slo = self.get_current_slo()
        if slo:
            if slo.id not in self.construction_rounds:
                self.construction_rounds[slo.id] = []
            self.construction_rounds[slo.id].append(round_data)

    # ==========================================================================
    # Scaffold and Mode Management
    # ==========================================================================

    def increase_scaffold(self) -> None:
        """Increase scaffold level (make heavier)."""
        levels = ["none", "light", "medium", "heavy"]
        current_idx = levels.index(self.current_scaffold_level)
        if current_idx < len(levels) - 1:
            self.current_scaffold_level = levels[current_idx + 1]

    def decrease_scaffold(self) -> None:
        """Decrease scaffold level (make lighter)."""
        levels = ["none", "light", "medium", "heavy"]
        current_idx = levels.index(self.current_scaffold_level)
        if current_idx > 0:
            self.current_scaffold_level = levels[current_idx - 1]

    def enter_surrender_recovery(self) -> None:
        """Enter surrender recovery mode."""
        self.current_mode = "surrender_recovery"
        self.consecutive_surrenders += 1

    def enter_code_mode(self) -> None:
        """Enter code mode."""
        self.current_mode = "code"

    def exit_special_mode(self) -> None:
        """Exit to normal mode."""
        self.current_mode = "normal"
        self.consecutive_surrenders = 0

    # ==========================================================================
    # Transition Conditions
    # ==========================================================================

    def is_construction_verified(self) -> bool:
        """Check if current SLO construction is verified."""
        slo = self.get_current_slo()
        if slo:
            return self.slo_status.get(slo.id) == "constructed"
        return False

    def has_next_slo(self) -> bool:
        """Check if there's another SLO to work on."""
        remaining = set(self.selected_slo_ids) - set(self.completed_slo_ids) - set(self.skipped_slo_ids)
        return len(remaining) > 0

    def advance_to_next_slo(self) -> bool:
        """Move to the next SLO. Returns True if successful."""
        current = self.get_current_slo()
        if current and current.id not in self.completed_slo_ids:
            self.completed_slo_ids.append(current.id)

        # Find next uncompleted SLO
        for i, slo_id in enumerate(self.selected_slo_ids):
            if slo_id not in self.completed_slo_ids and slo_id not in self.skipped_slo_ids:
                self.current_slo_index = i
                self.current_scaffold_level = "medium"
                self.current_mode = "normal"
                self.consecutive_surrenders = 0
                return True

        return False

    def mark_current_constructed(self) -> None:
        """Mark current SLO as constructed."""
        slo = self.get_current_slo()
        if slo:
            self.slo_status[slo.id] = "constructed"

    def mark_current_partial(self) -> None:
        """Mark current SLO as partial."""
        slo = self.get_current_slo()
        if slo:
            self.slo_status[slo.id] = "partial"

    # ==========================================================================
    # Serialization
    # ==========================================================================

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "phase_visits": self.phase_visits,
            "backward_trigger": self.backward_trigger,
            "backward_trigger_detail": self.backward_trigger_detail,
            # Phase 0
            "anchors": [
                {"id": a.id, "description": a.description, "strength": a.strength, "evidence": a.evidence}
                for a in self.anchors
            ],
            "primary_anchor_id": self.primary_anchor_id,
            "anchor_questions_asked": self.anchor_questions_asked,
            "anchors_confirmed": self.anchors_confirmed,
            # Phase 1
            "topic_type": self.topic_type,
            "slos": [
                {
                    "id": s.id, "statement": s.statement, "frame": s.frame,
                    "anchor_id": s.anchor_id, "in_scope": s.in_scope,
                    "out_of_scope": s.out_of_scope, "code_mode_likely": s.code_mode_likely,
                    "estimated_rounds": s.estimated_rounds,
                }
                for s in self.slos
            ],
            "selected_slo_ids": self.selected_slo_ids,
            "slos_presented": self.slos_presented,
            "slos_confirmed": self.slos_confirmed,
            # Phase 2
            "construction_sequences": self.construction_sequences,
            "sequences_designed": self.sequences_designed,
            # Phase 3
            "current_slo_index": self.current_slo_index,
            "current_scaffold_level": self.current_scaffold_level,
            "current_mode": self.current_mode,
            "construction_rounds": {
                slo_id: [
                    {
                        "round_num": r.round_num, "scaffold_type": r.scaffold_type,
                        "scaffold_content": r.scaffold_content, "learner_response": r.learner_response,
                        "outcome": r.outcome, "notes": r.notes,
                    }
                    for r in rounds
                ]
                for slo_id, rounds in self.construction_rounds.items()
            },
            "slo_status": self.slo_status,
            "consecutive_surrenders": self.consecutive_surrenders,
            "effective_strategies": self.effective_strategies,
            # Phase 4
            "completed_slo_ids": self.completed_slo_ids,
            "skipped_slo_ids": self.skipped_slo_ids,
            # Phase 5
            "consolidation_complete": self.consolidation_complete,
            "session_insights": self.session_insights,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BuildPhaseContext":
        """Deserialize from dictionary."""
        ctx = cls()
        ctx.phase_visits = data.get("phase_visits", {})
        ctx.backward_trigger = data.get("backward_trigger")
        ctx.backward_trigger_detail = data.get("backward_trigger_detail")
        # Phase 0
        ctx.anchors = [Anchor(**a) for a in data.get("anchors", [])]
        ctx.primary_anchor_id = data.get("primary_anchor_id")
        ctx.anchor_questions_asked = data.get("anchor_questions_asked", False)
        ctx.anchors_confirmed = data.get("anchors_confirmed", False)
        # Phase 1
        ctx.topic_type = data.get("topic_type", "ATOMIC")
        ctx.slos = [ConstructionSLO(**s) for s in data.get("slos", [])]
        ctx.selected_slo_ids = data.get("selected_slo_ids", [])
        ctx.slos_presented = data.get("slos_presented", False)
        ctx.slos_confirmed = data.get("slos_confirmed", False)
        # Phase 2
        ctx.construction_sequences = data.get("construction_sequences", {})
        ctx.sequences_designed = data.get("sequences_designed", False)
        # Phase 3
        ctx.current_slo_index = data.get("current_slo_index", 0)
        ctx.current_scaffold_level = data.get("current_scaffold_level", "medium")
        ctx.current_mode = data.get("current_mode", "normal")
        ctx.construction_rounds = {
            slo_id: [ConstructionRound(**r) for r in rounds]
            for slo_id, rounds in data.get("construction_rounds", {}).items()
        }
        ctx.slo_status = data.get("slo_status", {})
        ctx.consecutive_surrenders = data.get("consecutive_surrenders", 0)
        ctx.effective_strategies = data.get("effective_strategies", [])
        # Phase 4
        ctx.completed_slo_ids = data.get("completed_slo_ids", [])
        ctx.skipped_slo_ids = data.get("skipped_slo_ids", [])
        # Phase 5
        ctx.consolidation_complete = data.get("consolidation_complete", False)
        ctx.session_insights = data.get("session_insights", [])
        return ctx
