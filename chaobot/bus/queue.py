"""Message queue implementation using asyncio.Queue.

This follows nanobot's design for simplicity and clarity.
"""

import asyncio
from typing import Any

from rich.console import Console

from chaobot.bus.events import InboundMessage, OutboundMessage, AgentMessage

console = Console()


class MessageBus:
    """Message bus using asyncio.Queue for decoupled communication.
    
    This is the central hub for all message passing in the system.
    It decouples channels from agents using producer-consumer pattern.
    
    Example:
        bus = MessageBus()
        
        # Channel produces message
        await bus.inbound.put(InboundMessage(...))
        
        # Agent consumes message
        msg = await bus.inbound.get()
        
        # Agent produces response
        await bus.outbound.put(OutboundMessage(...))
        
        # Channel consumes response
        response = await bus.outbound.get()
    """
    
    def __init__(self) -> None:
        """Initialize the message bus with inbound and outbound queues."""
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()
        self._running = False
        
    async def start(self) -> None:
        """Start the message bus."""
        self._running = True
        console.print("[green]✅ Message bus started[/green]")
        
    async def stop(self) -> None:
        """Stop the message bus."""
        self._running = False
        console.print("[yellow]🛑 Message bus stopped[/yellow]")


# Global message bus instance
_bus: MessageBus | None = None


def get_bus() -> MessageBus:
    """Get the global message bus instance.
    
    Returns:
        The global MessageBus instance (creates one if needed)
    """
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus


def reset_bus() -> None:
    """Reset the global message bus (useful for testing)."""
    global _bus
    _bus = None
