"""Tests for user confirmation mechanism."""

import pytest
from unittest.mock import AsyncMock, patch

from chaobot.agent.tools.confirmation import (
    ConfirmationManager,
    ConfirmationResult,
    console_confirmation_callback,
)


class TestConfirmationManager:
    """Test ConfirmationManager singleton."""

    def test_singleton_pattern(self):
        """Test that ConfirmationManager is a singleton."""
        manager1 = ConfirmationManager()
        manager2 = ConfirmationManager()
        assert manager1 is manager2

    def test_requires_confirmation_shell_dangerous(self):
        """Test that dangerous shell commands require confirmation."""
        manager = ConfirmationManager()
        
        dangerous_commands = [
            {"command": "rm -rf /"},
            {"command": "rm -fr /home"},
            {"command": "mkfs.ext4 /dev/sda1"},
            {"command": "dd if=/dev/zero of=/dev/sda"},
            {"command": "sudo rm -rf /tmp"},
        ]
        
        for args in dangerous_commands:
            assert manager.requires_confirmation("shell", args) is True, f"{args} should require confirmation"

    def test_requires_confirmation_shell_safe(self):
        """Test that safe shell commands don't require confirmation."""
        manager = ConfirmationManager()
        
        safe_commands = [
            {"command": "ls -la"},
            {"command": "echo hello"},
            {"command": "cat file.txt"},
        ]
        
        for args in safe_commands:
            assert manager.requires_confirmation("shell", args) is False, f"{args} should not require confirmation"

    def test_requires_confirmation_file_write_existing(self):
        """Test that writing to existing files requires confirmation."""
        manager = ConfirmationManager()
        
        # Mock file existence check
        with patch('os.path.exists', return_value=True):
            assert manager.requires_confirmation("file_write", {"path": "/existing/file.txt"}) is True

    def test_requires_confirmation_file_write_new(self):
        """Test that writing to new files doesn't require confirmation."""
        manager = ConfirmationManager()
        
        with patch('os.path.exists', return_value=False):
            assert manager.requires_confirmation("file_write", {"path": "/new/file.txt"}) is False

    def test_requires_confirmation_file_edit_existing(self):
        """Test that editing existing files requires confirmation."""
        manager = ConfirmationManager()
        
        with patch('os.path.exists', return_value=True):
            assert manager.requires_confirmation("file_edit", {"path": "/existing/file.txt"}) is True

    def test_requires_confirmation_other_tools(self):
        """Test that other tools don't require confirmation."""
        manager = ConfirmationManager()
        
        assert manager.requires_confirmation("file_read", {"path": "/any/file.txt"}) is False
        assert manager.requires_confirmation("web_search", {"query": "test"}) is False
        assert manager.requires_confirmation("browser_navigate", {"url": "https://example.com"}) is False

    @pytest.mark.asyncio
    async def test_confirm_no_callback_auto_approve(self):
        """Test that confirmation auto-approves when no callback set."""
        manager = ConfirmationManager()
        manager._callback = None
        
        # For non-dangerous operations
        result = await manager.confirm("file_read", {"path": "/test.txt"})
        assert result.approved is True

    @pytest.mark.asyncio
    async def test_confirm_with_callback(self):
        """Test confirmation with callback."""
        manager = ConfirmationManager()
        
        async def mock_callback(tool_name, arguments):
            return ConfirmationResult(approved=True, message="Approved")
        
        manager.set_callback(mock_callback)
        
        result = await manager.confirm("shell", {"command": "rm -rf /"})
        assert result.approved is True
        assert result.message == "Approved"

    @pytest.mark.asyncio
    async def test_confirm_callback_rejection(self):
        """Test confirmation rejection via callback."""
        manager = ConfirmationManager()
        
        async def mock_callback(tool_name, arguments):
            return ConfirmationResult(approved=False, message="Rejected")
        
        manager.set_callback(mock_callback)
        
        result = await manager.confirm("shell", {"command": "rm -rf /"})
        assert result.approved is False
        assert result.message == "Rejected"

    @pytest.mark.asyncio
    async def test_confirm_callback_exception(self):
        """Test confirmation when callback raises exception."""
        manager = ConfirmationManager()
        
        async def mock_callback(tool_name, arguments):
            raise Exception("Callback error")
        
        manager.set_callback(mock_callback)
        
        result = await manager.confirm("shell", {"command": "rm -rf /"})
        assert result.approved is False
        assert "Confirmation failed" in result.message


class TestConfirmationResult:
    """Test ConfirmationResult dataclass."""

    def test_result_creation(self):
        """Test creating a confirmation result."""
        result = ConfirmationResult(approved=True, message="Test message")
        
        assert result.approved is True
        assert result.message == "Test message"

    def test_result_defaults(self):
        """Test confirmation result defaults."""
        result = ConfirmationResult(approved=False)
        
        assert result.approved is False
        assert result.message == ""


class TestDangerousPatterns:
    """Test detection of dangerous command patterns."""

    def test_rm_rf_detection(self):
        """Test detection of rm -rf commands."""
        manager = ConfirmationManager()
        
        assert manager.requires_confirmation("shell", {"command": "rm -rf /"}) is True
        assert manager.requires_confirmation("shell", {"command": "rm -rf /home/user"}) is True
        assert manager.requires_confirmation("shell", {"command": "rm -rf *"}) is True

    def test_mkfs_detection(self):
        """Test detection of mkfs commands."""
        manager = ConfirmationManager()
        
        assert manager.requires_confirmation("shell", {"command": "mkfs /dev/sda1"}) is True
        assert manager.requires_confirmation("shell", {"command": "mkfs.ext4 /dev/sdb"}) is True

    def test_dd_detection(self):
        """Test detection of dd commands."""
        manager = ConfirmationManager()
        
        assert manager.requires_confirmation("shell", {"command": "dd if=/dev/zero of=/dev/sda"}) is True

    def test_sudo_detection(self):
        """Test detection of sudo commands."""
        manager = ConfirmationManager()
        
        assert manager.requires_confirmation("shell", {"command": "sudo apt update"}) is True
        assert manager.requires_confirmation("shell", {"command": "sudo rm -rf /tmp"}) is True

    def test_chmod_detection(self):
        """Test detection of dangerous chmod commands."""
        manager = ConfirmationManager()
        
        assert manager.requires_confirmation("shell", {"command": "chmod -R 777 /"}) is True

    def test_mv_detection(self):
        """Test detection of dangerous mv commands."""
        manager = ConfirmationManager()
        
        assert manager.requires_confirmation("shell", {"command": "mv /* /tmp"}) is True
        assert manager.requires_confirmation("shell", {"command": "mv / /tmp"}) is True

    def test_fork_bomb_detection(self):
        """Test detection of fork bomb."""
        manager = ConfirmationManager()
        
        assert manager.requires_confirmation("shell", {"command": ":(){ :|:& };:"}) is True
