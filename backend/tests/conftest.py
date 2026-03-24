import pytest
from unittest.mock import MagicMock
from vector_store import VectorStore
from search_tools import CourseSearchTool
from models import Course, Lesson, CourseChunk


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
