"""Feishu (Lark) channel implementation using WebSocket long connection."""

import asyncio
import json
import threading
import time
import uuid
from typing import Any

from rich.console import Console

try:
    import lark_oapi as lark
    from lark_oapi.api.im.v1 import (
        CreateMessageRequest,
        CreateMessageRequestBody,
        P2ImMessageReceiveV1,
    )
    FEISHU_AVAILABLE = True
except ImportError:
    FEISHU_AVAILABLE = False

from chaobot.channels.base import BaseChannel
from chaobot.bus import InboundMessage, get_bus

console = Console()


class FeishuChannel(BaseChannel):
    """Feishu/Lark bot channel using WebSocket long connection."""

    name = "feishu"

    def __init__(self, config: Any) -> None:
        """Initialize Feishu channel.

        Args:
            config: Channel configuration
        """
        super().__init__(config)
        self.enabled = config.channels.feishu.enabled
        self.app_id = config.channels.feishu.app_id or ""
        self.app_secret = config.channels.feishu.app_secret or ""
        self.encrypt_key = config.channels.feishu.encrypt_key or ""
        self.verification_token = config.channels.feishu.verification_token or ""
        self.allow_users = config.channels.feishu.allow_from or []

        self._running = False
        self._client: Any = None
        self._ws_client: Any = None
        self._ws_thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def is_enabled(self) -> bool:
        """Check if channel is enabled."""
        if not FEISHU_AVAILABLE:
            console.print("[red]❌ lark-oapi not installed. Run: pip install lark-oapi[/red]")
            return False
        return self.enabled and bool(self.app_id and self.app_secret)

    async def start(self) -> None:
        """Start the Feishu channel with WebSocket long connection."""
        if not self.is_enabled():
            console.print("[yellow]⚠️  Feishu channel not enabled or missing credentials[/yellow]")
            return

        console.print(f"[blue]📝 Feishu App ID: {self.app_id[:10]}...[/blue]")
        self._running = True
        self._loop = asyncio.get_event_loop()

        # Create Lark client for sending messages
        try:
            self._client = lark.Client.builder() \
                .app_id(self.app_id) \
                .app_secret(self.app_secret) \
                .log_level(lark.LogLevel.INFO) \
                .build()
            console.print("[green]✅ Feishu client created[/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to create Feishu client: {e}[/red]")
            return

        # Create event handler for receiving messages
        event_handler = lark.EventDispatcherHandler.builder(
            self.encrypt_key,
            self.verification_token,
        ).register_p2_im_message_receive_v1(
            self._on_message_sync
        ).build()

        # Create WebSocket client for long connection
        self._ws_client = lark.ws.Client(
            self.app_id,
            self.app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO
        )

        console.print("[blue]🔌 Starting Feishu WebSocket connection...[/blue]")

        # Start WebSocket client in a separate thread with auto-reconnect
        def run_ws():
            while self._running:
                try:
                    console.print("[blue]🔄 Connecting to Feishu WebSocket...[/blue]")
                    self._ws_client.start()
                except Exception as e:
                    console.print(f"[yellow]⚠️  Feishu WebSocket error: {e}[/yellow]")
                if self._running:
                    console.print("[yellow]🔄 Reconnecting in 5 seconds...[/yellow]")
                    time.sleep(5)

        self._ws_thread = threading.Thread(target=run_ws, daemon=True)
        self._ws_thread.start()
        console.print("[green]✅ Feishu WebSocket started in background thread[/green]")

    async def stop(self) -> None:
        """Stop the Feishu channel."""
        self._running = False
        console.print("[yellow]🛑 Stopping Feishu channel...[/yellow]")

        # Note: lark-oapi WebSocket client doesn't have a stop method
        # It will stop when _running is False and the thread exits
        # Don't wait for thread - it will exit on its own when _running is False

        console.print("[green]✅ Feishu channel stopped[/green]")



    async def send_message(self, to: str, message: str) -> None:
        """Send a message to Feishu.

        Args:
            to: Chat ID or Open ID
            message: Message content
        """
        if not self._client:
            console.print("[red]❌ Feishu client not initialized[/red]")
            return

        # Determine receive_id_type
        if to.startswith("ou_"):
            receive_id_type = "open_id"
        elif to.startswith("oc_"):
            receive_id_type = "chat_id"
        else:
            receive_id_type = "open_id"

        # Build request
        request = CreateMessageRequest.builder() \
            .receive_id_type(receive_id_type) \
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(to)
                .msg_type("text")
                .content(json.dumps({"text": message}))
                .build()
            ) \
            .build()

        # Send message in executor (since lark client is sync)
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self._client.im.v1.message.create(request)
            )

            if response.success():
                console.print(f"[green]✅ Message sent to {to}[/green]")
            else:
                console.print(f"[red]❌ Failed to send message: {response.msg}[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error sending message: {e}[/red]")

    def _on_message_sync(self, data: P2ImMessageReceiveV1) -> None:
        """Sync handler for incoming messages (called from WebSocket thread).

        Args:
            data: Message data from Feishu
        """
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._on_message(data), self._loop)

    async def _on_message(self, data: P2ImMessageReceiveV1) -> None:
        """Handle incoming message from Feishu.

        Args:
            data: Message data
        """
        try:
            event = data.event
            message = event.message
            sender = event.sender

            console.print(f"[dim]📨 Message type: {message.message_type}[/dim]")

            # Skip bot messages
            if sender.sender_type == "bot":
                console.print("[yellow]⚠️  Skipping bot message[/yellow]")
                return

            # Get sender info
            sender_id = sender.sender_id.open_id
            sender_name = sender.sender_id.union_id or "Unknown"

            console.print(f"[blue]👤 Message from: {sender_name} ({sender_id})[/blue]")

            # Check if sender is allowed
            if self.allow_users and sender_id not in self.allow_users:
                console.print(f"[yellow]⚠️  Sender {sender_id} not in allowlist[/yellow]")
                return

            # Parse message content
            msg_type = message.message_type
            content_json = json.loads(message.content)

            if msg_type == "text":
                text = content_json.get("text", "")
            else:
                text = f"[Unsupported message type: {msg_type}]"

            console.print(f"[green]💬 Message: {text[:100]}...[/green]")

            # Get chat ID for reply
            chat_id = message.chat_id
            console.print(f"[blue]💬 Chat ID: {chat_id}[/blue]")

            # Create inbound message and publish to bus
            inbound_msg = InboundMessage(
                id=str(uuid.uuid4()),
                channel=self.name,
                sender_id=sender_id,
                chat_id=chat_id,
                content=text,
                raw_data=data
            )

            bus = get_bus()
            await bus.inbound.put(inbound_msg)

        except Exception as e:
            console.print(f"[red]❌ Error processing message: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
