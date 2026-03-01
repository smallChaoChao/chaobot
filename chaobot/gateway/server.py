"""Gateway server managing all channels.

This follows nanobot's design with:
- MessageBus for decoupled communication
- ChannelManager for centralized channel management
- AgentLoop for message processing
"""

import asyncio
import signal
from typing import Any

from rich.console import Console
from rich.panel import Panel

from chaobot.agent.loop import AgentLoop
from chaobot.channels.manager import ChannelManager
from chaobot.config.manager import ConfigManager
from chaobot.bus import get_bus, InboundMessage, OutboundMessage

console = Console()


class GatewayServer:
    """Server managing all chat channels and agent processing."""

    def __init__(self) -> None:
        """Initialize gateway server."""
        self.config = ConfigManager().load()
        self.channel_manager = ChannelManager(self.config)
        self.agent_loop: AgentLoop | None = None
        self.running = False
        self._stop_event = asyncio.Event()
        self._agent_task: asyncio.Task | None = None

    def start(self) -> None:
        """Start the gateway server."""
        console.print("🚀 Starting chaobot server...")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.running = True

        # Run event loop
        try:
            asyncio.run(self._run())
        except KeyboardInterrupt:
            console.print("\n👋 Server stopped")

    async def _run(self) -> None:
        """Run the gateway."""
        # Initialize message bus
        bus = get_bus()
        await bus.start()

        # Initialize agent loop
        self.agent_loop = AgentLoop(self.config)

        # Start channel manager (initializes and starts all channels)
        await self.channel_manager.start_all()

        if not self.channel_manager.channels:
            console.print("⚠️  No channels enabled. Enable channels in config.json")
            return

        # Start agent processing loop
        self._agent_task = asyncio.create_task(self._agent_processing_loop())

        console.print(Panel.fit(
            "✅ Server is running\n\n"
            "Active channels:\n" +
            "\n".join([f"  • {name}" for name in self.channel_manager.channels.keys()]) +
            "\n  • Agent (LLM processing)\n\n"
            "Press Ctrl+C to stop",
            title="🤖 chaobot Server",
            border_style="green"
        ))

        # Keep running until stop signal
        try:
            await self._stop_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self._shutdown()

    async def _agent_processing_loop(self) -> None:
        """Process inbound messages from the bus using AgentLoop.

        This runs continuously, consuming messages from bus.inbound,
        processing them with LLM, and publishing responses to bus.outbound.
        """
        bus = get_bus()

        console.print("[dim]🤖 Agent processing loop started[/dim]")

        while self.running:
            try:
                # Get message from inbound queue
                msg: InboundMessage = await bus.inbound.get()

                console.print(f"[blue]🤖 Processing message from {msg.channel}[/blue]")

                # Clean message content
                content = self._clean_content(msg.content)

                # Process with LLM
                try:
                    response = await self.agent_loop.run(content, session_id=msg.chat_id)
                    response_text = response.get("content", "")
                except Exception as e:
                    console.print(f"[red]❌ LLM error: {e}[/red]")
                    response_text = "抱歉，处理消息时出现错误。"

                # Create outbound message
                outbound_msg = OutboundMessage(
                    id=msg.id,
                    channel=msg.channel,
                    recipient_id=msg.chat_id,
                    content=response_text,
                    reply_to=msg.id
                )

                # Publish to outbound queue
                await bus.outbound.put(outbound_msg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                console.print(f"[red]❌ Agent processing error: {e}[/red]")

        console.print("[dim]🤖 Agent processing loop stopped[/dim]")

    def _clean_content(self, content: str) -> str:
        """Clean message content by removing @ mentions.

        Args:
            content: Raw message content

        Returns:
            Cleaned content
        """
        import re
        cleaned = re.sub(r'@_user_\w+\s*', '', content)
        return cleaned.strip()

    async def _shutdown(self) -> None:
        """Shutdown all components gracefully."""
        console.print("🛑 Shutting down server...")

        # Cancel agent task (don't wait for it)
        if self._agent_task:
            self._agent_task.cancel()

        # Stop channel manager
        await self.channel_manager.stop_all()

        # Stop message bus
        bus = get_bus()
        await bus.stop()

        console.print("[green]✅ Server shutdown complete[/green]")

    def stop(self) -> None:
        """Stop the gateway server."""
        self.running = False
        self._stop_event.set()

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle signals.

        Args:
            signum: Signal number
            frame: Current frame
        """
        console.print(f"\nReceived signal {signum}")
        self.stop()
