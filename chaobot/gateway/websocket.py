"""WebSocket server for real-time communication."""

import asyncio
import json
from typing import Any, Callable

from rich.console import Console

console = Console()


class WebSocketManager:
    """Manages WebSocket connections."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        """Initialize WebSocket manager.

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port
        self._clients: set[Any] = set()
        self._running = False
        self._message_handler: Callable[[str, Any], None] | None = None

    def set_message_handler(self, handler: Callable[[str, Any], None]) -> None:
        """Set handler for incoming messages.

        Args:
            handler: Function to handle messages (message, client)
        """
        self._message_handler = handler

    async def start(self) -> None:
        """Start the WebSocket server."""
        try:
            import websockets
        except ImportError:
            console.print("⚠️  websockets package not installed. Run: pip install websockets")
            return

        self._running = True

        async def handle_client(websocket: Any, path: str) -> None:
            """Handle a client connection."""
            self._clients.add(websocket)
            console.print(f"🔌 WebSocket client connected. Total: {len(self._clients)}")

            try:
                async for message in websocket:
                    await self._handle_message(message, websocket)
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self._clients.discard(websocket)
                console.print(f"🔌 WebSocket client disconnected. Total: {len(self._clients)}")

        self._server = await websockets.serve(
            handle_client,
            self.host,
            self.port
        )

        console.print(f"🌐 WebSocket server started on ws://{self.host}:{self.port}")

        # Keep running
        while self._running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        self._running = False

        # Close all client connections
        if hasattr(self, '_clients'):
            for client in list(self._clients):
                try:
                    await client.close()
                except Exception:
                    pass
            self._clients.clear()

        # Close server
        if hasattr(self, '_server'):
            self._server.close()
            await self._server.wait_closed()

        console.print("🛑 WebSocket server stopped")

    async def _handle_message(self, message: str, client: Any) -> None:
        """Handle incoming message.

        Args:
            message: Message content
            client: Client connection
        """
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            await self.send_to_client(client, {
                "type": "error",
                "error": "Invalid JSON"
            })
            return

        # Call message handler if set
        if self._message_handler:
            try:
                self._message_handler(message, client)
            except Exception as e:
                console.print(f"Error handling message: {e}")
                await self.send_to_client(client, {
                    "type": "error",
                    "error": str(e)
                })

    async def send_to_client(self, client: Any, data: dict) -> None:
        """Send message to a specific client.

        Args:
            client: Client connection
            data: Message data
        """
        try:
            import websockets
            if client in self._clients:
                await client.send(json.dumps(data))
        except Exception as e:
            console.print(f"Error sending to client: {e}")

    async def broadcast(self, data: dict) -> None:
        """Broadcast message to all connected clients.

        Args:
            data: Message data
        """
        if not self._clients:
            return

        message = json.dumps(data)
        disconnected = []

        for client in self._clients:
            try:
                await client.send(message)
            except Exception:
                disconnected.append(client)

        # Remove disconnected clients
        for client in disconnected:
            self._clients.discard(client)

    def get_client_count(self) -> int:
        """Get number of connected clients.

        Returns:
            Number of clients
        """
        return len(self._clients)
