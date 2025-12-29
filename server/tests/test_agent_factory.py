"""
Tests for the Agent Factory module.

Tests agent creation, initialization, and state persistence.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from server.persistence import (
    Session,
    JourneyDesignBrief,
    AgentState,
    ResearchModeData,
    UnderstandModeData,
    BuildModeData,
)
from server.agents import (
    create_agent,
    get_or_create_agent,
    save_agent_state,
    get_agent_state_for_restore,
    ResearchAgent,
    UnderstandAgent,
    BuildAgent,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def journey_brief():
    """Create a test journey brief."""
    return JourneyDesignBrief(
        original_question="How do I build a REST API?",
        ideal_answer="You can build a REST API by...",
        answer_type="skill",
        primary_mode="build",
        confirmation_message="Let's build a REST API together!",
    )


@pytest.fixture
def research_session():
    """Create a test research session."""
    return Session(
        id="test-research-session",
        mode="research",
        research_data=ResearchModeData(topic="Test topic"),
        agent_state=AgentState(),
    )


@pytest.fixture
def understand_session():
    """Create a test understand session."""
    return Session(
        id="test-understand-session",
        mode="understand",
        understand_data=UnderstandModeData(),
        agent_state=AgentState(),
    )


@pytest.fixture
def build_session():
    """Create a test build session."""
    return Session(
        id="test-build-session",
        mode="build",
        phase="grounding",
        build_data=BuildModeData(),
        agent_state=AgentState(),
    )


@pytest.fixture
def emit_event():
    """Create a mock emit event callback."""
    return AsyncMock()


# =============================================================================
# Test create_agent
# =============================================================================

class TestCreateAgent:
    """Tests for create_agent function."""

    def test_create_research_agent(self, research_session, emit_event):
        """Should create ResearchAgent for research mode."""
        agent = create_agent(research_session, emit_event)
        assert isinstance(agent, ResearchAgent)
        assert agent.session == research_session

    def test_create_understand_agent(self, understand_session, emit_event):
        """Should create UnderstandAgent for understand mode."""
        agent = create_agent(understand_session, emit_event)
        assert isinstance(agent, UnderstandAgent)
        assert agent.session == understand_session

    def test_create_build_agent(self, build_session, emit_event):
        """Should create BuildAgent for build mode."""
        agent = create_agent(build_session, emit_event)
        assert isinstance(agent, BuildAgent)
        assert agent.session == build_session

    def test_invalid_mode_raises(self, emit_event):
        """Should raise ValueError for invalid mode."""
        # Create session with valid mode, then modify it to test factory
        session = Session(id="test", mode="research")
        # Bypass Pydantic validation by directly setting the attribute
        object.__setattr__(session, "mode", "invalid")
        with pytest.raises(ValueError, match="Unknown mode"):
            create_agent(session, emit_event)


# =============================================================================
# Test get_or_create_agent
# =============================================================================

class TestGetOrCreateAgent:
    """Tests for get_or_create_agent function."""

    @pytest.mark.asyncio
    async def test_initializes_fresh_agent(
        self, research_session, journey_brief, emit_event
    ):
        """Should initialize agent when no existing state."""
        agent = await get_or_create_agent(
            research_session, journey_brief, emit_event
        )

        assert agent is not None
        assert agent.journey_brief == journey_brief
        assert agent.current_phase is not None

    @pytest.mark.asyncio
    async def test_restores_agent_state(
        self, research_session, journey_brief, emit_event
    ):
        """Should restore agent from existing state."""
        # Set up existing state (phase values are lowercase)
        research_session.agent_state.counters = {
            "current_phase": "answer",
            "agent_type": "research",
            "phase_context": {
                "phase_visits": {"decompose": 1, "answer": 1},
            },
            "transition_history": [],
        }

        agent = await get_or_create_agent(
            research_session, journey_brief, emit_event
        )

        # Should restore to answer phase
        assert agent.current_phase.value == "answer"


# =============================================================================
# Test save_agent_state
# =============================================================================

class TestSaveAgentState:
    """Tests for save_agent_state function."""

    @pytest.mark.asyncio
    async def test_saves_state_to_session(
        self, research_session, journey_brief, emit_event
    ):
        """Should save agent state to session.agent_state."""
        agent = await get_or_create_agent(
            research_session, journey_brief, emit_event
        )

        save_agent_state(research_session, agent)

        # Check state was saved
        counters = research_session.agent_state.counters
        assert "current_phase" in counters
        assert counters["agent_type"] == "research"
        assert "phase_context" in counters
        assert "transition_history" in counters


# =============================================================================
# Test get_agent_state_for_restore
# =============================================================================

class TestGetAgentStateForRestore:
    """Tests for get_agent_state_for_restore function."""

    def test_returns_empty_for_no_state(self):
        """Should return empty dict when no state exists."""
        session = Session(id="test", mode="research")
        state = get_agent_state_for_restore(session)

        assert state.get("current_phase") is None
        assert state.get("phase_context") == {}
        assert state.get("transition_history") == []

    def test_returns_existing_state(self):
        """Should return existing state from counters."""
        session = Session(
            id="test",
            mode="research",
            agent_state=AgentState(
                counters={
                    "current_phase": "ANSWER",
                    "phase_context": {"phase_visits": {"DECOMPOSE": 1}},
                    "transition_history": [{"from": "DECOMPOSE", "to": "ANSWER"}],
                }
            ),
        )

        state = get_agent_state_for_restore(session)

        assert state["current_phase"] == "ANSWER"
        assert state["phase_context"]["phase_visits"]["DECOMPOSE"] == 1
        assert len(state["transition_history"]) == 1


# =============================================================================
# Test Round Trip
# =============================================================================

class TestRoundTrip:
    """Tests for save/restore round trip."""

    @pytest.mark.asyncio
    async def test_state_round_trip(
        self, research_session, journey_brief, emit_event
    ):
        """Agent state should survive save/restore cycle."""
        # Create and initialize agent
        agent1 = await get_or_create_agent(
            research_session, journey_brief, emit_event
        )
        original_phase = agent1.current_phase

        # Save state
        save_agent_state(research_session, agent1)

        # Create new agent from saved state
        agent2 = await get_or_create_agent(
            research_session, journey_brief, emit_event
        )

        # Phase should be preserved
        assert agent2.current_phase == original_phase
