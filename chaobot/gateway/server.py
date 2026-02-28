"""Gateway server managing all channels."""

import asyncio
import signal
from typing import Any

from rich.console import Console

from chaobot.config.manager import ConfigManager

console = Console()


class GatewayServer:
    """Server managing all chat channels."""

    def __init__(self) -> None:
        """Initialize gateway server."""
        self.config = ConfigManager().load()
        self.channels: list[Any] = []
        self.running = False

    def start(self) -> None:
        """Start the gateway server."""
        console.print("🚀 Starting chaobot gateway...")

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
            console.print("\n👋 Gateway stopped")

    async def _run(self) -> None:
        """Run the gateway."""
        # Start all channels
        tasks = []
        for channel in self.channels:
            console.print(f"📡 Starting {channel.name} channel...")
            tasks.append(asyncio.create_task(channel.start()))

        console.print("✅ Gateway running. Press Ctrl+C to stop.")

        # Wait for all channels
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass

    def stop(self) -> None:
        """Stop the gateway server."""
        self.running = False
        console.print("🛑 Stopping gateway...")

        # Stop all channels
        for channel in self.channels:
            asyncio.create_task(channel.stop())

    def _init_channels(self) -> None:
        """Initialize enabled channels."""
        # TODO: Initialize channels based on config
        # This is a placeholder - implement actual channel initialization
        pass

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle signals.

        Args:
            signum: Signal number
            frame: Current frame
        """
        console.print(f"\nReceived signal {signum}")
        self.stop()
