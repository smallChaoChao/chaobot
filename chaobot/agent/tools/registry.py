"""Tool registry for managing available tools."""

from typing import Any

from chaobot.agent.tools.base import BaseTool, ToolResult
from chaobot.agent.tools.shell import ShellTool
from chaobot.agent.tools.file import FileReadTool, FileWriteTool, FileEditTool
from chaobot.agent.tools.web import WebSearchTool, WebFetchTool
from chaobot.agent.tools.browser import (
    BrowserNavigateTool, BrowserClickTool, BrowserInputTool,
    BrowserScreenshotTool, BrowserGetHtmlTool, BrowserScrollTool,
    BrowserFindElementTool
)
from chaobot.config.schema import Config


class ToolRegistry:
    """Registry for agent tools."""

    def __init__(self, config: Config) -> None:
        """Initialize tool registry.

        Args:
            config: Application configuration
        """
        self.config = config
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register default tools.

        NOTE: Only core, fundamental tools should be registered here.
        Specific capabilities like weather queries should be implemented as Skills,
        not as core Tools. Skills use these core Tools to accomplish their tasks.
        """
        tools = [
            ShellTool(self.config),
            FileReadTool(self.config),
            FileWriteTool(self.config),
            FileEditTool(self.config),
            WebSearchTool(self.config),
            WebFetchTool(self.config),
            # Browser automation tools (Phase 3)
            BrowserNavigateTool(self.config),
            BrowserClickTool(self.config),
            BrowserInputTool(self.config),
            BrowserScreenshotTool(self.config),
            BrowserGetHtmlTool(self.config),
            BrowserScrollTool(self.config),
            BrowserFindElementTool(self.config),
        ]

        for tool in tools:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        """Register a tool.

        Args:
            tool: Tool instance
        """
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool | None:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None
        """
        return self._tools.get(name)

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions for LLM.

        Returns:
            List of tool definitions
        """
        return [tool.get_definition() for tool in self._tools.values()]

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        return await tool.execute(**arguments)

    def list_tools(self) -> list[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())
