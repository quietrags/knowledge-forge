"""Tests for the API layer."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from server.api.main import app
from server.api.routes import journey, chat, session
from server.persistence import SessionStore


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
def client(temp_store):
    """Create a test client with temporary storage."""
    # Override the store in routes
    journey.store = temp_store
    chat.store = temp_store
    session.store = temp_store
    return TestClient(app)


class TestHealthEndpoints:
    """Test health and root endpoints."""

    def test_health_check(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root(self, client):
        """Test / endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["name"] == "Knowledge Forge API"


class TestJourneyEndpoints:
    """Test journey endpoints."""

    def test_analyze_build_question(self, client):
        """Test analyzing a build-style question."""
        response = client.post(
            "/api/journey/analyze",
            json={"question": "How do I write better prompts?"},
        )
        assert response.status_code == 200
        data = response.json()
        # /analyze returns brief directly per spec (camelCase)
        assert data["primaryMode"] == "build"
        assert data["answerType"] == "skill"

    def test_analyze_understand_question(self, client):
        """Test analyzing an understand-style question."""
        response = client.post(
            "/api/journey/analyze",
            json={"question": "Why do LLMs hallucinate?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["primaryMode"] == "understand"
        assert data["answerType"] == "understanding"

    def test_analyze_research_question(self, client):
        """Test analyzing a research-style question."""
        response = client.post(
            "/api/journey/analyze",
            json={"question": "What are the token limits for Claude models?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["primaryMode"] == "research"
        assert data["answerType"] == "facts"

    def test_analyze_empty_question(self, client):
        """Test that empty questions are rejected."""
        response = client.post(
            "/api/journey/analyze",
            json={"question": "   "},
        )
        assert response.status_code == 400

    def test_confirm_journey(self, client):
        """Test confirming a journey."""
        # First analyze - /analyze returns brief directly
        analyze_response = client.post(
            "/api/journey/analyze",
            json={"question": "How do I use LangChain?"},
        )
        brief = analyze_response.json()

        # Then confirm
        response = client.post(
            "/api/journey/confirm",
            json={"brief": brief, "confirmed": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["mode"] == "build"

    def test_confirm_with_alternative_mode(self, client):
        """Test confirming with an alternative mode."""
        # /analyze returns brief directly
        analyze_response = client.post(
            "/api/journey/analyze",
            json={"question": "How do I use LangChain?"},
        )
        brief = analyze_response.json()

        response = client.post(
            "/api/journey/confirm",
            json={
                "brief": brief,
                "confirmed": True,
                "alternative_mode": "research",
            },
        )
        assert response.status_code == 200
        assert response.json()["mode"] == "research"


class TestSessionEndpoints:
    """Test session endpoints."""

    def test_list_sessions_empty(self, client):
        """Test listing sessions when none exist."""
        response = client.get("/api/session")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_list_sessions_with_data(self, client, temp_store):
        """Test listing sessions with data."""
        # Create a session
        temp_store.create(mode="research")

        response = client.get("/api/session")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_get_session(self, client, temp_store):
        """Test getting a session by ID."""
        session = temp_store.create(mode="understand")

        response = client.get(f"/api/session/{session.id}")
        assert response.status_code == 200
        assert response.json()["mode"] == "understand"

    def test_get_session_not_found(self, client):
        """Test getting a nonexistent session."""
        response = client.get("/api/session/nonexistent-id")
        assert response.status_code == 404

    def test_save_session(self, client, temp_store):
        """Test saving a session."""
        session = temp_store.create(mode="build")

        response = client.post(f"/api/session/{session.id}/save", json={})
        assert response.status_code == 200
        assert response.json()["saved"] is True

    def test_delete_session(self, client, temp_store):
        """Test deleting a session."""
        session = temp_store.create(mode="research")

        response = client.delete(f"/api/session/{session.id}")
        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify it's gone
        response = client.get(f"/api/session/{session.id}")
        assert response.status_code == 404


class TestChatEndpoints:
    """Test chat endpoints."""

    def test_send_chat_message(self, client, temp_store):
        """Test sending a chat message."""
        session = temp_store.create(mode="research")

        response = client.post(
            "/api/chat",
            json={
                "session_id": session.id,
                "message": "What is prompt engineering?",
            },
        )
        assert response.status_code == 200
        assert response.json()["accepted"] is True

    def test_send_chat_message_not_found(self, client):
        """Test sending to nonexistent session."""
        response = client.post(
            "/api/chat",
            json={
                "session_id": "nonexistent-id",
                "message": "Hello",
            },
        )
        assert response.status_code == 404

    def test_send_empty_message(self, client, temp_store):
        """Test that empty messages are rejected."""
        session = temp_store.create(mode="research")

        response = client.post(
            "/api/chat",
            json={
                "session_id": session.id,
                "message": "   ",
            },
        )
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
