"""Gateway server managing all channels."""

import asyncio
import signal
from typing import Any

from rich.console import Console
from rich.panel import Panel

from chaobot.channels.feishu import FeishuChannel
from chaobot.config.manager import ConfigManager
from chaobot.gateway.websocket import WebSocketManager

console = Console()


class GatewayServer:
    """Server managing all chat channels."""

    def __init__(self) -> None:
        """Initialize gateway server."""
        self.config = ConfigManager().load()
        self.channels: list[Any] = []
        self.running = False
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        """Start the gateway server."""
        console.print("🚀 Starting chaobot server...")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Initialize enabled channels
        self._init_channels()

        if not self.channels:
            console.print("⚠️  No channels enabled. Enable channels in config.json")
            return

        self.running = True

        # Run event loop
        try:
            asyncio.run(self._run())
        except KeyboardInterrupt:
            console.print("\n👋 Server stopped")

    async def _run(self) -> None:
        """Run the gateway."""
        # Start all channels
        tasks = []
        for channel in self.channels:
            console.print(f"📡 Starting {channel.name} channel...")
            tasks.append(asyncio.create_task(channel.start()))

        # Start WebSocket server
        ws_manager = WebSocketManager(
            host="0.0.0.0",
            port=8765
        )
        tasks.append(asyncio.create_task(ws_manager.start()))

        console.print(Panel.fit(
            "✅ Server is running\n\n"
            "Active channels:\n" +
            "\n".join([f"  • {ch.name}" for ch in self.channels]) +
            "\n  • WebSocket (ws://localhost:8765)\n\n"
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
            # Stop all channels
            for channel in self.channels:
                await channel.stop()
            await ws_manager.stop()

    def stop(self) -> None:
        """Stop the gateway server."""
        self.running = False
        console.print("🛑 Stopping server...")
        self._stop_event.set()

    def _init_channels(self) -> None:
        """Initialize enabled channels based on configuration."""
        # Initialize Feishu channel if enabled
        if self.config.channels.feishu.enabled:
            self.channels.append(FeishuChannel(self.config))
            console.print("✓ Feishu channel initialized")

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle signals.

        Args:
            signum: Signal number
            frame: Current frame
        """
        console.print(f"\nReceived signal {signum}")
        self.stop()
