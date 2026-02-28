"""File operation tools."""

from pathlib import Path
from typing import Any

from chaobot.agent.tools.base import BaseTool, ToolResult


class FileReadTool(BaseTool):
    """Read file contents."""

    name = "file_read"
    description = "Read the contents of a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read"
            },
            "offset": {
                "type": "integer",
                "description": "Line offset to start reading from",
                "default": 1
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of lines to read",
                "default": 200
            }
        },
        "required": ["path"]
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Read file.

        Args:
            **kwargs: Must contain 'path', optionally 'offset' and 'limit'

        Returns:
            Tool execution result
        """
        path = kwargs.get("path", "")
        offset = kwargs.get("offset", 1)
        limit = kwargs.get("limit", 200)

        try:
            file_path = Path(path).expanduser().resolve()

            # Security check: prevent path traversal
            if self.config.tools.restrict_to_workspace:
                workspace = self.config.workspace_path.resolve()
                try:
                    # Use relative_to to properly check if path is within workspace
                    file_path.relative_to(workspace)
                except ValueError:
                    return ToolResult(
                        success=False,
                        content=f"Access denied: {path} is outside workspace"
                    )

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    content=f"File not found: {path}"
                )

            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    content=f"Not a file: {path}"
                )

            # Read file
            with open(file_path) as f:
                lines = f.readlines()

            # Apply offset and limit
            start = max(0, offset - 1)
            end = min(len(lines), start + limit)
            selected_lines = lines[start:end]

            content = "".join(selected_lines)

            # Add indicator if truncated
            if end < len(lines):
                content += f"\n... ({len(lines) - end} more lines)"

            return ToolResult(
                success=True,
                content=content,
                data={
                    "total_lines": len(lines),
                    "shown_lines": len(selected_lines),
                    "offset": offset
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Error reading file: {e}"
            )


class FileWriteTool(BaseTool):
    """Write to a file."""

    name = "file_write"
    description = "Write content to a file (creates or overwrites)"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write"
            }
        },
        "required": ["path", "content"]
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Write file.

        Args:
            **kwargs: Must contain 'path' and 'content'

        Returns:
            Tool execution result
        """
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")

        try:
            file_path = Path(path).expanduser().resolve()

            # Security check: prevent path traversal
            if self.config.tools.restrict_to_workspace:
                workspace = self.config.workspace_path.resolve()
                try:
                    file_path.relative_to(workspace)
                except ValueError:
                    return ToolResult(
                        success=False,
                        content=f"Access denied: {path} is outside workspace"
                    )

            # Create parent directories (only within workspace)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w") as f:
                f.write(content)

            return ToolResult(
                success=True,
                content=f"Successfully wrote to {path}"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Error writing file: {e}"
            )


class FileEditTool(BaseTool):
    """Edit a file using search/replace."""

    name = "file_edit"
    description = "Edit a file by searching for text and replacing it"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to edit"
            },
            "old_string": {
                "type": "string",
                "description": "Text to search for"
            },
            "new_string": {
                "type": "string",
                "description": "Text to replace with"
            }
        },
        "required": ["path", "old_string", "new_string"]
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Edit file.

        Args:
            **kwargs: Must contain 'path', 'old_string', and 'new_string'

        Returns:
            Tool execution result
        """
        path = kwargs.get("path", "")
        old_string = kwargs.get("old_string", "")
        new_string = kwargs.get("new_string", "")

        try:
            file_path = Path(path).expanduser().resolve()

            # Security check: prevent path traversal
            if self.config.tools.restrict_to_workspace:
                workspace = self.config.workspace_path.resolve()
                try:
                    file_path.relative_to(workspace)
                except ValueError:
                    return ToolResult(
                        success=False,
                        content=f"Access denied: {path} is outside workspace"
                    )

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    content=f"File not found: {path}"
                )

            with open(file_path) as f:
                content = f.read()

            if old_string not in content:
                return ToolResult(
                    success=False,
                    content=f"Could not find the text to replace in {path}"
                )

            new_content = content.replace(old_string, new_string, 1)

            with open(file_path, "w") as f:
                f.write(new_content)

            return ToolResult(
                success=True,
                content=f"Successfully edited {path}"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Error editing file: {e}"
            )
