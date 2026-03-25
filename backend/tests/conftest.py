import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from vector_store import VectorStore
from search_tools import CourseSearchTool
from models import Course, Lesson, CourseChunk


# =============================================================================
# Unit Test Fixtures (existing)
# =============================================================================


@pytest.fixture
def mock_vector_store():
    store = MagicMock(spec=VectorStore)
    store.get_lesson_link.return_value = None
    store.get_course_link.return_value = None
    return store


@pytest.fixture
def course_search_tool(mock_vector_store):
    return CourseSearchTool(mock_vector_store)


@pytest.fixture
def sample_course():
    return Course(
        title="Python Fundamentals",
        course_link="https://example.com/python",
        instructor="Jane Doe",
        lessons=[
            Lesson(lesson_number=1, title="Variables", lesson_link="https://example.com/python/1"),
            Lesson(lesson_number=2, title="Functions", lesson_link="https://example.com/python/2"),
        ],
    )


@pytest.fixture
def sample_chunks():
    return [
        CourseChunk(
            content="Lesson 1 content: Variables are containers for storing data values.",
            course_title="Python Fundamentals",
            lesson_number=1,
            chunk_index=0,
        ),
        CourseChunk(
            content="You can declare a variable by simply assigning a value to a name.",
            course_title="Python Fundamentals",
            lesson_number=1,
            chunk_index=1,
        ),
        CourseChunk(
            content="Lesson 2 content: Functions allow you to encapsulate reusable blocks of code.",
            course_title="Python Fundamentals",
            lesson_number=2,
            chunk_index=2,
        ),
    ]


@pytest.fixture
def real_vector_store(tmp_path):
    return VectorStore(
        chroma_path=str(tmp_path),
        embedding_model="all-MiniLM-L6-v2",
        max_results=5,
    )


# =============================================================================
# API Test Fixtures
# =============================================================================


@pytest.fixture
def mock_rag_system():
    """Create a mock RAG system for API tests."""
    mock = MagicMock()
    mock.session_manager = MagicMock()
    mock.session_manager.create_session.return_value = "test_session_123"
    mock.query.return_value = (
        "This is a test response about Python courses.",
        ["Python Fundamentals - Lesson 1: Variables"],
    )
    mock.get_course_analytics.return_value = {
        "total_courses": 3,
        "course_titles": ["Python Fundamentals", "Web Development", "Data Science"],
    }
    return mock


@pytest.fixture
def test_app(mock_rag_system):
    """
    Create a test FastAPI app without static file mounting.

    This avoids the issue where the main app.py tries to mount
    static files from a frontend directory that doesn't exist
    in the test environment.
    """
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Optional

    app = FastAPI(title="Course Materials RAG System - Test")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Use the mock RAG system
    rag_system = mock_rag_system

    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[str]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()
            answer, sources = rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    async def root():
        return {"message": "Course Materials RAG System API"}

    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the FastAPI test app."""
    from fastapi.testclient import TestClient
    return TestClient(test_app)


@pytest.fixture
async def async_test_client(test_app):
    """Create an async test client for async API tests."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
