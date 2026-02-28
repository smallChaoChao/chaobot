"""Base tool interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """Result of tool execution."""

    success: bool
    content: str
    data: dict[str, Any] | None = None


class BaseTool(ABC):
    """Base class for tools."""

    name: str
    description: str
    parameters: dict[str, Any]

    def __init__(self, config: Any) -> None:
        """Initialize tool.

        Args:
            config: Application configuration
        """
        self.config = config

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool execution result
        """
        pass

    def get_definition(self) -> dict[str, Any]:
        """Get tool definition for LLM.

        Returns:
            Tool definition dictionary
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
