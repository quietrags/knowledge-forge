"""
Understand Agent Phases and Transitions.

Defines the phase graph for the Socratic tutoring system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from server.agents.base import BasePhaseContext, PhaseTransition
from server.persistence import SLO, KnowledgeStateFacet


class UnderstandPhase(Enum):
    """Phases for the Understand agent."""

    # Stage 0: Knowledge Self-Assessment
    SELF_ASSESS = "self_assess"

    # Stage 0.5: Session Configuration
    CONFIGURE = "configure"

    # Stage 1: Topic Classification and MLO Generation
    CLASSIFY = "classify"

    # Stage 2: Triple Calibration (per SLO)
    CALIBRATE = "calibrate"

    # Stage 3: Diagnostic Loop (per SLO)
    DIAGNOSE = "diagnose"

    # Stage 4: SLO Completion and Transition
    SLO_COMPLETE = "slo_complete"

    # Stage 5: Session Completion
    COMPLETE = "complete"


# =============================================================================
# Phase Transitions
# =============================================================================

UNDERSTAND_TRANSITIONS: list[PhaseTransition] = [
    # Forward transitions
    PhaseTransition(
        from_phase=UnderstandPhase.SELF_ASSESS,
        to_phase=UnderstandPhase.CONFIGURE,
        condition="knowledge_confidence_established",
    ),
    PhaseTransition(
        from_phase=UnderstandPhase.CONFIGURE,
        to_phase=UnderstandPhase.CLASSIFY,
        condition="session_preferences_set",
    ),
    PhaseTransition(
        from_phase=UnderstandPhase.CLASSIFY,
        to_phase=UnderstandPhase.CALIBRATE,
        condition="slos_selected",
    ),
    PhaseTransition(
        from_phase=UnderstandPhase.CALIBRATE,
        to_phase=UnderstandPhase.DIAGNOSE,
        condition="calibration_complete",
    ),
    PhaseTransition(
        from_phase=UnderstandPhase.DIAGNOSE,
        to_phase=UnderstandPhase.SLO_COMPLETE,
        condition="mastery_criteria_met",
    ),
    PhaseTransition(
        from_phase=UnderstandPhase.SLO_COMPLETE,
        to_phase=UnderstandPhase.CALIBRATE,
        condition="next_slo_available",
        is_backward=True,
    ),
    PhaseTransition(
        from_phase=UnderstandPhase.SLO_COMPLETE,
        to_phase=UnderstandPhase.COMPLETE,
        condition="all_slos_complete",
    ),

    # Backward transitions
    PhaseTransition(
        from_phase=UnderstandPhase.DIAGNOSE,
        to_phase=UnderstandPhase.CALIBRATE,
        condition="slo_skipped_needs_recalibration",
        is_backward=True,
    ),
]


# =============================================================================
# Phase Context
# =============================================================================

@dataclass
class UnderstandPhaseContext(BasePhaseContext):
    """
    Context for the Understand agent that persists across phases.

    Tracks:
    - Session preferences (pace, style, learner context)
    - Generated SLOs and their state
    - Knowledge state map per SLO
    - Mastery counters per SLO
    """

    # Stage 0: Knowledge confidence
    knowledge_confidence: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    topic_brief: Optional[dict] = None
    aspects_to_skip: list[str] = field(default_factory=list)

    # Stage 0.5: Session preferences
    pace: str = "standard"  # standard, thorough, focused
    style: str = "balanced"  # balanced, example-heavy, theory-first, visual
    learner_context: str = ""
    config_questions_asked: bool = False  # Track if we've asked config questions
    session_configured: bool = False

    # Stage 1: Topic classification and SLOs
    topic_type: str = "ATOMIC"  # ATOMIC, COMPOSITE, SYSTEM, FIELD
    slos: list[SLO] = field(default_factory=list)
    selected_slo_ids: list[str] = field(default_factory=list)
    slos_presented: bool = False  # Track if we've presented SLOs to user
    slos_confirmed: bool = False

    # Stage 2-4: Current SLO tracking
    current_slo_index: int = 0
    current_slo_calibrated: bool = False

    # Calibration probe tracking (per SLO, keyed by slo_id)
    # Each entry is a dict with: {"feynman": "strong/partial/weak", "minimal_example": ..., "boundary": ...}
    calibration_probe_results: dict[str, dict[str, str]] = field(default_factory=dict)

    # Per-SLO mastery counters (keyed by slo_id)
    slo_counters: dict[str, dict] = field(default_factory=dict)

    # Per-SLO knowledge state maps (keyed by slo_id)
    knowledge_states: dict[str, dict[str, KnowledgeStateFacet]] = field(default_factory=dict)

    # Stage 4: SLO completion tracking
    completed_slo_ids: list[str] = field(default_factory=list)
    skipped_slo_ids: list[str] = field(default_factory=list)

    # ==========================================================================
    # SLO Management
    # ==========================================================================

    def add_slo(self, slo: SLO) -> None:
        """Add an SLO to the list."""
        self.slos.append(slo)
        # Initialize counters for this SLO
        self.slo_counters[slo.id] = {
            "total_rounds": 0,
            "consecutive_passes": 0,
            "transfer_passes": 0,
            "facet_rounds": {
                "vocabulary": 0,
                "mental_model": 0,
                "practical_grasp": 0,
                "boundary_conditions": 0,
                "transfer": 0,
            },
        }
        # Initialize knowledge state for this SLO
        self.knowledge_states[slo.id] = {
            "vocabulary": KnowledgeStateFacet(facet="vocabulary", status="not_tested"),
            "mental_model": KnowledgeStateFacet(facet="mental_model", status="not_tested"),
            "practical_grasp": KnowledgeStateFacet(facet="practical_grasp", status="not_tested"),
            "boundary_conditions": KnowledgeStateFacet(facet="boundary_conditions", status="not_tested"),
            "transfer": KnowledgeStateFacet(facet="transfer", status="not_tested"),
        }

    def get_current_slo(self) -> Optional[SLO]:
        """Get the currently active SLO."""
        if not self.selected_slo_ids:
            return None
        if self.current_slo_index >= len(self.selected_slo_ids):
            return None
        slo_id = self.selected_slo_ids[self.current_slo_index]
        return next((s for s in self.slos if s.id == slo_id), None)

    def get_current_counters(self) -> Optional[dict]:
        """Get counters for current SLO."""
        slo = self.get_current_slo()
        if slo:
            return self.slo_counters.get(slo.id)
        return None

    def get_current_probe_results(self) -> dict[str, str]:
        """Get calibration probe results for current SLO."""
        slo = self.get_current_slo()
        if slo:
            return self.calibration_probe_results.get(slo.id, {})
        return {}

    def record_probe_result(self, probe_type: str, result: str) -> None:
        """Record a calibration probe result for current SLO."""
        slo = self.get_current_slo()
        if slo:
            if slo.id not in self.calibration_probe_results:
                self.calibration_probe_results[slo.id] = {}
            self.calibration_probe_results[slo.id][probe_type] = result

    def get_remaining_probes(self) -> list[str]:
        """Get list of probes not yet completed for current SLO."""
        all_probes = ["feynman", "minimal_example", "boundary"]
        completed = set(self.get_current_probe_results().keys())
        return [p for p in all_probes if p not in completed]

    def is_calibration_probes_complete(self) -> bool:
        """Check if all calibration probes are done for current SLO."""
        return len(self.get_remaining_probes()) == 0

    def get_current_knowledge_state(self) -> Optional[dict[str, KnowledgeStateFacet]]:
        """Get knowledge state for current SLO."""
        slo = self.get_current_slo()
        if slo:
            return self.knowledge_states.get(slo.id)
        return None

    def increment_round(self, facet: str) -> None:
        """Increment round counter for current SLO."""
        counters = self.get_current_counters()
        if counters:
            counters["total_rounds"] += 1
            counters["facet_rounds"][facet] = counters["facet_rounds"].get(facet, 0) + 1

    def record_pass(self, is_transfer: bool = False) -> None:
        """Record a pass for current SLO."""
        counters = self.get_current_counters()
        if counters:
            counters["consecutive_passes"] += 1
            if is_transfer:
                counters["transfer_passes"] += 1

    def record_fail(self) -> None:
        """Record a fail for current SLO (resets consecutive passes)."""
        counters = self.get_current_counters()
        if counters:
            counters["consecutive_passes"] = 0

    def update_facet_status(
        self,
        facet: str,
        status: str,
        evidence: str,
    ) -> None:
        """Update knowledge state for a facet."""
        state = self.get_current_knowledge_state()
        if state and facet in state:
            state[facet].status = status
            state[facet].evidence = evidence

    # ==========================================================================
    # Transition Conditions
    # ==========================================================================

    def is_mastery_criteria_met(self) -> bool:
        """Check if current SLO meets mastery criteria."""
        counters = self.get_current_counters()
        state = self.get_current_knowledge_state()

        if not counters or not state:
            return False

        # Minimum 7 rounds
        if counters["total_rounds"] < 7:
            return False

        # At least 2 rounds per facet (excluding transfer)
        for facet in ["vocabulary", "mental_model", "practical_grasp", "boundary_conditions"]:
            if counters["facet_rounds"].get(facet, 0) < 2:
                return False

        # 3+ consecutive passes
        if counters["consecutive_passes"] < 3:
            return False

        # 2+ transfer passes
        if counters["transfer_passes"] < 2:
            return False

        # No facet is "missing"
        for facet_state in state.values():
            if facet_state.status == "missing":
                return False

        return True

    def has_next_slo(self) -> bool:
        """Check if there's another SLO to work on."""
        remaining = set(self.selected_slo_ids) - set(self.completed_slo_ids) - set(self.skipped_slo_ids)
        return len(remaining) > 0

    def advance_to_next_slo(self) -> bool:
        """Move to the next SLO. Returns True if successful."""
        # Mark current SLO as complete
        current = self.get_current_slo()
        if current and current.id not in self.completed_slo_ids:
            self.completed_slo_ids.append(current.id)

        # Find next uncompleted SLO
        for i, slo_id in enumerate(self.selected_slo_ids):
            if slo_id not in self.completed_slo_ids and slo_id not in self.skipped_slo_ids:
                self.current_slo_index = i
                self.current_slo_calibrated = False
                return True

        return False

    def skip_current_slo(self) -> None:
        """Skip the current SLO."""
        current = self.get_current_slo()
        if current:
            self.skipped_slo_ids.append(current.id)

    # ==========================================================================
    # Serialization
    # ==========================================================================

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "phase_visits": self.phase_visits,
            "backward_trigger": self.backward_trigger,
            "backward_trigger_detail": self.backward_trigger_detail,
            # Stage 0
            "knowledge_confidence": self.knowledge_confidence,
            "topic_brief": self.topic_brief,
            "aspects_to_skip": self.aspects_to_skip,
            # Stage 0.5
            "pace": self.pace,
            "style": self.style,
            "learner_context": self.learner_context,
            "config_questions_asked": self.config_questions_asked,
            "session_configured": self.session_configured,
            # Stage 1
            "topic_type": self.topic_type,
            "slos": [s.model_dump(by_alias=True) for s in self.slos],
            "selected_slo_ids": self.selected_slo_ids,
            "slos_presented": self.slos_presented,
            "slos_confirmed": self.slos_confirmed,
            # Stage 2-4
            "current_slo_index": self.current_slo_index,
            "current_slo_calibrated": self.current_slo_calibrated,
            "calibration_probe_results": self.calibration_probe_results,
            "slo_counters": self.slo_counters,
            "knowledge_states": {
                slo_id: {
                    facet: state.model_dump(by_alias=True)
                    for facet, state in states.items()
                }
                for slo_id, states in self.knowledge_states.items()
            },
            "completed_slo_ids": self.completed_slo_ids,
            "skipped_slo_ids": self.skipped_slo_ids,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UnderstandPhaseContext":
        """Deserialize from dictionary."""
        ctx = cls()
        ctx.phase_visits = data.get("phase_visits", {})
        ctx.backward_trigger = data.get("backward_trigger")
        ctx.backward_trigger_detail = data.get("backward_trigger_detail")
        # Stage 0
        ctx.knowledge_confidence = data.get("knowledge_confidence", "MEDIUM")
        ctx.topic_brief = data.get("topic_brief")
        ctx.aspects_to_skip = data.get("aspects_to_skip", [])
        # Stage 0.5
        ctx.pace = data.get("pace", "standard")
        ctx.style = data.get("style", "balanced")
        ctx.learner_context = data.get("learner_context", "")
        ctx.config_questions_asked = data.get("config_questions_asked", False)
        ctx.session_configured = data.get("session_configured", False)
        # Stage 1
        ctx.topic_type = data.get("topic_type", "ATOMIC")
        ctx.slos = [SLO(**s) for s in data.get("slos", [])]
        ctx.selected_slo_ids = data.get("selected_slo_ids", [])
        ctx.slos_presented = data.get("slos_presented", False)
        ctx.slos_confirmed = data.get("slos_confirmed", False)
        # Stage 2-4
        ctx.current_slo_index = data.get("current_slo_index", 0)
        ctx.current_slo_calibrated = data.get("current_slo_calibrated", False)
        ctx.calibration_probe_results = data.get("calibration_probe_results", {})
        ctx.slo_counters = data.get("slo_counters", {})
        ctx.knowledge_states = {
            slo_id: {
                facet: KnowledgeStateFacet(**state)
                for facet, state in states.items()
            }
            for slo_id, states in data.get("knowledge_states", {}).items()
        }
        ctx.completed_slo_ids = data.get("completed_slo_ids", [])
        ctx.skipped_slo_ids = data.get("skipped_slo_ids", [])
        return ctx
