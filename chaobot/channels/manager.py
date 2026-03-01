"""Channel manager for managing all chat channels.

This follows nanobot's design for centralized channel management.
"""

import asyncio
from typing import Any

from rich.console import Console

from chaobot.channels.base import BaseChannel
from chaobot.channels.feishu import FeishuChannel
from chaobot.config.schema import Config
from chaobot.bus import get_bus, OutboundMessage

console = Console()


class ChannelManager:
    """Manager for all chat channels.
    
    Responsibilities:
    - Initialize enabled channels based on configuration
    - Start/stop all channels
    - Dispatch outbound messages to appropriate channels
    
    Example:
        manager = ChannelManager(config)
        await manager.start_all()
        
        # Dispatch loop runs automatically
        # Messages from bus.outbound are routed to channels
    """
    
    def __init__(self, config: Config) -> None:
        """Initialize channel manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.channels: dict[str, BaseChannel] = {}
        self._running = False
        self._dispatch_task: asyncio.Task | None = None
        
    def _init_channels(self) -> None:
        """Initialize enabled channels based on configuration."""
        # Initialize Feishu channel if enabled
        if self.config.channels.feishu.enabled:
            channel = FeishuChannel(self.config)
            if channel.is_enabled():
                self.channels[channel.name] = channel
                console.print(f"✓ {channel.name} channel initialized")
            else:
                console.print(f"⚠️  {channel.name} channel not properly configured")
                
    async def start_all(self) -> None:
        """Start all enabled channels and the dispatch loop."""
        self._init_channels()
        
        if not self.channels:
            console.print("⚠️  No channels enabled. Enable channels in config.json")
            return
            
        self._running = True
        
        # Start all channels
        for name, channel in self.channels.items():
            console.print(f"📡 Starting {name} channel...")
            await channel.start()
            
        # Start dispatch loop for outbound messages
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())
        
    async def stop_all(self) -> None:
        """Stop all channels and the dispatch loop."""
        self._running = False
        
        # Cancel dispatch task
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
                
        # Stop all channels
        for name, channel in self.channels.items():
            console.print(f"🛑 Stopping {name} channel...")
            await channel.stop()
            
    async def _dispatch_loop(self) -> None:
        """Dispatch outbound messages to appropriate channels.
        
        This runs continuously, consuming messages from the bus outbound queue
        and routing them to the correct channel.
        """
        bus = get_bus()
        
        console.print("[dim]📤 Outbound dispatch loop started[/dim]")
        
        while self._running:
            try:
                # Get message from outbound queue
                msg = await bus.outbound.get()
                
                # Route to appropriate channel
                channel = self.channels.get(msg.channel)
                if channel:
                    try:
                        await channel.send_message(msg.recipient_id, msg.content)
                    except Exception as e:
                        console.print(f"[red]❌ Error sending to {msg.channel}: {e}[/red]")
                else:
                    console.print(f"[yellow]⚠️  Unknown channel: {msg.channel}[/yellow]")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                console.print(f"[red]❌ Dispatch error: {e}[/red]")
                
        console.print("[dim]📤 Outbound dispatch loop stopped[/dim]")
