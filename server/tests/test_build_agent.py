"""
Tests for BuildAgent.

Tests the Constructivist tutoring system using the Claude Agent SDK
and phase graph pattern.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from server.agents.build import (
    BuildAgent,
    BuildPhase,
    BuildPhaseContext,
    BUILD_TRANSITIONS,
)
from server.agents.build.phases import Anchor, ConstructionSLO, ConstructionRound
from server.persistence import Session, JourneyDesignBrief, BuildModeData


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_session():
    """Create a mock session."""
    session = MagicMock(spec=Session)
    session.id = "test-session-id"
    session.build_data = BuildModeData()
    return session


@pytest.fixture
def mock_emit():
    """Create a mock event emitter."""
    return AsyncMock()


@pytest.fixture
def mock_checkpoint_handler():
    """Create a mock checkpoint handler."""
    handler = AsyncMock()
    handler.return_value = MagicMock(approved=True, selected_option="Ready to proceed")
    return handler


@pytest.fixture
def journey_brief():
    """Create a test journey brief."""
    return JourneyDesignBrief(
        original_question="How do ReACT agents work?",
        ideal_answer="A deep understanding of ReACT agent mechanisms",
        answer_type="understanding",
        primary_mode="build",
        confirmation_message="Let's build understanding of ReACT agents",
    )


@pytest.fixture
def agent(mock_session, mock_emit, mock_checkpoint_handler):
    """Create a BuildAgent instance."""
    return BuildAgent(
        session=mock_session,
        emit_event=mock_emit,
        checkpoint_handler=mock_checkpoint_handler,
    )


# =============================================================================
# BuildPhase Tests
# =============================================================================


class TestBuildPhase:
    """Tests for BuildPhase enum."""

    def test_all_phases_exist(self):
        """Test all expected phases exist."""
        expected = [
            "ANCHOR_DISCOVERY",
            "CLASSIFY",
            "SEQUENCE_DESIGN",
            "CONSTRUCTION",
            "SLO_COMPLETE",
            "CONSOLIDATION",
            "COMPLETE",
        ]
        actual = [p.name for p in BuildPhase]
        assert actual == expected

    def test_phase_values(self):
        """Test phase enum values."""
        assert BuildPhase.ANCHOR_DISCOVERY.value == "anchor_discovery"
        assert BuildPhase.CLASSIFY.value == "classify"
        assert BuildPhase.SEQUENCE_DESIGN.value == "sequence_design"
        assert BuildPhase.CONSTRUCTION.value == "construction"
        assert BuildPhase.SLO_COMPLETE.value == "slo_complete"
        assert BuildPhase.CONSOLIDATION.value == "consolidation"
        assert BuildPhase.COMPLETE.value == "complete"


# =============================================================================
# BuildPhaseContext Tests
# =============================================================================


class TestBuildPhaseContext:
    """Tests for BuildPhaseContext."""

    def test_initial_state(self):
        """Test initial context state."""
        ctx = BuildPhaseContext()
        assert ctx.anchors == []
        assert ctx.primary_anchor_id is None
        assert ctx.anchors_confirmed is False
        assert ctx.topic_type == "ATOMIC"
        assert ctx.slos == []
        assert ctx.selected_slo_ids == []
        assert ctx.current_scaffold_level == "medium"
        assert ctx.current_mode == "normal"
        assert ctx.consecutive_surrenders == 0

    def test_add_anchor(self):
        """Test adding an anchor."""
        ctx = BuildPhaseContext()
        anchor = Anchor(
            id="anchor-1",
            description="Debugging with print statements",
            strength="strong",
            evidence="Mentioned extensive experience",
        )
        ctx.add_anchor(anchor)
        assert len(ctx.anchors) == 1
        assert ctx.anchors[0].id == "anchor-1"
        assert ctx.anchors[0].strength == "strong"

    def test_get_anchor(self):
        """Test retrieving an anchor by ID."""
        ctx = BuildPhaseContext()
        anchor = Anchor(
            id="anchor-1",
            description="Book index",
            strength="medium",
            evidence="Used library catalogs",
        )
        ctx.add_anchor(anchor)

        found = ctx.get_anchor("anchor-1")
        assert found is not None
        assert found.description == "Book index"

        not_found = ctx.get_anchor("nonexistent")
        assert not_found is None

    def test_get_strong_anchors(self):
        """Test filtering strong anchors."""
        ctx = BuildPhaseContext()
        ctx.add_anchor(Anchor(id="a1", description="Strong anchor", strength="strong", evidence="e1"))
        ctx.add_anchor(Anchor(id="a2", description="Weak anchor", strength="weak", evidence="e2"))
        ctx.add_anchor(Anchor(id="a3", description="Another strong", strength="strong", evidence="e3"))

        strong = ctx.get_strong_anchors()
        assert len(strong) == 2
        assert all(a.strength == "strong" for a in strong)

    def test_add_slo(self):
        """Test adding an SLO."""
        ctx = BuildPhaseContext()
        slo = ConstructionSLO(
            id="slo-1",
            statement="Build understanding of observe step",
            frame="BUILD",
            anchor_id="anchor-1",
            in_scope=["observation", "feedback loop"],
            out_of_scope=["advanced patterns"],
        )
        ctx.add_slo(slo)
        assert len(ctx.slos) == 1
        assert ctx.slo_status["slo-1"] == "not_started"
        assert ctx.construction_rounds["slo-1"] == []

    def test_get_current_slo(self):
        """Test getting current SLO."""
        ctx = BuildPhaseContext()
        slo1 = ConstructionSLO(id="slo-1", statement="SLO 1", frame="BUILD", anchor_id="a1", in_scope=[], out_of_scope=[])
        slo2 = ConstructionSLO(id="slo-2", statement="SLO 2", frame="CONNECT", anchor_id="a2", in_scope=[], out_of_scope=[])
        ctx.add_slo(slo1)
        ctx.add_slo(slo2)
        ctx.selected_slo_ids = ["slo-1", "slo-2"]

        current = ctx.get_current_slo()
        assert current is not None
        assert current.id == "slo-1"

        ctx.current_slo_index = 1
        current = ctx.get_current_slo()
        assert current.id == "slo-2"

    def test_construction_rounds(self):
        """Test adding construction rounds."""
        ctx = BuildPhaseContext()
        slo = ConstructionSLO(id="slo-1", statement="Test SLO", frame="BUILD", anchor_id="a1", in_scope=[], out_of_scope=[])
        ctx.add_slo(slo)
        ctx.selected_slo_ids = ["slo-1"]

        round1 = ConstructionRound(
            round_num=1,
            scaffold_type="question",
            scaffold_content="What happens after the agent acts?",
            learner_response="It observes the result",
            outcome="partial",
        )
        ctx.add_construction_round(round1)

        rounds = ctx.get_current_rounds()
        assert len(rounds) == 1
        assert rounds[0].outcome == "partial"

    def test_scaffold_level_adjustment(self):
        """Test scaffold level increase/decrease."""
        ctx = BuildPhaseContext()

        # Start at medium
        assert ctx.current_scaffold_level == "medium"

        # Increase to heavy
        ctx.increase_scaffold()
        assert ctx.current_scaffold_level == "heavy"

        # Can't go higher than heavy
        ctx.increase_scaffold()
        assert ctx.current_scaffold_level == "heavy"

        # Decrease back down
        ctx.decrease_scaffold()
        assert ctx.current_scaffold_level == "medium"

        ctx.decrease_scaffold()
        assert ctx.current_scaffold_level == "light"

        ctx.decrease_scaffold()
        assert ctx.current_scaffold_level == "none"

        # Can't go lower than none
        ctx.decrease_scaffold()
        assert ctx.current_scaffold_level == "none"

    def test_mode_transitions(self):
        """Test mode transitions."""
        ctx = BuildPhaseContext()

        assert ctx.current_mode == "normal"
        assert ctx.consecutive_surrenders == 0

        ctx.enter_surrender_recovery()
        assert ctx.current_mode == "surrender_recovery"
        assert ctx.consecutive_surrenders == 1

        ctx.enter_surrender_recovery()
        assert ctx.consecutive_surrenders == 2

        ctx.enter_code_mode()
        assert ctx.current_mode == "code"

        ctx.exit_special_mode()
        assert ctx.current_mode == "normal"
        assert ctx.consecutive_surrenders == 0

    def test_advance_to_next_slo(self):
        """Test advancing through SLOs."""
        ctx = BuildPhaseContext()
        ctx.add_slo(ConstructionSLO(id="slo-1", statement="S1", frame="BUILD", anchor_id="a1", in_scope=[], out_of_scope=[]))
        ctx.add_slo(ConstructionSLO(id="slo-2", statement="S2", frame="CONNECT", anchor_id="a2", in_scope=[], out_of_scope=[]))
        ctx.add_slo(ConstructionSLO(id="slo-3", statement="S3", frame="TRANSFER", anchor_id="a3", in_scope=[], out_of_scope=[]))
        ctx.selected_slo_ids = ["slo-1", "slo-2", "slo-3"]

        # First SLO is current
        assert ctx.get_current_slo().id == "slo-1"

        # Complete first, advance to second
        success = ctx.advance_to_next_slo()
        assert success
        assert ctx.get_current_slo().id == "slo-2"
        assert "slo-1" in ctx.completed_slo_ids

        # Complete second, advance to third
        success = ctx.advance_to_next_slo()
        assert success
        assert ctx.get_current_slo().id == "slo-3"

        # Complete third, no more SLOs
        success = ctx.advance_to_next_slo()
        assert not success

    def test_mark_current_constructed(self):
        """Test marking current SLO as constructed."""
        ctx = BuildPhaseContext()
        ctx.add_slo(ConstructionSLO(id="slo-1", statement="S1", frame="BUILD", anchor_id="a1", in_scope=[], out_of_scope=[]))
        ctx.selected_slo_ids = ["slo-1"]

        assert ctx.slo_status["slo-1"] == "not_started"

        ctx.mark_current_constructed()
        assert ctx.slo_status["slo-1"] == "constructed"

    def test_serialization(self):
        """Test context serialization/deserialization."""
        ctx = BuildPhaseContext()
        ctx.add_anchor(Anchor(id="a1", description="Anchor 1", strength="strong", evidence="e1"))
        ctx.primary_anchor_id = "a1"
        ctx.anchors_confirmed = True
        ctx.topic_type = "COMPOSITE"
        ctx.add_slo(ConstructionSLO(id="slo-1", statement="S1", frame="BUILD", anchor_id="a1", in_scope=[], out_of_scope=[]))
        ctx.selected_slo_ids = ["slo-1"]
        ctx.current_scaffold_level = "heavy"
        ctx.current_mode = "code"

        data = ctx.to_dict()
        restored = BuildPhaseContext.from_dict(data)

        assert len(restored.anchors) == 1
        assert restored.primary_anchor_id == "a1"
        assert restored.anchors_confirmed is True
        assert restored.topic_type == "COMPOSITE"
        assert len(restored.slos) == 1
        assert restored.current_scaffold_level == "heavy"
        assert restored.current_mode == "code"


# =============================================================================
# BuildAgent Tests
# =============================================================================


class TestBuildAgent:
    """Tests for BuildAgent class."""

    @pytest.mark.asyncio
    async def test_initialization(self, agent, journey_brief):
        """Test agent initialization."""
        await agent.initialize(journey_brief)

        assert agent.journey_brief is not None
        assert agent.phase_context is not None
        assert agent._mcp_server is not None

    def test_agent_type(self, agent):
        """Test agent type property."""
        assert agent.agent_type == "build"

    def test_initial_phase(self, agent):
        """Test initial phase."""
        assert agent.initial_phase == BuildPhase.ANCHOR_DISCOVERY

    def test_complete_phase(self, agent):
        """Test complete phase."""
        assert agent.complete_phase == BuildPhase.COMPLETE

    @pytest.mark.asyncio
    async def test_allowed_tools_anchor_discovery(self, agent, journey_brief):
        """Test allowed tools for anchor discovery phase."""
        await agent.initialize(journey_brief)
        tools = agent._get_allowed_tools(BuildPhase.ANCHOR_DISCOVERY)

        assert "mcp__build__emit_anchor" in tools
        assert "mcp__build__set_primary_anchor" in tools
        assert "mcp__build__mark_anchors_confirmed" in tools
        assert "mcp__build__get_phase_context" in tools

    @pytest.mark.asyncio
    async def test_allowed_tools_classify(self, agent, journey_brief):
        """Test allowed tools for classify phase."""
        await agent.initialize(journey_brief)
        tools = agent._get_allowed_tools(BuildPhase.CLASSIFY)

        assert "mcp__build__emit_topic_type" in tools
        assert "mcp__build__emit_construction_slo" in tools
        assert "mcp__build__mark_slos_selected" in tools

    @pytest.mark.asyncio
    async def test_allowed_tools_construction(self, agent, journey_brief):
        """Test allowed tools for construction phase."""
        await agent.initialize(journey_brief)
        tools = agent._get_allowed_tools(BuildPhase.CONSTRUCTION)

        assert "WebSearch" in tools
        assert "mcp__build__record_construction_round" in tools
        assert "mcp__build__set_scaffold_level" in tools
        assert "mcp__build__enter_code_mode" in tools
        assert "mcp__build__emit_surrender_strategy" in tools
        assert "mcp__build__flag_anchor_gap" in tools
        assert "mcp__build__mark_construction_verified" in tools


# =============================================================================
# Phase Transitions Tests
# =============================================================================


class TestBuildTransitions:
    """Tests for phase transitions."""

    def test_transitions_count(self):
        """Test expected number of transitions."""
        assert len(BUILD_TRANSITIONS) == 8

    def test_anchor_to_classify_transition(self):
        """Test transition from anchor discovery to classify."""
        transition = next(t for t in BUILD_TRANSITIONS if t.from_phase == BuildPhase.ANCHOR_DISCOVERY)
        assert transition.to_phase == BuildPhase.CLASSIFY
        assert transition.condition == "anchors_confirmed"
        assert not transition.is_backward

    def test_classify_to_sequence_transition(self):
        """Test transition from classify to sequence design."""
        transition = next(t for t in BUILD_TRANSITIONS if t.from_phase == BuildPhase.CLASSIFY)
        assert transition.to_phase == BuildPhase.SEQUENCE_DESIGN
        assert transition.condition == "slos_selected"

    def test_construction_to_slo_complete_transition(self):
        """Test transition from construction to SLO complete."""
        transition = next(
            t for t in BUILD_TRANSITIONS
            if t.from_phase == BuildPhase.CONSTRUCTION and not t.is_backward
        )
        assert transition.to_phase == BuildPhase.SLO_COMPLETE
        assert transition.condition == "construction_verified"

    def test_slo_complete_backward_transition(self):
        """Test backward transition for next SLO."""
        transition = next(
            t for t in BUILD_TRANSITIONS
            if t.from_phase == BuildPhase.SLO_COMPLETE and t.is_backward
        )
        assert transition.to_phase == BuildPhase.CONSTRUCTION
        assert transition.condition == "next_slo_available"

    def test_anchor_gap_backward_transition(self):
        """Test backward transition on anchor gap."""
        transition = next(
            t for t in BUILD_TRANSITIONS
            if t.condition == "anchor_gap_detected"
        )
        assert transition.from_phase == BuildPhase.CONSTRUCTION
        assert transition.to_phase == BuildPhase.ANCHOR_DISCOVERY
        assert transition.is_backward


# =============================================================================
# Transition Condition Tests
# =============================================================================


class TestTransitionConditions:
    """Tests for transition condition evaluation."""

    @pytest.mark.asyncio
    async def test_anchors_confirmed_condition(self, agent, journey_brief):
        """Test anchors_confirmed condition."""
        await agent.initialize(journey_brief)

        # Get transition
        transition = next(t for t in BUILD_TRANSITIONS if t.condition == "anchors_confirmed")

        # Initially false
        assert not agent._evaluate_transition_condition(transition)

        # After confirmation
        agent.phase_context.anchors_confirmed = True
        assert agent._evaluate_transition_condition(transition)

    @pytest.mark.asyncio
    async def test_slos_selected_condition(self, agent, journey_brief):
        """Test slos_selected condition."""
        await agent.initialize(journey_brief)

        transition = next(t for t in BUILD_TRANSITIONS if t.condition == "slos_selected")

        # Initially false
        assert not agent._evaluate_transition_condition(transition)

        # Confirmed but no SLOs selected
        agent.phase_context.slos_confirmed = True
        assert not agent._evaluate_transition_condition(transition)

        # With SLOs selected
        agent.phase_context.selected_slo_ids = ["slo-1"]
        assert agent._evaluate_transition_condition(transition)

    @pytest.mark.asyncio
    async def test_construction_verified_condition(self, agent, journey_brief):
        """Test construction_verified condition."""
        await agent.initialize(journey_brief)

        transition = next(t for t in BUILD_TRANSITIONS if t.condition == "construction_verified")

        # Set up SLO
        slo = ConstructionSLO(id="slo-1", statement="Test", frame="BUILD", anchor_id="a1", in_scope=[], out_of_scope=[])
        agent.phase_context.add_slo(slo)
        agent.phase_context.selected_slo_ids = ["slo-1"]

        # Initially false
        assert not agent._evaluate_transition_condition(transition)

        # After construction verified
        agent.phase_context.mark_current_constructed()
        assert agent._evaluate_transition_condition(transition)

    @pytest.mark.asyncio
    async def test_next_slo_available_condition(self, agent, journey_brief):
        """Test next_slo_available condition."""
        await agent.initialize(journey_brief)

        transition = next(t for t in BUILD_TRANSITIONS if t.condition == "next_slo_available")

        # Add multiple SLOs
        agent.phase_context.add_slo(ConstructionSLO(id="slo-1", statement="S1", frame="BUILD", anchor_id="a1", in_scope=[], out_of_scope=[]))
        agent.phase_context.add_slo(ConstructionSLO(id="slo-2", statement="S2", frame="CONNECT", anchor_id="a2", in_scope=[], out_of_scope=[]))
        agent.phase_context.selected_slo_ids = ["slo-1", "slo-2"]

        # Has next
        assert agent._evaluate_transition_condition(transition)

        # Complete all
        agent.phase_context.completed_slo_ids = ["slo-1", "slo-2"]
        assert not agent._evaluate_transition_condition(transition)

    @pytest.mark.asyncio
    async def test_anchor_gap_detected_condition(self, agent, journey_brief):
        """Test anchor_gap_detected condition."""
        await agent.initialize(journey_brief)

        transition = next(t for t in BUILD_TRANSITIONS if t.condition == "anchor_gap_detected")

        # Initially false
        assert not agent._evaluate_transition_condition(transition)

        # After gap detection
        agent.phase_context.backward_trigger = "anchor_gap_detected"
        assert agent._evaluate_transition_condition(transition)


# =============================================================================
# Completion Summary Tests
# =============================================================================


class TestCompletionSummary:
    """Tests for completion summary generation."""

    @pytest.mark.asyncio
    async def test_completion_summary(self, agent, journey_brief):
        """Test completion summary generation."""
        await agent.initialize(journey_brief)

        # Set up completed state
        agent.phase_context.add_anchor(Anchor(id="a1", description="A1", strength="strong", evidence="e1"))
        agent.phase_context.add_anchor(Anchor(id="a2", description="A2", strength="medium", evidence="e2"))
        agent.phase_context.add_slo(ConstructionSLO(id="slo-1", statement="S1", frame="BUILD", anchor_id="a1", in_scope=[], out_of_scope=[]))
        agent.phase_context.completed_slo_ids = ["slo-1"]
        agent.phase_context.construction_rounds["slo-1"] = [
            ConstructionRound(1, "question", "Q1", "R1", "partial"),
            ConstructionRound(2, "scenario", "S1", "R2", "constructed"),
        ]

        summary = agent._generate_completion_summary()

        assert "1 concepts" in summary
        assert "2 anchors" in summary
        assert "2" in summary  # Total rounds


# =============================================================================
# State Persistence Tests
# =============================================================================


class TestStatePersistence:
    """Tests for state persistence."""

    @pytest.mark.asyncio
    async def test_serialize_phase_context(self, agent, journey_brief):
        """Test phase context serialization."""
        await agent.initialize(journey_brief)

        agent.phase_context.add_anchor(Anchor(id="a1", description="Test", strength="strong", evidence="e1"))
        agent.phase_context.primary_anchor_id = "a1"
        agent.phase_context.anchors_confirmed = True

        state = agent._serialize_phase_context()

        assert len(state["anchors"]) == 1
        assert state["primary_anchor_id"] == "a1"
        assert state["anchors_confirmed"] is True

    @pytest.mark.asyncio
    async def test_restore_phase_context(self, agent, journey_brief):
        """Test phase context restoration."""
        await agent.initialize(journey_brief)

        state = {
            "anchors": [{"id": "a1", "description": "Restored", "strength": "medium", "evidence": "e1"}],
            "primary_anchor_id": "a1",
            "anchors_confirmed": True,
            "topic_type": "SYSTEM",
            "slos": [],
            "selected_slo_ids": [],
            "slos_confirmed": False,
            "construction_sequences": {},
            "sequences_designed": False,
            "current_slo_index": 0,
            "current_scaffold_level": "light",
            "current_mode": "normal",
            "construction_rounds": {},
            "slo_status": {},
            "consecutive_surrenders": 0,
            "effective_strategies": [],
            "completed_slo_ids": [],
            "skipped_slo_ids": [],
            "consolidation_complete": False,
            "session_insights": [],
        }

        agent._restore_phase_context(state)

        assert len(agent.phase_context.anchors) == 1
        assert agent.phase_context.anchors[0].description == "Restored"
        assert agent.phase_context.primary_anchor_id == "a1"
        assert agent.phase_context.topic_type == "SYSTEM"
        assert agent.phase_context.current_scaffold_level == "light"

    @pytest.mark.asyncio
    async def test_get_state(self, agent, journey_brief):
        """Test full state retrieval."""
        await agent.initialize(journey_brief)

        state = agent.get_state()

        assert "mode_data" in state
        assert "topic" in state["mode_data"]
        assert state["mode_data"]["topic"] == "How do ReACT agents work?"
