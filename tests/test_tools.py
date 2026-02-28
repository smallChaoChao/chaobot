"""Tests for tools."""

import pytest

from chaobot.agent.tools.base import ToolResult
from chaobot.agent.tools.shell import ShellTool
from chaobot.agent.tools.file import FileReadTool, FileWriteTool
from chaobot.config.schema import Config


@pytest.fixture
def config() -> Config:
    """Create test config."""
    return Config()


@pytest.mark.asyncio
async def test_shell_tool_echo(config: Config) -> None:
    """Test shell tool with echo command."""
    tool = ShellTool(config)
    result = await tool.execute(command="echo hello")

    assert result.success is True
    assert "hello" in result.content


@pytest.mark.asyncio
async def test_shell_tool_timeout(config: Config) -> None:
    """Test shell tool timeout."""
    tool = ShellTool(config)
    result = await tool.execute(command="sleep 10", timeout=1)

    assert result.success is False
    assert "timed out" in result.content.lower()


@pytest.mark.asyncio
async def test_shell_tool_no_command(config: Config) -> None:
    """Test shell tool with no command."""
    tool = ShellTool(config)
    result = await tool.execute(command="")

    assert result.success is False
    assert "No command" in result.content


@pytest.mark.asyncio
async def test_file_read_tool(tmp_path, config: Config) -> None:
    """Test file read tool."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    tool = FileReadTool(config)
    result = await tool.execute(path=str(test_file))

    assert result.success is True
    assert "Hello, World!" in result.content


@pytest.mark.asyncio
async def test_file_read_tool_not_found(config: Config) -> None:
    """Test file read tool with non-existent file."""
    tool = FileReadTool(config)
    result = await tool.execute(path="/nonexistent/file.txt")

    assert result.success is False
    assert "not found" in result.content.lower() or "No such file" in result.content


@pytest.mark.asyncio
async def test_file_write_tool(tmp_path, config: Config) -> None:
    """Test file write tool."""
    test_file = tmp_path / "output.txt"

    tool = FileWriteTool(config)
    result = await tool.execute(
        path=str(test_file),
        content="Test content"
    )

    assert result.success is True
    assert test_file.exists()
    assert test_file.read_text() == "Test content"


@pytest.mark.asyncio
async def test_file_write_tool_no_content(tmp_path, config: Config) -> None:
    """Test file write tool with no content."""
    test_file = tmp_path / "empty.txt"

    tool = FileWriteTool(config)
    result = await tool.execute(path=str(test_file), content="")

    assert result.success is True
    assert test_file.exists()
    assert test_file.read_text() == ""


def test_tool_result_success() -> None:
    """Test ToolResult success case."""
    result = ToolResult(success=True, content="Success message")
    assert result.success is True
    assert result.content == "Success message"
    assert result.data is None


def test_tool_result_failure() -> None:
    """Test ToolResult failure case."""
    result = ToolResult(success=False, content="Error message", data={"error": "details"})
    assert result.success is False
    assert result.content == "Error message"
    assert result.data == {"error": "details"}
