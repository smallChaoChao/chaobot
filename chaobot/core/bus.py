"""Message bus for decoupled communication between channels and agents.

This module implements a message bus pattern similar to nanobot but with improvements:
- Type-safe message definitions
- Async/await support
- Pluggable handlers
- Message routing and filtering
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine

from rich.console import Console

console = Console()


@dataclass
class Message:
    """Base message class.
    
    All messages in the system should inherit from this class.
    """
    id: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InboundMessage(Message):
    """Message received from external channels (Feishu, Discord, etc.).
    
    Attributes:
        channel: Channel name (e.g., "feishu", "discord")
        sender_id: Unique sender identifier
        chat_id: Chat/room identifier
        content: Text content
        media: List of media file paths
        raw_data: Original raw data from the channel
    """
    channel: str
    sender_id: str
    chat_id: str
    content: str
    media: list[str] = field(default_factory=list)
    raw_data: Any = None


@dataclass
class OutboundMessage(Message):
    """Message to be sent to external channels.
    
    Attributes:
        channel: Target channel name
        recipient_id: Recipient identifier (chat_id or user_id)
        content: Text content
        media: List of media file paths to send
        reply_to: Original message ID to reply to
    """
    channel: str
    recipient_id: str
    content: str
    media: list[str] = field(default_factory=list)
    reply_to: str | None = None


@dataclass
class AgentMessage(Message):
    """Internal message for agent communication.
    
    Attributes:
        agent_id: Target agent identifier
        action: Action to perform
        payload: Action parameters
    """
    agent_id: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)


# Type aliases for handlers
InboundHandler = Callable[[InboundMessage], Coroutine[Any, Any, None]]
OutboundHandler = Callable[[OutboundMessage], Coroutine[Any, Any, None]]
AgentHandler = Callable[[AgentMessage], Coroutine[Any, Any, None]]


class MessageBus:
    """Message bus for routing messages between components.
    
    This is the central hub for all message passing in the system.
    It decouples channels from agents, allowing:
    - Multiple channels (Feishu, Discord, CLI, etc.)
    - Multiple agents
    - Easy testing and mocking
    - Flexible routing
    
    Example:
        bus = MessageBus()
        
        # Register handlers
        bus.on_inbound(agent.handle_message)
        bus.on_outbound(feishu_channel.send_message)
        
        # Publish messages
        await bus.publish_inbound(InboundMessage(...))
        await bus.publish_outbound(OutboundMessage(...))
    """
    
    def __init__(self) -> None:
        """Initialize the message bus."""
        self._inbound_handlers: list[InboundHandler] = []
        self._outbound_handlers: list[OutboundHandler] = []
        self._agent_handlers: dict[str, list[AgentHandler]] = {}
        self._running = False
        self._inbound_queue: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self._outbound_queue: asyncio.Queue[OutboundMessage] = asyncio.Queue()
        
    def on_inbound(self, handler: InboundHandler) -> None:
        """Register a handler for inbound messages.
        
        Args:
            handler: Async function to handle inbound messages
        """
        self._inbound_handlers.append(handler)
        console.print(f"[dim]📥 Registered inbound handler: {handler.__name__}[/dim]")
        
    def on_outbound(self, handler: OutboundHandler) -> None:
        """Register a handler for outbound messages.
        
        Args:
            handler: Async function to handle outbound messages
        """
        self._outbound_handlers.append(handler)
        console.print(f"[dim]📤 Registered outbound handler: {handler.__name__}[/dim]")
        
    def on_agent(self, agent_id: str, handler: AgentHandler) -> None:
        """Register a handler for agent messages.
        
        Args:
            agent_id: Agent identifier
            handler: Async function to handle agent messages
        """
        if agent_id not in self._agent_handlers:
            self._agent_handlers[agent_id] = []
        self._agent_handlers[agent_id].append(handler)
        console.print(f"[dim]🤖 Registered agent handler: {agent_id}/{handler.__name__}[/dim]")
        
    async def publish_inbound(self, message: InboundMessage) -> None:
        """Publish an inbound message to all handlers.
        
        Args:
            message: The inbound message to publish
        """
        console.print(f"[dim]📥 Publishing inbound message from {message.channel}[/dim]")
        
        # Process handlers concurrently
        if self._inbound_handlers:
            await asyncio.gather(
                *[handler(message) for handler in self._inbound_handlers],
                return_exceptions=True
            )
        else:
            console.print("[yellow]⚠️  No inbound handlers registered[/yellow]")
            
    async def publish_outbound(self, message: OutboundMessage) -> None:
        """Publish an outbound message to all handlers.
        
        Args:
            message: The outbound message to publish
        """
        console.print(f"[dim]📤 Publishing outbound message to {message.channel}[/dim]")
        
        # Process handlers concurrently
        if self._outbound_handlers:
            await asyncio.gather(
                *[handler(message) for handler in self._outbound_handlers],
                return_exceptions=True
            )
        else:
            console.print("[yellow]⚠️  No outbound handlers registered[/yellow]")
            
    async def publish_agent(self, message: AgentMessage) -> None:
        """Publish an agent message to the target agent.
        
        Args:
            message: The agent message to publish
        """
        console.print(f"[dim]🤖 Publishing agent message to {message.agent_id}[/dim]")
        
        handlers = self._agent_handlers.get(message.agent_id, [])
        if handlers:
            await asyncio.gather(
                *[handler(message) for handler in handlers],
                return_exceptions=True
            )
        else:
            console.print(f"[yellow]⚠️  No handlers for agent: {message.agent_id}[/yellow]")
            
    async def start(self) -> None:
        """Start the message bus processing loop."""
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
