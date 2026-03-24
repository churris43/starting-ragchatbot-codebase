"""Unit tests for AIGenerator — anthropic.Anthropic is always mocked."""
from unittest.mock import MagicMock, patch


def _make_text_block(text):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_tool_use_block(name, tool_id, input_dict):
    block = MagicMock()
    block.type = "tool_use"
    block.name = name
    block.id = tool_id
    block.input = input_dict
    return block


def _make_response(stop_reason, content_blocks):
    resp = MagicMock()
    resp.stop_reason = stop_reason
    resp.content = content_blocks
    return resp


# ---------------------------------------------------------------------------
# Direct (no-tool) response path
# ---------------------------------------------------------------------------

def test_direct_response_no_tools():
    with patch("ai_generator.anthropic.Anthropic") as MockAnthropic:
        client = MockAnthropic.return_value
        client.messages.create.return_value = _make_response(
            "end_turn", [_make_text_block("Paris is the capital of France.")]
        )
        from ai_generator import AIGenerator
        gen = AIGenerator(api_key="test", model="claude-test")
        result = gen.generate_response("What is the capital of France?")
        assert result == "Paris is the capital of France."


# ---------------------------------------------------------------------------
# Tool-use path — happy path
# ---------------------------------------------------------------------------

def test_tool_is_invoked_on_tool_use():
    with patch("ai_generator.anthropic.Anthropic") as MockAnthropic:
        client = MockAnthropic.return_value
        first_response = _make_response(
            "tool_use",
            [_make_tool_use_block("search_course_content", "tool_123", {"query": "python functions"})],
        )
        second_response = _make_response("end_turn", [_make_text_block("Functions are blocks of code.")])
        client.messages.create.side_effect = [first_response, second_response]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "Functions are reusable."

        from ai_generator import AIGenerator
        gen = AIGenerator(api_key="test", model="claude-test")
        gen.generate_response("Tell me about functions", tool_manager=tool_manager, tools=[{}])

        tool_manager.execute_tool.assert_called_once_with(
            "search_course_content", query="python functions"
        )


def test_tool_result_included_in_followup_messages():
    with patch("ai_generator.anthropic.Anthropic") as MockAnthropic:
        client = MockAnthropic.return_value
        first_response = _make_response(
            "tool_use",
            [_make_tool_use_block("search_course_content", "tool_abc", {"query": "closures"})],
        )
        second_response = _make_response("end_turn", [_make_text_block("Answer.")])
        client.messages.create.side_effect = [first_response, second_response]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "Closures capture their enclosing scope."

        from ai_generator import AIGenerator
        gen = AIGenerator(api_key="test", model="claude-test")
        gen.generate_response("What are closures?", tool_manager=tool_manager, tools=[{}])

        second_call_messages = client.messages.create.call_args_list[1][1]["messages"]
        tool_result_message = second_call_messages[-1]
        assert tool_result_message["role"] == "user"
        tool_result_block = tool_result_message["content"][0]
        assert tool_result_block["type"] == "tool_result"
        assert tool_result_block["tool_use_id"] == "tool_abc"
        assert tool_result_block["content"] == "Closures capture their enclosing scope."


def test_final_response_text_returned():
    with patch("ai_generator.anthropic.Anthropic") as MockAnthropic:
        client = MockAnthropic.return_value
        first_response = _make_response(
            "tool_use",
            [_make_tool_use_block("search_course_content", "tool_1", {"query": "loops"})],
        )
        second_response = _make_response("end_turn", [_make_text_block("Loops repeat code blocks.")])
        client.messages.create.side_effect = [first_response, second_response]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "For loops iterate over sequences."

        from ai_generator import AIGenerator
        gen = AIGenerator(api_key="test", model="claude-test")
        result = gen.generate_response("Explain loops", tool_manager=tool_manager, tools=[{}])
        assert result == "Loops repeat code blocks."


