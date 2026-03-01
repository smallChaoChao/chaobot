"""Message event definitions for the message bus."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class InboundMessage:
    """Message received from external channels (Feishu, Discord, etc.).

    Attributes:
        id: Unique message identifier
        timestamp: Message timestamp
        channel: Channel name (e.g., "feishu", "discord")
        sender_id: Unique sender identifier
        chat_id: Chat/room identifier
        content: Text content
        media: List of media file paths
        metadata: Additional metadata
        raw_data: Original raw data from the channel
    """
    id: str
    channel: str
    sender_id: str
    chat_id: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    media: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_data: Any = None


@dataclass
class OutboundMessage:
    """Message to be sent to external channels.

    Attributes:
        id: Unique message identifier
        timestamp: Message timestamp
        channel: Target channel name
        recipient_id: Recipient identifier (chat_id or user_id)
        content: Text content
        media: List of media file paths to send
        metadata: Additional metadata
        reply_to: Original message ID to reply to
    """
    id: str
    channel: str
    recipient_id: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    media: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    reply_to: str | None = None


@dataclass
class AgentMessage:
    """Internal message for agent communication.

    Attributes:
        id: Unique message identifier
        timestamp: Message timestamp
        agent_id: Target agent identifier
        action: Action to perform
        payload: Action parameters
        metadata: Additional metadata
    """
    id: str
    agent_id: str
    action: str
    timestamp: datetime = field(default_factory=datetime.now)
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
