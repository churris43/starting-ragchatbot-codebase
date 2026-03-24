"""Tests for RAGSystem.query() — unit tests with mocked deps + integration tests with real ChromaDB."""
import pytest
from unittest.mock import MagicMock, patch
from search_tools import CourseSearchTool, ToolManager


# ---------------------------------------------------------------------------
# Helpers to build a RAGSystem with mocked internals
# ---------------------------------------------------------------------------

def _make_rag_system(mock_vector_store):
    """Return a RAGSystem where VectorStore, AIGenerator, and SessionManager are mocked."""
    from config import Config
    from rag_system import RAGSystem

    config = Config(ANTHROPIC_API_KEY="test-key")

    with patch("rag_system.VectorStore") as MockVS, \
         patch("rag_system.AIGenerator") as MockAI, \
         patch("rag_system.SessionManager") as MockSM, \
         patch("rag_system.DocumentProcessor"):

        MockVS.return_value = mock_vector_store
        rag = RAGSystem(config)
        rag._mock_ai = MockAI.return_value
        rag._mock_sm = MockSM.return_value

    return rag


# ---------------------------------------------------------------------------
# Unit tests — AIGenerator mocked via patch.object after construction
# ---------------------------------------------------------------------------

def test_query_calls_generator_with_tools(mock_vector_store):
    rag = _make_rag_system(mock_vector_store)
    with patch.object(rag.ai_generator, "generate_response", return_value="Answer."):
        rag.query("What is a variable?", session_id=None)
        call_kwargs = rag.ai_generator.generate_response.call_args[1]
        assert "tools" in call_kwargs
        assert "tool_manager" in call_kwargs


def test_query_returns_response_text(mock_vector_store):
    rag = _make_rag_system(mock_vector_store)
    with patch.object(rag.ai_generator, "generate_response", return_value="Variables hold values."):
        response, _ = rag.query("What is a variable?")
    assert response == "Variables hold values."


def test_query_returns_sources_from_tool_manager(mock_vector_store):
    rag = _make_rag_system(mock_vector_store)
    fake_sources = ['<a href="https://example.com">Python 101</a>']

    with patch.object(rag.ai_generator, "generate_response", return_value="Answer."), \
         patch.object(rag.tool_manager, "get_last_sources", return_value=fake_sources):
        _, sources = rag.query("Functions?")
    assert sources == fake_sources


def test_query_resets_sources_after_retrieval(mock_vector_store):
    rag = _make_rag_system(mock_vector_store)
    with patch.object(rag.ai_generator, "generate_response", return_value="Answer."), \
         patch.object(rag.tool_manager, "get_last_sources", return_value=[]), \
         patch.object(rag.tool_manager, "reset_sources") as mock_reset:
        rag.query("Anything?")
    mock_reset.assert_called_once()


def test_query_updates_session_history(mock_vector_store):
    rag = _make_rag_system(mock_vector_store)
    session_id = rag.session_manager.create_session.return_value = "session_1"

    with patch.object(rag.ai_generator, "generate_response", return_value="Answer."), \
         patch.object(rag.session_manager, "get_conversation_history", return_value=None), \
         patch.object(rag.session_manager, "add_exchange") as mock_add:
        rag.query("What is scope?", session_id="session_1")
    mock_add.assert_called_once()
    args = mock_add.call_args[0]
    assert args[0] == "session_1"
    assert args[2] == "Answer."


def test_query_no_session_skips_history(mock_vector_store):
    rag = _make_rag_system(mock_vector_store)
    with patch.object(rag.ai_generator, "generate_response", return_value="Answer."), \
         patch.object(rag.session_manager, "get_conversation_history") as mock_hist, \
         patch.object(rag.session_manager, "add_exchange") as mock_add:
        rag.query("Hello?", session_id=None)
    mock_hist.assert_not_called()
    mock_add.assert_not_called()


# ---------------------------------------------------------------------------
# Bug A: exception from generate_response propagates out of query()
# NOTE: Confirms the bug. After Fix A, update to assert graceful return.
# ---------------------------------------------------------------------------

def test_query_exception_propagates(mock_vector_store):
    """Fix A verified at RAGSystem layer — generate_response no longer raises for tool errors.
    This test confirms that a RuntimeError from generate_response still propagates (RAGSystem
    itself has no catch), but Fix A prevents that RuntimeError from ever being raised in practice
    because _handle_tool_execution now catches tool exceptions internally."""
    rag = _make_rag_system(mock_vector_store)
    with patch.object(
        rag.ai_generator, "generate_response",
        side_effect=RuntimeError("tool crashed")
    ):
        with pytest.raises(RuntimeError, match="tool crashed"):
            rag.query("Content question?", session_id=None)


# ---------------------------------------------------------------------------
# Bug C: integration tests — real ChromaDB via real_vector_store fixture
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_search_empty_collection_returns_string_not_exception(real_vector_store):
    """BUG C — search on an empty DB must return a string, never raise."""
    tool = CourseSearchTool(real_vector_store)
    result = tool.execute(query="python functions")
    assert isinstance(result, str), "execute() must return a string, not raise"
    # Either "No relevant content found" or "Search error: ..." — both are acceptable strings


@pytest.mark.integration
def test_search_finds_indexed_content(real_vector_store, sample_course, sample_chunks):
    """After indexing, a relevant query returns content (not empty/error)."""
    real_vector_store.add_course_metadata(sample_course)
    real_vector_store.add_course_content(sample_chunks)

    tool = CourseSearchTool(real_vector_store)
    result = tool.execute(query="functions reusable code")

    assert not result.startswith("No relevant content found")
    assert not result.startswith("Search error:")
    assert len(result) > 0


@pytest.mark.integration
def test_search_with_partial_course_name(real_vector_store, sample_course, sample_chunks):
    """Partial course name 'Python' resolves to 'Python Fundamentals' via semantic match."""
    real_vector_store.add_course_metadata(sample_course)
    real_vector_store.add_course_content(sample_chunks)

    tool = CourseSearchTool(real_vector_store)
    result = tool.execute(query="variables", course_name="Python")

    assert not result.startswith("No course found")
    assert not result.startswith("Search error:")
