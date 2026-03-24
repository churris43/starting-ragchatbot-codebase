"""Unit tests for CourseSearchTool.execute() — VectorStore is always mocked."""
from helpers import make_search_results


# ---------------------------------------------------------------------------
# Error and empty-result paths
# ---------------------------------------------------------------------------

def test_execute_returns_error_string(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = make_search_results(
        [], [], error="Search error: collection is empty"
    )
    result = course_search_tool.execute(query="python basics")
    assert result == "Search error: collection is empty"


def test_execute_no_results_message(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = make_search_results([], [])
    result = course_search_tool.execute(query="python basics")
    assert result.startswith("No relevant content found")


def test_execute_no_results_with_course_filter(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = make_search_results([], [])
    result = course_search_tool.execute(query="variables", course_name="MCP")
    assert result == "No relevant content found in course 'MCP'."


def test_execute_no_results_with_lesson_filter(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = make_search_results([], [])
    result = course_search_tool.execute(query="variables", lesson_number=3)
    assert result == "No relevant content found in lesson 3."


# ---------------------------------------------------------------------------
# Formatting and source-link generation
# ---------------------------------------------------------------------------

def test_execute_formats_document_content(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = make_search_results(
        ["Functions are reusable blocks of code."],
        [{"course_title": "Python 101", "lesson_number": 2}],
    )
    result = course_search_tool.execute(query="functions")
    assert "[Python 101 - Lesson 2]" in result
    assert "Functions are reusable blocks of code." in result


def test_execute_source_uses_lesson_link(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = make_search_results(
        ["Variables store data."],
        [{"course_title": "Python 101", "lesson_number": 1}],
    )
    mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"
    course_search_tool.execute(query="variables")
    assert 'href="https://example.com/lesson1"' in course_search_tool.last_sources[0]


def test_execute_source_falls_back_to_course_link(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = make_search_results(
        ["Variables store data."],
        [{"course_title": "Python 101", "lesson_number": 1}],
    )
    mock_vector_store.get_lesson_link.return_value = None
    mock_vector_store.get_course_link.return_value = "https://example.com/course"
    course_search_tool.execute(query="variables")
    assert 'href="https://example.com/course"' in course_search_tool.last_sources[0]


def test_execute_source_plain_label_when_no_link(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = make_search_results(
        ["Variables store data."],
        [{"course_title": "Python 101", "lesson_number": 1}],
    )
    mock_vector_store.get_lesson_link.return_value = None
    mock_vector_store.get_course_link.return_value = None
    course_search_tool.execute(query="variables")
    assert course_search_tool.last_sources[0] == "Python 101 - Lesson 1"


def test_execute_populates_last_sources_count(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = make_search_results(
        ["doc1", "doc2", "doc3"],
        [
            {"course_title": "A", "lesson_number": 1},
            {"course_title": "B", "lesson_number": 2},
            {"course_title": "C", "lesson_number": 3},
        ],
    )
    course_search_tool.execute(query="anything")
    assert len(course_search_tool.last_sources) == 3


# ---------------------------------------------------------------------------
# Argument forwarding
# ---------------------------------------------------------------------------

def test_execute_search_called_with_correct_args(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = make_search_results([], [])
    course_search_tool.execute(query="closures", course_name="Python 101", lesson_number=3)
    mock_vector_store.search.assert_called_once_with(
        query="closures",
        course_name="Python 101",
        lesson_number=3,
    )
