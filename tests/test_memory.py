"""Tests for memory management."""

import json
import pytest
from pathlib import Path

from chaobot.agent.memory import MemoryManager
from chaobot.config.schema import Config


@pytest.fixture
def memory_manager(tmp_path: Path) -> MemoryManager:
    """Create a memory manager with temporary directory."""
    config = Config()
    config.config_path = tmp_path / "config.json"
    config.workspace_path = tmp_path / "workspace"
    return MemoryManager(config)


@pytest.mark.asyncio
async def test_save_and_load_history(memory_manager: MemoryManager) -> None:
    """Test saving and loading conversation history."""
    session_id = "test_session"
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]

    # Save history
    await memory_manager.save_history(session_id, messages)

    # Load history
    loaded = await memory_manager.load_history(session_id)

    assert len(loaded) == 2
    assert loaded[0]["role"] == "user"
    assert loaded[0]["content"] == "Hello"
    assert loaded[1]["role"] == "assistant"
    assert loaded[1]["content"] == "Hi there!"


@pytest.mark.asyncio
async def test_load_nonexistent_session(memory_manager: MemoryManager) -> None:
    """Test loading history for non-existent session."""
    loaded = await memory_manager.load_history("nonexistent")
    assert loaded == []


@pytest.mark.asyncio
async def test_clear_history(memory_manager: MemoryManager) -> None:
    """Test clearing conversation history."""
    session_id = "test_session"
    messages = [{"role": "user", "content": "Hello"}]

    # Save and verify
    await memory_manager.save_history(session_id, messages)
    loaded = await memory_manager.load_history(session_id)
    assert len(loaded) == 1

    # Clear and verify
    await memory_manager.clear_history(session_id)
    loaded = await memory_manager.load_history(session_id)
    assert loaded == []


@pytest.mark.asyncio
async def test_history_limit(memory_manager: MemoryManager) -> None:
    """Test that history is limited to 100 messages."""
    session_id = "test_session"
    messages = [{"role": "user", "content": f"Message {i}"} for i in range(150)]

    await memory_manager.save_history(session_id, messages)
    loaded = await memory_manager.load_history(session_id)

    # Should only keep last 100 messages
    assert len(loaded) == 100


@pytest.mark.asyncio
async def test_get_all_sessions(memory_manager: MemoryManager) -> None:
    """Test getting all session IDs."""
    # Create multiple sessions
    await memory_manager.save_history("session1", [{"role": "user", "content": "Hello"}])
    await memory_manager.save_history("session2", [{"role": "user", "content": "Hi"}])

    sessions = memory_manager.get_all_sessions()

    assert len(sessions) == 2
    assert "session1" in sessions
    assert "session2" in sessions


def test_memory_files_created(memory_manager: MemoryManager) -> None:
    """Test that MEMORY.md and HISTORY.md are created."""
    memory_file = memory_manager.get_memory_file_path()
    history_file = memory_manager.get_history_file_path()

    assert memory_file.exists()
    assert history_file.exists()

    # Check content
    memory_content = memory_file.read_text()
    assert "# Long-term Memory" in memory_content

    history_content = history_file.read_text()
    assert "# Conversation History" in history_content


@pytest.mark.asyncio
async def test_jsonl_format(memory_manager: MemoryManager) -> None:
    """Test that history is saved in JSONL format."""
    session_id = "test_session"
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"}
    ]

    await memory_manager.save_history(session_id, messages)

    # Read raw file
    session_file = memory_manager.sessions_dir / f"{session_id}.jsonl"
    lines = session_file.read_text().strip().split("\n")

    # First line should be metadata
    metadata = json.loads(lines[0])
    assert metadata["_type"] == "metadata"
    assert metadata["key"] == f"cli:{session_id}"

    # Subsequent lines should be messages
    msg1 = json.loads(lines[1])
    assert msg1["role"] == "user"
    assert msg1["content"] == "Hello"
