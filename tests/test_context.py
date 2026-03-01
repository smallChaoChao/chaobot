"""Tests for context builder."""

import pytest
from pathlib import Path

from chaobot.agent.context import ContextBuilder
from chaobot.config.schema import Config


@pytest.fixture
def context_builder(tmp_path: Path) -> ContextBuilder:
    """Create a context builder with temporary config."""
    config = Config()
    config.config_path = tmp_path / "config.json"
    config.workspace_path = tmp_path / "workspace"
    return ContextBuilder(config)


def test_build_basic_context(context_builder: ContextBuilder) -> None:
    """Test building basic context."""
    messages = context_builder.build("Hello")

    # Should have system message and user message
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hello"


def test_build_with_history(context_builder: ContextBuilder) -> None:
    """Test building context with history."""
    history = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"}
    ]

    messages = context_builder.build("Follow up", history=history)

    # Should have system + history + current user message
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Previous question"
    assert messages[2]["role"] == "assistant"
    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == "Follow up"


def test_build_with_tools(context_builder: ContextBuilder) -> None:
    """Test building context with tools."""
    tools = [
        {"type": "function", "function": {"name": "test_tool"}}
    ]

    messages = context_builder.build("Use tool", tools=tools)

    # System message should have tools
    assert "tools" in messages[0]
    assert messages[0]["tools"] == tools


def test_filter_history_removes_system(context_builder: ContextBuilder) -> None:
    """Test that _filter_history removes system messages."""
    history = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "User message"},
        {"role": "assistant", "content": "Assistant response"}
    ]

    filtered = context_builder._filter_history(history)

    # System message should be removed
    assert len(filtered) == 2
    assert all(msg["role"] != "system" for msg in filtered)


def test_filter_history_truncates_long_messages(context_builder: ContextBuilder) -> None:
    """Test that long messages are truncated."""
    long_content = "x" * 10000
    history = [
        {"role": "assistant", "content": long_content}
    ]

    filtered = context_builder._filter_history(history)

    # Message should be truncated
    assert len(filtered[0]["content"]) < 10000
    assert "..." in filtered[0]["content"]


def test_filter_history_preserves_tool_calls(context_builder: ContextBuilder) -> None:
    """Test that tool call information is preserved."""
    history = [
        {
            "role": "assistant",
            "content": "Using tool",
            "tool_calls": [{"id": "call_123", "function": {"name": "test"}}]
        }
    ]

    filtered = context_builder._filter_history(history)

    assert len(filtered) == 1
    assert "tool_calls" in filtered[0]
