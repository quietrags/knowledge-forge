"""
Tests for the Understand Agent.

Tests cover:
- Phase progression (forward transitions)
- Backward transitions
- SLO management
- Knowledge state tracking
- Mastery criteria
- State persistence
"""

import pytest
from unittest.mock import AsyncMock

from server.agents.understand import (
    UnderstandAgent,
    UnderstandPhase,
    UnderstandPhaseContext,
)
from server.agents.understand.phases import UNDERSTAND_TRANSITIONS
from server.agents.base import PhaseTransition, CheckpointResponse
from server.persistence import (
    Session,
    JourneyDesignBrief,
    UnderstandModeData,
    SLO,
    KnowledgeStateFacet,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_session():
    """Create a mock session for testing."""
    session = Session(
        id="test-session-123",
        mode="understand",
        understand_data=UnderstandModeData(),
    )
    return session


@pytest.fixture
def mock_journey_brief():
    """Create a mock journey brief for testing."""
    return JourneyDesignBrief(
        original_question="How do database indexes work?",
        ideal_answer="A deep understanding of database indexing mechanisms",
        answer_type="understanding",
        primary_mode="understand",
        confirmation_message="Let's understand database indexes together",
    )


@pytest.fixture
def mock_emit():
    """Create a mock async event emitter."""
    return AsyncMock()


@pytest.fixture
def mock_checkpoint_handler():
    """Create a mock async checkpoint handler that auto-approves."""
    return AsyncMock(return_value=CheckpointResponse(approved=True))


@pytest.fixture
def understand_agent(mock_session, mock_emit, mock_checkpoint_handler):
    """Create an Understand Agent for testing."""
    return UnderstandAgent(
        session=mock_session,
        emit_event=mock_emit,
        checkpoint_handler=mock_checkpoint_handler,
    )


# =============================================================================
# Phase Transition Tests
# =============================================================================

class TestPhaseTransitions:
    """Tests for phase transition definitions."""

    def test_all_phases_have_forward_transition(self):
        """Every non-terminal phase should have at least one forward transition."""
        non_terminal_phases = [
            UnderstandPhase.SELF_ASSESS,
            UnderstandPhase.CONFIGURE,
            UnderstandPhase.CLASSIFY,
            UnderstandPhase.CALIBRATE,
            UnderstandPhase.DIAGNOSE,
            UnderstandPhase.SLO_COMPLETE,
        ]

        for phase in non_terminal_phases:
            forward_transitions = [
                t for t in UNDERSTAND_TRANSITIONS
                if t.from_phase == phase and not t.is_backward
            ]
            assert len(forward_transitions) >= 1, f"No forward transition from {phase}"

    def test_backward_transitions_exist(self):
        """Verify backward transitions are defined."""
        backward_transitions = [t for t in UNDERSTAND_TRANSITIONS if t.is_backward]
        assert len(backward_transitions) >= 1, "Should have at least 1 backward transition"

    def test_slo_complete_has_dual_paths(self):
        """SLO_COMPLETE should transition to CALIBRATE or COMPLETE."""
        slo_complete_transitions = [
            t for t in UNDERSTAND_TRANSITIONS
            if t.from_phase == UnderstandPhase.SLO_COMPLETE
        ]
        assert len(slo_complete_transitions) >= 2, "SLO_COMPLETE needs paths to CALIBRATE and COMPLETE"

        to_calibrate = any(t.to_phase == UnderstandPhase.CALIBRATE for t in slo_complete_transitions)
        to_complete = any(t.to_phase == UnderstandPhase.COMPLETE for t in slo_complete_transitions)
        assert to_calibrate and to_complete

    def test_complete_phase_has_no_transitions(self):
        """COMPLETE phase should have no outgoing transitions."""
        complete_transitions = [
            t for t in UNDERSTAND_TRANSITIONS
            if t.from_phase == UnderstandPhase.COMPLETE
        ]
        assert len(complete_transitions) == 0


# =============================================================================
# Phase Context Tests
# =============================================================================

class TestUnderstandPhaseContext:
    """Tests for UnderstandPhaseContext."""

    def test_initial_state(self):
        """Test initial context state."""
        ctx = UnderstandPhaseContext()

        assert ctx.knowledge_confidence == "MEDIUM"
        assert not ctx.session_configured
        assert len(ctx.slos) == 0
        assert not ctx.slos_confirmed
        assert ctx.current_slo_index == 0

    def test_add_slo(self):
        """Test adding an SLO."""
        ctx = UnderstandPhaseContext()
        slo = SLO(
            id="slo-1",
            statement="Explain what a database index does",
            frame="EXPLAIN",
        )

        ctx.add_slo(slo)

        assert len(ctx.slos) == 1
        assert ctx.slos[0].statement == "Explain what a database index does"
        # Verify counters and knowledge state initialized
        assert "slo-1" in ctx.slo_counters
        assert "slo-1" in ctx.knowledge_states
        assert ctx.slo_counters["slo-1"]["total_rounds"] == 0

    def test_get_current_slo(self):
        """Test getting current SLO."""
        ctx = UnderstandPhaseContext()
        slo1 = SLO(id="slo-1", statement="First SLO", frame="EXPLAIN")
        slo2 = SLO(id="slo-2", statement="Second SLO", frame="DECIDE")
        ctx.add_slo(slo1)
        ctx.add_slo(slo2)
        ctx.selected_slo_ids = ["slo-1", "slo-2"]

        current = ctx.get_current_slo()
        assert current.id == "slo-1"

        ctx.current_slo_index = 1
        current = ctx.get_current_slo()
        assert current.id == "slo-2"

    def test_increment_round(self):
        """Test incrementing round counter."""
        ctx = UnderstandPhaseContext()
        slo = SLO(id="slo-1", statement="Test SLO", frame="EXPLAIN")
        ctx.add_slo(slo)
        ctx.selected_slo_ids = ["slo-1"]

        ctx.increment_round("vocabulary")
        ctx.increment_round("vocabulary")
        ctx.increment_round("mental_model")

        counters = ctx.get_current_counters()
        assert counters["total_rounds"] == 3
        assert counters["facet_rounds"]["vocabulary"] == 2
        assert counters["facet_rounds"]["mental_model"] == 1

    def test_record_pass_and_fail(self):
        """Test recording pass and fail."""
        ctx = UnderstandPhaseContext()
        slo = SLO(id="slo-1", statement="Test SLO", frame="EXPLAIN")
        ctx.add_slo(slo)
        ctx.selected_slo_ids = ["slo-1"]

        # Record passes
        ctx.record_pass()
        ctx.record_pass()
        ctx.record_pass(is_transfer=True)

        counters = ctx.get_current_counters()
        assert counters["consecutive_passes"] == 3
        assert counters["transfer_passes"] == 1

        # Record fail resets consecutive
        ctx.record_fail()
        counters = ctx.get_current_counters()
        assert counters["consecutive_passes"] == 0
        assert counters["transfer_passes"] == 1  # Transfer passes not reset

    def test_is_mastery_criteria_met(self):
        """Test mastery criteria checking."""
        ctx = UnderstandPhaseContext()
        slo = SLO(id="slo-1", statement="Test SLO", frame="EXPLAIN")
        ctx.add_slo(slo)
        ctx.selected_slo_ids = ["slo-1"]

        # Initially not met
        assert not ctx.is_mastery_criteria_met()

        # Add rounds for each facet
        for _ in range(3):
            ctx.increment_round("vocabulary")
            ctx.increment_round("mental_model")
            ctx.increment_round("practical_grasp")
            ctx.increment_round("boundary_conditions")

        # Still not met - need passes
        assert not ctx.is_mastery_criteria_met()

        # Add passes
        for _ in range(3):
            ctx.record_pass()
        ctx.record_pass(is_transfer=True)
        ctx.record_pass(is_transfer=True)

        # Update facet statuses (can't be "missing")
        state = ctx.get_current_knowledge_state()
        for facet in state.values():
            facet.status = "solid"

        # Now should be met
        assert ctx.is_mastery_criteria_met()

    def test_advance_to_next_slo(self):
        """Test advancing to next SLO."""
        ctx = UnderstandPhaseContext()
        slo1 = SLO(id="slo-1", statement="First SLO", frame="EXPLAIN")
        slo2 = SLO(id="slo-2", statement="Second SLO", frame="DECIDE")
        ctx.add_slo(slo1)
        ctx.add_slo(slo2)
        ctx.selected_slo_ids = ["slo-1", "slo-2"]

        # Complete first SLO
        assert ctx.advance_to_next_slo()
        assert ctx.current_slo_index == 1
        assert "slo-1" in ctx.completed_slo_ids

        # No more after second
        ctx.completed_slo_ids.append("slo-2")
        assert not ctx.advance_to_next_slo()

    def test_has_next_slo(self):
        """Test checking for next SLO."""
        ctx = UnderstandPhaseContext()
        slo1 = SLO(id="slo-1", statement="First SLO", frame="EXPLAIN")
        slo2 = SLO(id="slo-2", statement="Second SLO", frame="DECIDE")
        ctx.add_slo(slo1)
        ctx.add_slo(slo2)
        ctx.selected_slo_ids = ["slo-1", "slo-2"]

        assert ctx.has_next_slo()

        ctx.completed_slo_ids = ["slo-1"]
        assert ctx.has_next_slo()

        ctx.completed_slo_ids = ["slo-1", "slo-2"]
        assert not ctx.has_next_slo()

    def test_serialization_round_trip(self):
        """Test serialization and deserialization."""
        ctx = UnderstandPhaseContext()
        ctx.phase_visits = {"self_assess": 1, "configure": 1}
        ctx.knowledge_confidence = "HIGH"
        ctx.session_configured = True
        ctx.pace = "thorough"
        ctx.style = "visual"
        slo = SLO(id="slo-1", statement="Test SLO", frame="EXPLAIN")
        ctx.add_slo(slo)
        ctx.selected_slo_ids = ["slo-1"]
        ctx.increment_round("vocabulary")
        ctx.record_pass()

        # Serialize
        data = ctx.to_dict()

        # Deserialize
        restored = UnderstandPhaseContext.from_dict(data)

        assert restored.phase_visits == ctx.phase_visits
        assert restored.knowledge_confidence == ctx.knowledge_confidence
        assert restored.session_configured == ctx.session_configured
        assert restored.pace == ctx.pace
        assert restored.style == ctx.style
        assert len(restored.slos) == 1
        assert restored.slo_counters["slo-1"]["total_rounds"] == 1


# =============================================================================
# Understand Agent Tests
# =============================================================================

class TestUnderstandAgent:
    """Tests for UnderstandAgent."""

    def test_agent_properties(self, understand_agent):
        """Test agent property definitions."""
        assert understand_agent.Phase == UnderstandPhase
        assert understand_agent.initial_phase == UnderstandPhase.SELF_ASSESS
        assert understand_agent.complete_phase == UnderstandPhase.COMPLETE
        assert understand_agent.agent_type == "understand"

    @pytest.mark.asyncio
    async def test_initialize(self, understand_agent, mock_journey_brief):
        """Test agent initialization."""
        await understand_agent.initialize(mock_journey_brief)

        assert understand_agent.journey_brief == mock_journey_brief
        assert understand_agent.current_phase == UnderstandPhase.SELF_ASSESS
        assert understand_agent.phase_context is not None
        assert understand_agent.phase_context.get_visit_count(UnderstandPhase.SELF_ASSESS) == 1

    def test_phase_tools(self, understand_agent):
        """Test that each phase has appropriate tools."""
        self_assess_tools = understand_agent._get_allowed_tools(UnderstandPhase.SELF_ASSESS)
        assert "mcp__understand__emit_knowledge_confidence" in self_assess_tools

        configure_tools = understand_agent._get_allowed_tools(UnderstandPhase.CONFIGURE)
        assert "mcp__understand__emit_session_config" in configure_tools

        classify_tools = understand_agent._get_allowed_tools(UnderstandPhase.CLASSIFY)
        assert "mcp__understand__emit_slo" in classify_tools
        assert "mcp__understand__mark_slos_selected" in classify_tools

        calibrate_tools = understand_agent._get_allowed_tools(UnderstandPhase.CALIBRATE)
        assert "mcp__understand__update_facet_status" in calibrate_tools
        assert "mcp__understand__mark_calibration_complete" in calibrate_tools

        diagnose_tools = understand_agent._get_allowed_tools(UnderstandPhase.DIAGNOSE)
        assert "mcp__understand__record_diagnostic_result" in diagnose_tools
        assert "mcp__understand__mark_mastery_achieved" in diagnose_tools

    @pytest.mark.asyncio
    async def test_transition_evaluation_forward(self, understand_agent, mock_journey_brief):
        """Test forward transition evaluation."""
        await understand_agent.initialize(mock_journey_brief)

        # Initially, session not configured
        assert not understand_agent._evaluate_transition_condition(
            PhaseTransition(
                from_phase=UnderstandPhase.CONFIGURE,
                to_phase=UnderstandPhase.CLASSIFY,
                condition="session_preferences_set",
            )
        )

        # Configure session
        understand_agent.phase_context.session_configured = True

        assert understand_agent._evaluate_transition_condition(
            PhaseTransition(
                from_phase=UnderstandPhase.CONFIGURE,
                to_phase=UnderstandPhase.CLASSIFY,
                condition="session_preferences_set",
            )
        )

    @pytest.mark.asyncio
    async def test_state_persistence(self, understand_agent, mock_journey_brief):
        """Test state serialization and restoration."""
        await understand_agent.initialize(mock_journey_brief)

        # Add some state
        understand_agent.phase_context.session_configured = True
        understand_agent.phase_context.pace = "focused"
        slo = SLO(id="slo-1", statement="Test SLO", frame="EXPLAIN")
        understand_agent.phase_context.add_slo(slo)

        # Serialize
        state = understand_agent.get_state()

        assert state["agent_type"] == "understand"
        assert state["current_phase"] == "self_assess"
        assert state["phase_context"]["session_configured"] is True
        assert state["phase_context"]["pace"] == "focused"

        # Create new agent and restore
        new_agent = UnderstandAgent(
            session=understand_agent.session,
            emit_event=AsyncMock(),
        )
        new_agent.journey_brief = mock_journey_brief
        await new_agent.restore_state(state)

        assert new_agent.current_phase == UnderstandPhase.SELF_ASSESS
        assert new_agent.phase_context.session_configured is True
        assert new_agent.phase_context.pace == "focused"
        assert len(new_agent.phase_context.slos) == 1

    def test_prompt_generation_initial(self, understand_agent, mock_journey_brief):
        """Test initial prompt generation."""
        understand_agent.journey_brief = mock_journey_brief
        understand_agent.phase_context = UnderstandPhaseContext()

        prompt = understand_agent._get_phase_prompt(UnderstandPhase.SELF_ASSESS, visit_count=1)

        assert "database indexes" in prompt.lower()

    def test_prompt_generation_configure(self, understand_agent, mock_journey_brief):
        """Test configure prompt generation."""
        understand_agent.journey_brief = mock_journey_brief
        understand_agent.phase_context = UnderstandPhaseContext()

        prompt = understand_agent._get_phase_prompt(UnderstandPhase.CONFIGURE, visit_count=1)

        assert "pace" in prompt.lower()
        assert "style" in prompt.lower()


# =============================================================================
# Integration Tests
# =============================================================================

class TestUnderstandAgentIntegration:
    """Integration tests for UnderstandAgent."""

    @pytest.mark.asyncio
    async def test_full_phase_progression(self, understand_agent, mock_journey_brief):
        """Test that agent can progress through phases."""
        await understand_agent.initialize(mock_journey_brief)

        # SELF_ASSESS → CONFIGURE
        understand_agent.phase_context.knowledge_confidence = "HIGH"
        next_phase = understand_agent._evaluate_transitions()
        assert next_phase == UnderstandPhase.CONFIGURE

        # CONFIGURE → CLASSIFY
        understand_agent.current_phase = UnderstandPhase.CONFIGURE
        understand_agent.phase_context.session_configured = True
        next_phase = understand_agent._evaluate_transitions()
        assert next_phase == UnderstandPhase.CLASSIFY

        # CLASSIFY → CALIBRATE
        understand_agent.current_phase = UnderstandPhase.CLASSIFY
        slo = SLO(id="slo-1", statement="Test", frame="EXPLAIN")
        understand_agent.phase_context.add_slo(slo)
        understand_agent.phase_context.selected_slo_ids = ["slo-1"]
        understand_agent.phase_context.slos_confirmed = True
        next_phase = understand_agent._evaluate_transitions()
        assert next_phase == UnderstandPhase.CALIBRATE

        # CALIBRATE → DIAGNOSE
        understand_agent.current_phase = UnderstandPhase.CALIBRATE
        understand_agent.phase_context.current_slo_calibrated = True
        next_phase = understand_agent._evaluate_transitions()
        assert next_phase == UnderstandPhase.DIAGNOSE

    @pytest.mark.asyncio
    async def test_slo_completion_flow(self, understand_agent, mock_journey_brief):
        """Test SLO completion and transition to next."""
        await understand_agent.initialize(mock_journey_brief)

        # Setup two SLOs
        slo1 = SLO(id="slo-1", statement="First SLO", frame="EXPLAIN")
        slo2 = SLO(id="slo-2", statement="Second SLO", frame="DECIDE")
        understand_agent.phase_context.add_slo(slo1)
        understand_agent.phase_context.add_slo(slo2)
        understand_agent.phase_context.selected_slo_ids = ["slo-1", "slo-2"]
        understand_agent.phase_context.slos_confirmed = True

        # Move to SLO_COMPLETE with next SLO available
        understand_agent.current_phase = UnderstandPhase.SLO_COMPLETE
        assert understand_agent.phase_context.has_next_slo()

        next_phase = understand_agent._evaluate_transitions()
        assert next_phase == UnderstandPhase.CALIBRATE  # Back to calibrate for next SLO

        # Complete first, advance to second
        understand_agent.phase_context.advance_to_next_slo()
        assert understand_agent.phase_context.current_slo_index == 1

        # Complete second SLO
        understand_agent.phase_context.completed_slo_ids.append("slo-2")
        assert not understand_agent.phase_context.has_next_slo()

        next_phase = understand_agent._evaluate_transitions()
        assert next_phase == UnderstandPhase.COMPLETE
