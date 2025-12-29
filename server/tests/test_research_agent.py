"""
Tests for the Research Agent.

Tests cover:
- Phase progression (forward transitions)
- Backward transitions
- Re-entry behavior
- State persistence
- Checkpoint handling
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from server.agents.research import (
    ResearchAgent,
    ResearchPhase,
    ResearchPhaseContext,
)
from server.agents.research.phases import RESEARCH_TRANSITIONS
from server.agents.base import PhaseTransition, Checkpoint, CheckpointResponse
from server.persistence import (
    Session,
    JourneyDesignBrief,
    ResearchModeData,
    CategoryQuestion,
    Question,
)
from server.api.streaming import SSEEvent


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_session():
    """Create a mock session for testing."""
    session = Session(
        id="test-session-123",
        mode="research",
        research_data=ResearchModeData(topic="Test Topic"),
    )
    return session


@pytest.fixture
def mock_journey_brief():
    """Create a mock journey brief for testing."""
    return JourneyDesignBrief(
        original_question="What are the best practices for LLM fine-tuning?",
        ideal_answer="A comprehensive guide to LLM fine-tuning techniques",
        answer_type="facts",
        primary_mode="research",
        confirmation_message="Let's research LLM fine-tuning",
    )


@pytest.fixture
def mock_emit():
    """Create a mock event emitter."""
    return MagicMock()


@pytest.fixture
def mock_checkpoint_handler():
    """Create a mock checkpoint handler that auto-approves."""
    return MagicMock(return_value=CheckpointResponse(approved=True))


@pytest.fixture
def research_agent(mock_session, mock_emit, mock_checkpoint_handler):
    """Create a Research Agent for testing."""
    return ResearchAgent(
        session=mock_session,
        emit_event=mock_emit,
        client=None,  # Will be mocked for API calls
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
            ResearchPhase.DECOMPOSE,
            ResearchPhase.ANSWER,
            ResearchPhase.RISE_ABOVE,
            ResearchPhase.EXPAND,
        ]

        for phase in non_terminal_phases:
            forward_transitions = [
                t for t in RESEARCH_TRANSITIONS
                if t.from_phase == phase and not t.is_backward
            ]
            assert len(forward_transitions) >= 1, f"No forward transition from {phase}"

    def test_backward_transitions_exist(self):
        """Verify backward transitions are defined."""
        backward_transitions = [t for t in RESEARCH_TRANSITIONS if t.is_backward]
        assert len(backward_transitions) >= 2, "Should have at least 2 backward transitions"

    def test_backward_transition_from_answer(self):
        """ANSWER should have backward transition to DECOMPOSE."""
        transition = next(
            (t for t in RESEARCH_TRANSITIONS
             if t.from_phase == ResearchPhase.ANSWER
             and t.to_phase == ResearchPhase.DECOMPOSE
             and t.is_backward),
            None,
        )
        assert transition is not None
        assert transition.condition == "new_category_discovered"

    def test_backward_transition_from_rise_above(self):
        """RISE_ABOVE should have backward transition to ANSWER."""
        transition = next(
            (t for t in RESEARCH_TRANSITIONS
             if t.from_phase == ResearchPhase.RISE_ABOVE
             and t.to_phase == ResearchPhase.ANSWER
             and t.is_backward),
            None,
        )
        assert transition is not None
        assert transition.condition == "synthesis_requires_more_answers"

    def test_complete_phase_has_no_transitions(self):
        """COMPLETE phase should have no outgoing transitions."""
        complete_transitions = [
            t for t in RESEARCH_TRANSITIONS
            if t.from_phase == ResearchPhase.COMPLETE
        ]
        assert len(complete_transitions) == 0


# =============================================================================
# Phase Context Tests
# =============================================================================

class TestResearchPhaseContext:
    """Tests for ResearchPhaseContext."""

    def test_initial_state(self):
        """Test initial context state."""
        ctx = ResearchPhaseContext()

        assert len(ctx.categories) == 0
        assert len(ctx.questions) == 0
        assert not ctx.question_tree_approved
        assert len(ctx.answered_question_ids) == 0
        assert not ctx.high_priority_complete

    def test_add_category(self):
        """Test adding a category."""
        ctx = ResearchPhaseContext()
        category = CategoryQuestion(
            id="cat-1",
            category="Fundamentals",
            question_ids=[],
        )

        ctx.add_category(category)

        assert len(ctx.categories) == 1
        assert ctx.categories[0].category == "Fundamentals"

    def test_add_question(self):
        """Test adding a question."""
        ctx = ResearchPhaseContext()
        question = Question(
            id="q-1",
            question="What is fine-tuning?",
            status="open",
            category_id="cat-1",
        )

        ctx.add_question(question)

        assert len(ctx.questions) == 1
        assert ctx.questions[0].question == "What is fine-tuning?"

    def test_mark_question_answered(self):
        """Test marking a question as answered."""
        ctx = ResearchPhaseContext()
        question = Question(id="q-1", question="Test?", status="open")
        ctx.add_question(question)

        ctx.mark_question_answered("q-1")

        assert "q-1" in ctx.answered_question_ids

    def test_get_unanswered_questions(self):
        """Test getting unanswered questions."""
        ctx = ResearchPhaseContext()
        q1 = Question(id="q-1", question="Test 1?", status="open")
        q2 = Question(id="q-2", question="Test 2?", status="open")
        ctx.add_question(q1)
        ctx.add_question(q2)
        ctx.mark_question_answered("q-1")

        unanswered = ctx.get_unanswered_questions()

        assert len(unanswered) == 1
        assert unanswered[0].id == "q-2"

    def test_backward_trigger_detection(self):
        """Test backward trigger detection."""
        ctx = ResearchPhaseContext()

        # Initially no triggers
        assert not ctx.should_trigger_backward_to_decompose()
        assert not ctx.should_trigger_backward_to_answer()

        # Set trigger for decompose
        ctx.new_category_pending = "New Category"
        assert ctx.should_trigger_backward_to_decompose()

        # Set trigger for answer
        ctx.unanswered_for_synthesis = ["q-1", "q-2"]
        assert ctx.should_trigger_backward_to_answer()

    def test_clear_backward_triggers(self):
        """Test clearing backward triggers."""
        ctx = ResearchPhaseContext()
        ctx.new_category_pending = "New Category"
        ctx.unanswered_for_synthesis = ["q-1"]

        ctx.clear_backward_triggers()

        assert ctx.new_category_pending is None
        assert len(ctx.unanswered_for_synthesis) == 0

    def test_serialization_round_trip(self):
        """Test serialization and deserialization."""
        ctx = ResearchPhaseContext()
        ctx.phase_visits = {"decompose": 2, "answer": 1}
        ctx.question_tree_approved = True
        category = CategoryQuestion(id="cat-1", category="Test", question_ids=["q-1"])
        ctx.add_category(category)
        question = Question(id="q-1", question="Test?", status="answered", category_id="cat-1")
        ctx.add_question(question)
        ctx.mark_question_answered("q-1")

        # Serialize
        data = ctx.to_dict()

        # Deserialize
        restored = ResearchPhaseContext.from_dict(data)

        assert restored.phase_visits == ctx.phase_visits
        assert restored.question_tree_approved == ctx.question_tree_approved
        assert len(restored.categories) == 1
        assert len(restored.questions) == 1
        assert "q-1" in restored.answered_question_ids


# =============================================================================
# Research Agent Tests
# =============================================================================

class TestResearchAgent:
    """Tests for ResearchAgent."""

    def test_agent_properties(self, research_agent):
        """Test agent property definitions."""
        assert research_agent.Phase == ResearchPhase
        assert research_agent.initial_phase == ResearchPhase.DECOMPOSE
        assert research_agent.complete_phase == ResearchPhase.COMPLETE
        assert research_agent.agent_type == "research"

    @pytest.mark.asyncio
    async def test_initialize(self, research_agent, mock_journey_brief):
        """Test agent initialization."""
        await research_agent.initialize(mock_journey_brief)

        assert research_agent.journey_brief == mock_journey_brief
        assert research_agent.current_phase == ResearchPhase.DECOMPOSE
        assert research_agent.phase_context is not None
        assert research_agent.phase_context.get_visit_count(ResearchPhase.DECOMPOSE) == 1

    def test_phase_tools(self, research_agent):
        """Test that each phase has appropriate tools."""
        decompose_tools = research_agent._get_phase_tools(ResearchPhase.DECOMPOSE)
        assert any(t["name"] == "emit_category" for t in decompose_tools)
        assert any(t["name"] == "emit_question" for t in decompose_tools)

        answer_tools = research_agent._get_phase_tools(ResearchPhase.ANSWER)
        assert any(t["name"] == "web_search" for t in answer_tools)
        assert any(t["name"] == "emit_answer" for t in answer_tools)

        rise_above_tools = research_agent._get_phase_tools(ResearchPhase.RISE_ABOVE)
        assert any(t["name"] == "emit_category_insight" for t in rise_above_tools)
        assert any(t["name"] == "emit_key_insight" for t in rise_above_tools)

        expand_tools = research_agent._get_phase_tools(ResearchPhase.EXPAND)
        assert any(t["name"] == "emit_adjacent_question" for t in expand_tools)

    @pytest.mark.asyncio
    async def test_transition_evaluation_forward(self, research_agent, mock_journey_brief):
        """Test forward transition evaluation."""
        await research_agent.initialize(mock_journey_brief)

        # Initially, question_tree_approved is False
        assert not research_agent._evaluate_transition_condition(
            PhaseTransition(
                from_phase=ResearchPhase.DECOMPOSE,
                to_phase=ResearchPhase.ANSWER,
                condition="question_tree_approved",
            )
        )

        # Approve question tree
        research_agent.phase_context.question_tree_approved = True

        assert research_agent._evaluate_transition_condition(
            PhaseTransition(
                from_phase=ResearchPhase.DECOMPOSE,
                to_phase=ResearchPhase.ANSWER,
                condition="question_tree_approved",
            )
        )

    @pytest.mark.asyncio
    async def test_transition_evaluation_backward(self, research_agent, mock_journey_brief):
        """Test backward transition evaluation."""
        await research_agent.initialize(mock_journey_brief)

        # No backward trigger initially
        assert not research_agent._evaluate_transition_condition(
            PhaseTransition(
                from_phase=ResearchPhase.ANSWER,
                to_phase=ResearchPhase.DECOMPOSE,
                condition="new_category_discovered",
                is_backward=True,
            )
        )

        # Set backward trigger
        research_agent.phase_context.new_category_pending = "New Category"

        assert research_agent._evaluate_transition_condition(
            PhaseTransition(
                from_phase=ResearchPhase.ANSWER,
                to_phase=ResearchPhase.DECOMPOSE,
                condition="new_category_discovered",
                is_backward=True,
            )
        )

    @pytest.mark.asyncio
    async def test_state_persistence(self, research_agent, mock_journey_brief):
        """Test state serialization and restoration."""
        await research_agent.initialize(mock_journey_brief)

        # Add some state
        research_agent.phase_context.question_tree_approved = True
        category = CategoryQuestion(id="cat-1", category="Test", question_ids=[])
        research_agent.phase_context.add_category(category)

        # Serialize
        state = research_agent.get_state()

        assert state["agent_type"] == "research"
        assert state["current_phase"] == "decompose"
        assert state["phase_context"]["question_tree_approved"] is True

        # Create new agent and restore
        new_agent = ResearchAgent(
            session=research_agent.session,
            emit_event=MagicMock(),
        )
        new_agent.journey_brief = mock_journey_brief
        await new_agent.restore_state(state)

        assert new_agent.current_phase == ResearchPhase.DECOMPOSE
        assert new_agent.phase_context.question_tree_approved is True
        assert len(new_agent.phase_context.categories) == 1

    def test_prompt_generation_initial(self, research_agent, mock_journey_brief):
        """Test initial prompt generation."""
        research_agent.journey_brief = mock_journey_brief
        research_agent.phase_context = ResearchPhaseContext()

        prompt = research_agent._get_phase_prompt(ResearchPhase.DECOMPOSE, visit_count=1)

        assert "DECOMPOSE" in prompt
        assert mock_journey_brief.original_question in prompt

    def test_prompt_generation_reentry(self, research_agent, mock_journey_brief):
        """Test re-entry prompt generation."""
        research_agent.journey_brief = mock_journey_brief
        research_agent.phase_context = ResearchPhaseContext()
        research_agent.phase_context.backward_trigger = "new_category_discovered"
        research_agent.phase_context.backward_trigger_detail = "Found a new area"
        category = CategoryQuestion(id="cat-1", category="Existing", question_ids=[])
        research_agent.phase_context.add_category(category)

        prompt = research_agent._get_phase_prompt(ResearchPhase.DECOMPOSE, visit_count=2)

        assert "returning" in prompt.lower()
        assert "new_category_discovered" in prompt
        assert "Existing" in prompt


# =============================================================================
# Integration Tests (require mocking Claude API)
# =============================================================================

class TestResearchAgentIntegration:
    """Integration tests for ResearchAgent with mocked Claude API."""

    @pytest.mark.asyncio
    async def test_full_phase_progression(self, research_agent, mock_journey_brief):
        """Test that agent can progress through all phases."""
        # This would require mocking the Claude API
        # For now, just verify structure is correct
        await research_agent.initialize(mock_journey_brief)

        # Simulate phase progression by setting flags
        research_agent.phase_context.question_tree_approved = True
        next_phase = research_agent._evaluate_transitions()
        assert next_phase == ResearchPhase.ANSWER

        research_agent.current_phase = ResearchPhase.ANSWER
        research_agent.phase_context.high_priority_complete = True
        next_phase = research_agent._evaluate_transitions()
        assert next_phase == ResearchPhase.RISE_ABOVE

        research_agent.current_phase = ResearchPhase.RISE_ABOVE
        research_agent.phase_context.insights_complete = True
        next_phase = research_agent._evaluate_transitions()
        assert next_phase == ResearchPhase.EXPAND

        research_agent.current_phase = ResearchPhase.EXPAND
        research_agent.phase_context.frontier_populated = True
        next_phase = research_agent._evaluate_transitions()
        assert next_phase == ResearchPhase.COMPLETE

    @pytest.mark.asyncio
    async def test_backward_transition_flow(self, research_agent, mock_journey_brief):
        """Test backward transition during answer phase."""
        await research_agent.initialize(mock_journey_brief)

        # Move to ANSWER phase
        research_agent.phase_context.question_tree_approved = True
        research_agent.current_phase = ResearchPhase.ANSWER
        research_agent.phase_context.increment_visit(ResearchPhase.ANSWER)

        # Trigger backward transition
        research_agent.phase_context.new_category_pending = "Security Considerations"

        next_phase = research_agent._evaluate_transitions()
        assert next_phase == ResearchPhase.DECOMPOSE

        # Verify it's marked as backward
        assert research_agent._is_backward_transition(
            ResearchPhase.ANSWER,
            ResearchPhase.DECOMPOSE,
        )