def test_no_tools_in_final_api_call():
    with patch("ai_generator.anthropic.Anthropic") as MockAnthropic:
        client = MockAnthropic.return_value
        first_response = _make_response(
            "tool_use",
            [_make_tool_use_block("search_course_content", "tool_1", {"query": "variables"})],
        )
        second_response = _make_response("end_turn", [_make_text_block("Done.")])
        client.messages.create.side_effect = [first_response, second_response]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "Variables store values."

        from ai_generator import AIGenerator
        gen = AIGenerator(api_key="test", model="claude-test")
        gen.generate_response("Variables?", tool_manager=tool_manager, tools=[{"name": "search"}])

        second_call_kwargs = client.messages.create.call_args_list[1][1]
        assert "tools" not in second_call_kwargs


def test_conversation_history_included_in_system_prompt():
    with patch("ai_generator.anthropic.Anthropic") as MockAnthropic:
        client = MockAnthropic.return_value
        client.messages.create.return_value = _make_response(
            "end_turn", [_make_text_block("Answer.")]
        )
        from ai_generator import AIGenerator
        gen = AIGenerator(api_key="test", model="claude-test")
        gen.generate_response("Follow-up question", conversation_history="User: hello\nAssistant: hi")

        system_arg = client.messages.create.call_args[1]["system"]
        assert "Previous conversation:" in system_arg
        assert "User: hello" in system_arg


# ---------------------------------------------------------------------------
# Bug A: uncaught exception when tool raises
# NOTE: These tests CONFIRM the bug exists (they pass on buggy code).
# After Fix A is applied, update assertions to expect graceful error strings.
# ---------------------------------------------------------------------------

def test_tool_exception_returns_graceful_response():
    """Fix A verified — tool exception is caught; Claude receives the error and replies gracefully."""
    with patch("ai_generator.anthropic.Anthropic") as MockAnthropic:
        client = MockAnthropic.return_value
        first_response = _make_response(
            "tool_use",
            [_make_tool_use_block("search_course_content", "tool_err", {"query": "crash"})],
        )
        fallback_response = _make_response("end_turn", [_make_text_block("Sorry, search is unavailable.")])
        client.messages.create.side_effect = [first_response, fallback_response]

        tool_manager = MagicMock()
        tool_manager.execute_tool.side_effect = RuntimeError("ChromaDB exploded")

        from ai_generator import AIGenerator
        gen = AIGenerator(api_key="test", model="claude-test")
        result = gen.generate_response("Crash query", tool_manager=tool_manager, tools=[{}])

        # Must not raise; the error is forwarded as a tool_result so Claude can respond
        assert isinstance(result, str)
        # Verify the tool_result message sent to Claude contained the error text
        second_call_messages = client.messages.create.call_args_list[1][1]["messages"]
        tool_result_block = second_call_messages[-1]["content"][0]
        assert "ChromaDB exploded" in tool_result_block["content"]


# ---------------------------------------------------------------------------
# Bug B: unguarded content[0].text access
# NOTE: These tests CONFIRM the bug exists.
# After Fix B is applied, update assertions to expect a fallback string.
# ---------------------------------------------------------------------------

def test_empty_content_list_returns_fallback():
    """Fix B verified — empty content list returns fallback string, not IndexError."""
    with patch("ai_generator.anthropic.Anthropic") as MockAnthropic:
        client = MockAnthropic.return_value
        client.messages.create.return_value = _make_response("end_turn", [])

        from ai_generator import AIGenerator
        gen = AIGenerator(api_key="test", model="claude-test")
        result = gen.generate_response("Hello")
        assert result == "I was unable to generate a response."


def test_non_text_content_block_returns_fallback():
    """Fix B verified — content[0] without .text returns fallback string, not AttributeError."""
    with patch("ai_generator.anthropic.Anthropic") as MockAnthropic:
        client = MockAnthropic.return_value
        no_text_block = MagicMock(spec=[])  # spec=[] means NO attributes
        client.messages.create.return_value = _make_response("end_turn", [no_text_block])

        from ai_generator import AIGenerator
        gen = AIGenerator(api_key="test", model="claude-test")
        result = gen.generate_response("Hello")
        assert result == "I was unable to generate a response."
