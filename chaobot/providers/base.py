"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class BaseProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, config: Any, provider_config: Any) -> None:
        """Initialize provider.

        Args:
            config: Application configuration
            provider_config: Provider-specific configuration
        """
        self.config = config
        self.provider_config = provider_config

    @abstractmethod
    async def complete(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Complete a conversation.

        Args:
            messages: List of messages

        Returns:
            Response dictionary with 'content' and optionally 'tool_calls'
        """
        pass

    @abstractmethod
    async def complete_stream(
        self,
        messages: list[dict[str, Any]]
    ) -> AsyncIterator[str]:
        """Complete a conversation with streaming.

        Args:
            messages: List of messages

        Yields:
            Chunks of response content
        """
        pass

    @abstractmethod
    def format_messages(
        self,
        messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Format messages for this provider.

        Args:
            messages: Generic messages

        Returns:
            Provider-specific formatted messages
        """
        pass

    def parse_response(self, response: Any) -> dict[str, Any]:
        """Parse provider response.

        Args:
            response: Raw provider response

        Returns:
            Standardized response dictionary
        """
        return {
            "content": str(response),
            "tool_calls": None
        }
