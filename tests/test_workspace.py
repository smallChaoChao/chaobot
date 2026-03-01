"""Tests for workspace file system."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from chaobot.agent.context import ContextBuilder
from chaobot.config.schema import Config


class TestWorkspaceFiles:
    """Test workspace file loading."""

    @pytest.fixture
    def config(self) -> Config:
        """Create test config."""
        return Config()

    def test_load_existing_soul_md(self, config: Config, tmp_path):
        """Test loading SOUL.md when it exists."""
        # Create a temporary workspace
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        soul_content = "# Test Soul\n\nTest behavioral guidelines."
        soul_file = workspace / "SOUL.md"
        soul_file.write_text(soul_content)
        
        # Create context builder with mocked workspace path
        builder = ContextBuilder(config)
        builder.workspace_dir = workspace
        
        loaded = builder._load_workspace_file("SOUL.md")
        assert loaded == soul_content

    def test_load_nonexistent_file(self, config: Config, tmp_path):
        """Test loading a file that doesn't exist."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        builder = ContextBuilder(config)
        builder.workspace_dir = workspace
        
        loaded = builder._load_workspace_file("NONEXISTENT.md")
        assert loaded is None

    def test_load_tools_md(self, config: Config, tmp_path):
        """Test loading TOOLS.md."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        tools_content = "# Test Tools\n\nTool guidelines."
        tools_file = workspace / "TOOLS.md"
        tools_file.write_text(tools_content)
        
        builder = ContextBuilder(config)
        builder.workspace_dir = workspace
        
        loaded = builder._load_workspace_file("TOOLS.md")
        assert loaded == tools_content

    def test_load_agents_md(self, config: Config, tmp_path):
        """Test loading AGENTS.md."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        agents_content = "# Test Agents\n\nAgent coordination."
        agents_file = workspace / "AGENTS.md"
        agents_file.write_text(agents_content)
        
        builder = ContextBuilder(config)
        builder.workspace_dir = workspace
        
        loaded = builder._load_workspace_file("AGENTS.md")
        assert loaded == agents_content

    def test_build_includes_workspace_files(self, config: Config, tmp_path):
        """Test that build() includes workspace files in system prompt."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        # Create workspace files
        (workspace / "SOUL.md").write_text("# Soul\nBehavior.")
        (workspace / "TOOLS.md").write_text("# Tools\nGuidelines.")
        (workspace / "AGENTS.md").write_text("# Agents\nCoordination.")
        
        builder = ContextBuilder(config)
        builder.workspace_dir = workspace
        
        messages = builder.build(user_message="Hello")
        
        # Check system message includes workspace content
        system_msg = messages[0]
        assert "Behavioral Guidelines" in system_msg["content"]
        assert "Tool Guidelines" in system_msg["content"]
        assert "Agent Coordination" in system_msg["content"]

    def test_build_without_workspace_files(self, config: Config, tmp_path):
        """Test that build() works without workspace files."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        builder = ContextBuilder(config)
        builder.workspace_dir = workspace
        
        messages = builder.build(user_message="Hello")
        
        # Should still work, just without extra sections
        system_msg = messages[0]
        assert "Behavioral Guidelines" not in system_msg["content"]
        assert "chaobot" in system_msg["content"].lower()


class TestWorkspaceStructure:
    """Test workspace directory structure."""

    @pytest.fixture
    def project_workspace(self):
        """Get project workspace directory."""
        # Use project directory workspace for tests
        return Path(__file__).parent.parent / "workspace"

    def test_workspace_directory_exists(self, project_workspace):
        """Test that workspace directory exists."""
        assert project_workspace.exists()

    def test_soul_md_exists(self, project_workspace):
        """Test that SOUL.md exists."""
        soul_file = project_workspace / "SOUL.md"
        assert soul_file.exists()

    def test_agents_md_exists(self, project_workspace):
        """Test that AGENTS.md exists."""
        agents_file = project_workspace / "AGENTS.md"
        assert agents_file.exists()

    def test_tools_md_exists(self, project_workspace):
        """Test that TOOLS.md exists."""
        tools_file = project_workspace / "TOOLS.md"
        assert tools_file.exists()

    def test_learnings_directory_exists(self, project_workspace):
        """Test that .learnings directory exists."""
        learnings_dir = project_workspace / ".learnings"
        assert learnings_dir.exists()

    def test_learnings_md_exists(self, project_workspace):
        """Test that LEARNINGS.md exists."""
        learnings_file = project_workspace / ".learnings" / "LEARNINGS.md"
        assert learnings_file.exists()

    def test_errors_md_exists(self, project_workspace):
        """Test that ERRORS.md exists."""
        errors_file = project_workspace / ".learnings" / "ERRORS.md"
        assert errors_file.exists()


class TestLearningsFormat:
    """Test learning record format."""

    @pytest.fixture
    def project_workspace(self):
        """Get project workspace directory."""
        return Path(__file__).parent.parent / "workspace"

    def test_learnings_template_structure(self, project_workspace):
        """Test that LEARNINGS.md has correct template structure."""
        learnings_file = project_workspace / ".learnings" / "LEARNINGS.md"
        content = learnings_file.read_text()
        
        # Check for required sections
        assert "## Learning Format" in content
        assert "**Logged**:" in content
        assert "**Priority**:" in content
        assert "**Status**:" in content
        assert "**Area**:" in content
        assert "### Summary" in content
        assert "### Details" in content
        assert "### Suggested Action" in content

    def test_errors_template_structure(self, project_workspace):
        """Test that ERRORS.md has correct template structure."""
        errors_file = project_workspace / ".learnings" / "ERRORS.md"
        content = errors_file.read_text()
        
        # Check for required sections
        assert "## Error Format" in content
        assert "**Occurred**:" in content
        assert "**Tool**:" in content
        assert "**Severity**:" in content
        assert "**Status**:" in content
        assert "### Error Message" in content
        assert "### Context" in content
        assert "### Root Cause" in content
        assert "### Resolution" in content

    def test_promotion_path_documented(self, project_workspace):
        """Test that promotion path is documented in LEARNINGS.md."""
        learnings_file = project_workspace / ".learnings" / "LEARNINGS.md"
        content = learnings_file.read_text()
        
        assert "## Promotion Path" in content
        assert "SOUL.md" in content
        assert "TOOLS.md" in content
        assert "AGENTS.md" in content
