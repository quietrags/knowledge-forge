"""Tests for the orchestrator module."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
import pytest_asyncio

from server.persistence import (
    SessionStore,
    JourneyDesignBrief,
    Session,
    GroundingConcept,
)
from server.orchestrator import (
    QuestionRouter,
    JourneyDesigner,
    PhaseManager,
    Orchestrator,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_store(temp_data_dir):
    """Create a session store with temporary storage."""
    return SessionStore(data_dir=temp_data_dir)


@pytest.fixture
def router():
    """Create a question router without LLM client."""
    return QuestionRouter(client=None)


@pytest.fixture
def phase_manager():
    """Create a phase manager."""
    return PhaseManager()


@pytest.fixture
def journey_designer(temp_store):
    """Create a journey designer with temp store."""
    return JourneyDesigner(store=temp_store)


@pytest.fixture
def orchestrator(temp_store):
    """Create an orchestrator with temp store."""
    return Orchestrator(store=temp_store)


# =============================================================================
# QuestionRouter Tests
# =============================================================================


class TestQuestionRouter:
    """Tests for the QuestionRouter class."""

    def test_route_build_questions(self, router):
        """Test routing build-style questions."""
        build_questions = [
            "How do I write better prompts?",
            "How can I implement caching?",
            "Help me create a React component",
            "Build me a login form",
            "Make a sorting algorithm",
        ]
        for question in build_questions:
            mode, answer_type = router.route_heuristic(question)
            assert mode == "build", f"Expected 'build' for: {question}"
            assert answer_type == "skill"

    def test_route_understand_questions(self, router):
        """Test routing understand-style questions."""
        understand_questions = [
            "Why do LLMs hallucinate?",
            "What's the difference between REST and GraphQL?",
            "How does garbage collection work?",
            "Explain polymorphism to me",
            "Why does this error happen?",
        ]
        for question in understand_questions:
            mode, answer_type = router.route_heuristic(question)
            assert mode == "understand", f"Expected 'understand' for: {question}"
            assert answer_type == "understanding"

    def test_route_research_questions(self, router):
        """Test routing research-style questions."""
        research_questions = [
            "What is the token limit for Claude?",
            "What are the best practices for error handling?",
            "What approaches exist for caching?",
            "Who created JavaScript?",
            "When was Python 3 released?",
        ]
        for question in research_questions:
            mode, answer_type = router.route_heuristic(question)
            assert mode == "research", f"Expected 'research' for: {question}"
            assert answer_type == "facts"

    def test_analyze_quick(self, router):
        """Test quick analysis returns proper JourneyDesignBrief."""
        brief = router.analyze_quick("How do I use async await?")

        assert isinstance(brief, JourneyDesignBrief)
        assert brief.original_question == "How do I use async await?"
        assert brief.primary_mode == "build"
        assert brief.answer_type == "skill"
        assert brief.confirmation_message is not None
        assert brief.ideal_answer is not None


# =============================================================================
# PhaseManager Tests
# =============================================================================


class TestPhaseManager:
    """Tests for the PhaseManager class."""

    def test_get_phase_build_session(self, phase_manager, temp_store):
        """Test getting phase for a build session."""
        session = temp_store.create(mode="build")
        session.phase = "grounding"

        phase = phase_manager.get_phase(session)
        assert phase == "grounding"

    def test_get_phase_non_build_session(self, phase_manager, temp_store):
        """Test getting phase for non-build session returns None."""
        session = temp_store.create(mode="research")

        phase = phase_manager.get_phase(session)
        assert phase is None

    def test_grounding_not_complete_initially(self, phase_manager, temp_store):
        """Test that grounding is not complete when session starts."""
        session = temp_store.create(mode="build")
        session.phase = "grounding"

        assert not phase_manager.is_grounding_complete(session)

    def test_grounding_complete_with_sufficient_concepts(self, phase_manager, temp_store):
        """Test grounding is complete with sufficient concepts."""
        session = temp_store.create(mode="build")
        session.phase = "grounding"

        # Add sufficient concepts
        for i in range(phase_manager.MIN_GROUNDING_CONCEPTS):
            concept = GroundingConcept(
                name=f"Concept {i}",
                distinction=f"Distinction {i}",
                sufficient=True,
            )
            session.grounding_concepts.append(concept)

        assert phase_manager.is_grounding_complete(session)

    def test_grounding_complete_when_marked_ready(self, phase_manager, temp_store):
        """Test grounding is complete when explicitly marked ready."""
        session = temp_store.create(mode="build")
        session.phase = "grounding"
        session.grounding_ready = True

        assert phase_manager.is_grounding_complete(session)

    def test_cannot_transition_without_grounding(self, phase_manager, temp_store):
        """Test cannot transition to making without grounding."""
        session = temp_store.create(mode="build")
        session.phase = "grounding"

        can_transition, reason = phase_manager.can_transition_to_making(session)
        assert not can_transition
        assert "not complete" in reason.lower()

    def test_add_grounding_concept(self, phase_manager, temp_store):
        """Test adding a grounding concept."""
        session = temp_store.create(mode="build")
        session.phase = "grounding"

        concept = phase_manager.add_grounding_concept(
            session,
            name="Concept",
            distinction="What makes it different",
            sufficient=True,
        )

        assert concept.name == "Concept"
        assert concept.distinction == "What makes it different"
        assert concept.sufficient is True
        assert len(session.grounding_concepts) == 1

    def test_mark_grounding_ready(self, phase_manager, temp_store):
        """Test marking grounding as ready."""
        session = temp_store.create(mode="build")
        session.phase = "grounding"

        result = phase_manager.mark_grounding_ready(session)
        assert result is True
        assert session.grounding_ready is True

    def test_mark_grounding_ready_wrong_mode(self, phase_manager, temp_store):
        """Test marking grounding ready fails for non-build mode."""
        session = temp_store.create(mode="research")

        result = phase_manager.mark_grounding_ready(session)
        assert result is False


@pytest.mark.asyncio
class TestPhaseManagerAsync:
    """Async tests for PhaseManager."""

    async def test_transition_to_making_success(self, phase_manager, temp_store):
        """Test successful transition to making phase."""
        session = temp_store.create(mode="build")
        session.phase = "grounding"
        session.grounding_ready = True

        result = await phase_manager.transition_to_making(session)

        assert result.transitioned is True
        assert result.from_phase == "grounding"
        assert result.to_phase == "making"
        assert session.phase == "making"

    async def test_transition_to_making_forced(self, phase_manager, temp_store):
        """Test forced transition to making phase."""
        session = temp_store.create(mode="build")
        session.phase = "grounding"

        result = await phase_manager.transition_to_making(session, force=True)

        assert result.transitioned is True
        assert session.phase == "making"

    async def test_transition_fails_without_grounding(self, phase_manager, temp_store):
        """Test transition fails without grounding complete."""
        session = temp_store.create(mode="build")
        session.phase = "grounding"

        result = await phase_manager.transition_to_making(session)

        assert result.transitioned is False
        assert session.phase == "grounding"


# =============================================================================
# JourneyDesigner Tests
# =============================================================================


class TestJourneyDesigner:
    """Tests for the JourneyDesigner class."""

    def test_initialize_research_session(self, journey_designer):
        """Test initializing a research session."""
        brief = JourneyDesignBrief(
            original_question="What is caching?",
            ideal_answer="Clear explanation of caching",
            answer_type="facts",
            primary_mode="research",
            confirmation_message="Let's research caching.",
        )

        session = journey_designer.initialize_session(brief)

        assert session.mode == "research"
        assert session.research_data is not None
        assert session.research_data.topic == "What is caching?"

    def test_initialize_understand_session(self, journey_designer):
        """Test initializing an understand session."""
        brief = JourneyDesignBrief(
            original_question="Why do databases use indexes?",
            ideal_answer="Mental model for database indexes",
            answer_type="understanding",
            primary_mode="understand",
            confirmation_message="Let's understand indexes.",
        )

        session = journey_designer.initialize_session(brief)

        assert session.mode == "understand"
        assert session.understand_data is not None

    def test_initialize_build_session(self, journey_designer):
        """Test initializing a build session."""
        brief = JourneyDesignBrief(
            original_question="How do I build a REST API?",
            ideal_answer="Step by step API building guide",
            answer_type="skill",
            primary_mode="build",
            confirmation_message="Let's build an API.",
        )

        session = journey_designer.initialize_session(brief)

        assert session.mode == "build"
        assert session.phase == "grounding"
        assert session.build_data is not None
        assert session.grounding_ready is False

    def test_initialize_with_alternative_mode(self, journey_designer):
        """Test initializing with an alternative mode."""
        brief = JourneyDesignBrief(
            original_question="How do I use Redis?",
            ideal_answer="Redis usage guide",
            answer_type="skill",
            primary_mode="build",
            confirmation_message="Let's build with Redis.",
        )

        session = journey_designer.initialize_session(brief, mode="research")

        assert session.mode == "research"
        assert session.research_data is not None


# =============================================================================
# Orchestrator Tests
# =============================================================================


class TestOrchestrator:
    """Tests for the Orchestrator class."""

    def test_analyze_question_sync(self, orchestrator):
        """Test synchronous question analysis."""
        brief = orchestrator.analyze_question_sync("How do I write tests?")

        assert brief.primary_mode == "build"
        assert brief.answer_type == "skill"

    def test_get_session(self, orchestrator, temp_store):
        """Test getting a session."""
        session = temp_store.create(mode="research")

        retrieved = orchestrator.get_session(session.id)
        assert retrieved is not None
        assert retrieved.id == session.id

    def test_get_session_not_found(self, orchestrator):
        """Test getting non-existent session returns None."""
        retrieved = orchestrator.get_session("nonexistent-id")
        assert retrieved is None


@pytest.mark.asyncio
class TestOrchestratorAsync:
    """Async tests for Orchestrator."""

    async def test_analyze_question_uses_heuristics_without_llm(self, orchestrator):
        """Test question analysis falls back to heuristics."""
        brief = await orchestrator.analyze_question(
            "How do I implement caching?",
            use_llm=False,
        )

        assert brief.primary_mode == "build"
        assert brief.answer_type == "skill"

    async def test_initialize_journey(self, orchestrator):
        """Test journey initialization."""
        brief = JourneyDesignBrief(
            original_question="How do I use Docker?",
            ideal_answer="Docker usage guide",
            answer_type="skill",
            primary_mode="build",
            confirmation_message="Let's build with Docker.",
        )

        session = await orchestrator.initialize_journey(brief)

        assert session is not None
        assert session.mode == "build"
        assert session.journey_brief is not None

    async def test_initialize_journey_with_alternative_mode(self, orchestrator):
        """Test journey initialization with alternative mode."""
        brief = JourneyDesignBrief(
            original_question="How do I use Docker?",
            ideal_answer="Docker usage guide",
            answer_type="skill",
            primary_mode="build",
            confirmation_message="Let's build with Docker.",
        )

        session = await orchestrator.initialize_journey(brief, alternative_mode="research")

        assert session.mode == "research"

    async def test_transition_to_making(self, orchestrator, temp_store):
        """Test phase transition through orchestrator."""
        brief = JourneyDesignBrief(
            original_question="How do I use async?",
            ideal_answer="Async guide",
            answer_type="skill",
            primary_mode="build",
            confirmation_message="Let's build async.",
        )

        session = await orchestrator.initialize_journey(brief)
        orchestrator.mark_grounding_ready(session)

        result = await orchestrator.transition_to_making(session)
        assert result is True

        # Verify persistence
        saved_session = orchestrator.get_session(session.id)
        assert saved_session.phase == "making"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
