"""Tests for the persistence layer."""

import tempfile
from pathlib import Path
import pytest

from server.persistence import (
    SessionStore,
    SessionNotFoundError,
    Session,
    JourneyDesignBrief,
    ResearchModeData,
    Question,
    CategoryQuestion,
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def store(temp_data_dir):
    """Create a session store with temporary storage."""
    return SessionStore(data_dir=temp_data_dir)


class TestSessionStore:
    """Tests for SessionStore CRUD operations."""

    def test_create_session(self, store):
        """Test creating a new session."""
        session = store.create(mode="research")

        assert session.id is not None
        assert session.mode == "research"
        assert session.research_data is not None
        assert session.created is not None
        assert session.updated is not None

    def test_create_session_with_brief(self, store):
        """Test creating a session with a journey brief."""
        brief = JourneyDesignBrief(
            original_question="How do I write better prompts?",
            ideal_answer="5 concrete techniques with examples",
            answer_type="skill",
            primary_mode="build",
            confirmation_message="You want to learn prompting techniques.",
        )

        session = store.create(journey_brief=brief, mode="build")

        assert session.journey_brief is not None
        assert session.journey_brief.original_question == "How do I write better prompts?"
        assert session.mode == "build"
        assert session.phase == "grounding"
        assert session.build_data is not None

    def test_get_session(self, store):
        """Test retrieving a session by ID."""
        created = store.create(mode="understand")
        retrieved = store.get(created.id)

        assert retrieved.id == created.id
        assert retrieved.mode == "understand"

    def test_get_nonexistent_session(self, store):
        """Test that getting a nonexistent session raises error."""
        with pytest.raises(SessionNotFoundError):
            store.get("nonexistent-id")

    def test_get_or_none(self, store):
        """Test get_or_none returns None for missing sessions."""
        result = store.get_or_none("nonexistent-id")
        assert result is None

    def test_save_session(self, store):
        """Test updating a session."""
        session = store.create(mode="research")
        original_updated = session.updated

        # Modify and save
        session.research_data = ResearchModeData(topic="Test Topic")
        saved = store.save(session)

        assert saved.research_data.topic == "Test Topic"
        assert saved.updated >= original_updated

    def test_delete_session(self, store):
        """Test deleting a session."""
        session = store.create(mode="research")

        assert store.exists(session.id)
        deleted = store.delete(session.id)
        assert deleted is True
        assert not store.exists(session.id)

    def test_delete_nonexistent(self, store):
        """Test deleting a nonexistent session returns False."""
        deleted = store.delete("nonexistent-id")
        assert deleted is False

    def test_list_sessions(self, store):
        """Test listing all sessions."""
        store.create(mode="research")
        store.create(mode="build")
        store.create(mode="understand")

        sessions = store.list()
        assert len(sessions) == 3

    def test_list_with_metadata(self, store):
        """Test listing sessions with metadata."""
        brief = JourneyDesignBrief(
            original_question="Test question for listing",
            ideal_answer="Test answer",
            answer_type="facts",
            primary_mode="research",
            confirmation_message="Test confirmation",
        )
        store.create(journey_brief=brief, mode="research")

        sessions = store.list_with_metadata()
        assert len(sessions) == 1
        assert sessions[0]["mode"] == "research"
        assert "Test question" in sessions[0]["topic"]


class TestSessionUpdates:
    """Tests for specific update operations."""

    def test_update_mode(self, store):
        """Test changing session mode."""
        session = store.create(mode="research")
        updated = store.update_mode(session.id, "build")

        assert updated.mode == "build"
        assert updated.build_data is not None
        assert updated.phase == "grounding"

    def test_update_phase(self, store):
        """Test changing build phase."""
        session = store.create(mode="build")
        updated = store.update_phase(session.id, "making")

        assert updated.phase == "making"

    def test_add_grounding_concept(self, store):
        """Test adding a grounding concept."""
        from server.persistence import GroundingConcept

        session = store.create(mode="build")
        concept = GroundingConcept(
            name="Context Window",
            distinction="Not memory, but attention span",
        )
        updated = store.add_grounding_concept(session.id, concept)

        assert len(updated.grounding_concepts) == 1
        assert updated.grounding_concepts[0].name == "Context Window"

    def test_mark_grounding_ready(self, store):
        """Test transitioning from grounding to making."""
        session = store.create(mode="build")
        updated = store.mark_grounding_ready(session.id)

        assert updated.grounding_ready is True
        assert updated.phase == "making"


class TestModeData:
    """Tests for mode-specific data persistence."""

    def test_research_data_persistence(self, store):
        """Test that research data persists correctly."""
        session = store.create(mode="research")

        # Add some research data
        session.research_data = ResearchModeData(
            topic="AI Agents",
            categories=[
                CategoryQuestion(
                    category="Architecture",
                    question_ids=["q1", "q2"],
                )
            ],
            questions=[
                Question(id="q1", question="What is ReACT?", status="open"),
                Question(id="q2", question="How do tools work?", status="answered"),
            ],
        )
        store.save(session)

        # Retrieve and verify
        retrieved = store.get(session.id)
        assert retrieved.research_data.topic == "AI Agents"
        assert len(retrieved.research_data.categories) == 1
        assert len(retrieved.research_data.questions) == 2
        assert retrieved.research_data.questions[1].status == "answered"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
