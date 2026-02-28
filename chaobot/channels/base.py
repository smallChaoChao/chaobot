"""Base channel interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseChannel(ABC):
    """Base class for chat channels."""

    name: str

    def __init__(self, config: Any) -> None:
        """Initialize channel.

        Args:
            config: Channel configuration
        """
        self.config = config

    @abstractmethod
    async def start(self) -> None:
        """Start the channel."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel."""
        pass

    @abstractmethod
    async def send_message(self, to: str, message: str) -> None:
        """Send a message.

        Args:
            to: Recipient identifier
            message: Message content
        """
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if channel is enabled.

        Returns:
            True if enabled
        """
        pass
