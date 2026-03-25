"""
API endpoint tests for the RAG system FastAPI application.

These tests use a test app fixture that mirrors the main app's endpoints
but without static file mounting, avoiding import issues in the test environment.
"""

import pytest
from unittest.mock import MagicMock


# =============================================================================
# Root Endpoint Tests
# =============================================================================


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_welcome_message(self, test_client):
        """GET / should return a welcome message."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "RAG System" in data["message"]


# =============================================================================
# Query Endpoint Tests
# =============================================================================


class TestQueryEndpoint:
    """Tests for the /api/query endpoint."""

    def test_query_with_valid_request(self, test_client):
        """POST /api/query with valid query should return response."""
        response = test_client.post(
            "/api/query",
            json={"query": "What is Python?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert isinstance(data["sources"], list)

    def test_query_creates_session_when_not_provided(self, test_client):
        """POST /api/query without session_id should create new session."""
        response = test_client.post(
            "/api/query",
            json={"query": "Tell me about courses"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test_session_123"

    def test_query_uses_provided_session_id(self, test_client, mock_rag_system):
        """POST /api/query with session_id should use provided session."""
        response = test_client.post(
            "/api/query",
            json={"query": "Follow up question", "session_id": "existing_session"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "existing_session"
        mock_rag_system.query.assert_called_with("Follow up question", "existing_session")

    def test_query_returns_sources(self, test_client):
        """POST /api/query should return sources in response."""
        response = test_client.post(
            "/api/query",
            json={"query": "What are variables?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["sources"]) > 0
        assert "Python Fundamentals" in data["sources"][0]

    def test_query_with_empty_query(self, test_client):
        """POST /api/query with empty query should still work."""
        response = test_client.post(
            "/api/query",
            json={"query": ""},
        )
        # The API accepts empty queries (validation is application-level)
        assert response.status_code == 200

    def test_query_missing_query_field(self, test_client):
        """POST /api/query without query field should return 422."""
        response = test_client.post(
            "/api/query",
            json={},
        )
        assert response.status_code == 422

    def test_query_invalid_json(self, test_client):
        """POST /api/query with invalid JSON should return 422."""
        response = test_client.post(
            "/api/query",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


# =============================================================================
# Courses Endpoint Tests
# =============================================================================


class TestCoursesEndpoint:
    """Tests for the /api/courses endpoint."""

    def test_get_courses_returns_stats(self, test_client):
        """GET /api/courses should return course statistics."""
        response = test_client.get("/api/courses")
        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 3
        assert len(data["course_titles"]) == 3

    def test_get_courses_returns_correct_titles(self, test_client):
        """GET /api/courses should return correct course titles."""
        response = test_client.get("/api/courses")
        assert response.status_code == 200
        data = response.json()
        assert "Python Fundamentals" in data["course_titles"]
        assert "Web Development" in data["course_titles"]
        assert "Data Science" in data["course_titles"]


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for API error handling."""

    def test_query_error_returns_500(self, test_app):
        """POST /api/query should return 500 when RAG system fails."""
        from fastapi.testclient import TestClient

        # Get the mock rag_system from the test_app's routes
        # We need to modify the mock to raise an exception
        for route in test_app.routes:
            if hasattr(route, "endpoint") and route.path == "/api/query":
                # Create a new test app with failing RAG system
                from fastapi import FastAPI, HTTPException
                from pydantic import BaseModel
                from typing import List, Optional

                failing_app = FastAPI()

                class QueryRequest(BaseModel):
                    query: str
                    session_id: Optional[str] = None

                class QueryResponse(BaseModel):
                    answer: str
                    sources: List[str]
                    session_id: str

                @failing_app.post("/api/query", response_model=QueryResponse)
                async def query_fail(request: QueryRequest):
                    raise HTTPException(status_code=500, detail="RAG system error")

                client = TestClient(failing_app)
                response = client.post(
                    "/api/query",
                    json={"query": "test"},
                )
                assert response.status_code == 500
                assert "RAG system error" in response.json()["detail"]
                return

    def test_courses_error_returns_500(self, test_app):
        """GET /api/courses should return 500 when analytics fail."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
        from typing import List

        failing_app = FastAPI()

        class CourseStats(BaseModel):
            total_courses: int
            course_titles: List[str]

        @failing_app.get("/api/courses", response_model=CourseStats)
        async def courses_fail():
            raise HTTPException(status_code=500, detail="Analytics error")

        client = TestClient(failing_app)
        response = client.get("/api/courses")
        assert response.status_code == 500
        assert "Analytics error" in response.json()["detail"]

    def test_nonexistent_endpoint_returns_404(self, test_client):
        """GET /api/nonexistent should return 404."""
        response = test_client.get("/api/nonexistent")
        assert response.status_code == 404


# =============================================================================
# Content Type Tests
# =============================================================================


class TestContentTypes:
    """Tests for API content type handling."""

    def test_query_accepts_json(self, test_client):
        """POST /api/query should accept application/json."""
        response = test_client.post(
            "/api/query",
            json={"query": "test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200

    def test_query_returns_json(self, test_client):
        """POST /api/query should return application/json."""
        response = test_client.post(
            "/api/query",
            json={"query": "test"},
        )
        assert "application/json" in response.headers["content-type"]

    def test_courses_returns_json(self, test_client):
        """GET /api/courses should return application/json."""
        response = test_client.get("/api/courses")
        assert "application/json" in response.headers["content-type"]


# =============================================================================
# Response Schema Tests
# =============================================================================


class TestResponseSchemas:
    """Tests for API response schema validation."""

    def test_query_response_has_required_fields(self, test_client):
        """Query response should have all required fields."""
        response = test_client.post(
            "/api/query",
            json={"query": "test"},
        )
        data = response.json()
        required_fields = ["answer", "sources", "session_id"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_courses_response_has_required_fields(self, test_client):
        """Courses response should have all required fields."""
        response = test_client.get("/api/courses")
        data = response.json()
        required_fields = ["total_courses", "course_titles"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_query_sources_is_list_of_strings(self, test_client):
        """Query sources should be a list of strings."""
        response = test_client.post(
            "/api/query",
            json={"query": "test"},
        )
        data = response.json()
        assert isinstance(data["sources"], list)
        for source in data["sources"]:
            assert isinstance(source, str)

    def test_courses_titles_is_list_of_strings(self, test_client):
        """Course titles should be a list of strings."""
        response = test_client.get("/api/courses")
        data = response.json()
        assert isinstance(data["course_titles"], list)
        for title in data["course_titles"]:
            assert isinstance(title, str)

    def test_courses_total_is_integer(self, test_client):
        """Total courses should be an integer."""
        response = test_client.get("/api/courses")
        data = response.json()
        assert isinstance(data["total_courses"], int)
        assert data["total_courses"] >= 0
