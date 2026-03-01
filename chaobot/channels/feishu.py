"""Feishu (Lark) channel implementation."""

import asyncio
import hashlib
import json
from typing import Any

import httpx

from chaobot.channels.base import BaseChannel


class FeishuChannel(BaseChannel):
    """Feishu/Lark bot channel."""

    name = "feishu"

    def __init__(self, config: Any) -> None:
        """Initialize Feishu channel.

        Args:
            config: Channel configuration
        """
        super().__init__(config)
        self.enabled = config.channels.feishu.enabled
        self.app_id = config.channels.feishu.app_id
        self.app_secret = config.channels.feishu.app_secret
        self.webhook_url = config.channels.feishu.webhook_url
        self.bot_name = config.channels.feishu.bot_name
        self.allow_users = config.channels.feishu.allow_from

        self._running = False
        self._client: httpx.AsyncClient | None = None
        self._token: str | None = None
        self._token_expires: int = 0

    def is_enabled(self) -> bool:
        """Check if channel is enabled."""
        return self.enabled and bool(self.app_id and self.app_secret)

    async def start(self) -> None:
        """Start the Feishu channel."""
        if not self.is_enabled():
            return

        self._running = True
        self._client = httpx.AsyncClient(timeout=30)

        # Get tenant access token
        await self._refresh_token()

        # Start webhook server if configured
        if self.webhook_url:
            asyncio.create_task(self._webhook_server())

    async def stop(self) -> None:
        """Stop the Feishu channel."""
        self._running = False
        if self._client:
            await self._client.aclose()

    async def send_message(self, to: str, message: str) -> None:
        """Send a message to Feishu.

        Args:
            to: Chat ID or Open ID
            message: Message content
        """
        if not self._client:
            return

        # Ensure token is valid
        if not self._token or asyncio.get_event_loop().time() > self._token_expires:
            await self._refresh_token()

        url = "https://open.feishu.cn/open-apis/im/v1/messages"

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

        # Determine if it's a user or chat
        if to.startswith("ou_"):
            receive_id_type = "open_id"
        elif to.startswith("oc_"):
            receive_id_type = "chat_id"
        else:
            receive_id_type = "open_id"

        data = {
            "receive_id": to,
            "msg_type": "text",
            "content": json.dumps({"text": message})
        }

        try:
            response = await self._client.post(
                url,
                headers=headers,
                params={"receive_id_type": receive_id_type},
                json=data
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(f"Failed to send Feishu message: {e}")

    async def _refresh_token(self) -> None:
        """Refresh tenant access token."""
        if not self._client:
            return

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        try:
            response = await self._client.post(url, json=data)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                self._token = result["tenant_access_token"]
                # Token expires in expire - 60 seconds (buffer)
                self._token_expires = asyncio.get_event_loop().time() + result.get("expire", 7200) - 60
            else:
                print(f"Failed to get Feishu token: {result}")
        except httpx.HTTPError as e:
            print(f"Failed to refresh Feishu token: {e}")

    async def _webhook_server(self) -> None:
        """Start webhook server for receiving messages."""
        from aiohttp import web

        async def handle_webhook(request: web.Request) -> web.Response:
            """Handle incoming webhook."""
            try:
                body = await request.json()

                # Verify signature if encrypt key is configured
                if not self._verify_signature(request):
                    return web.Response(status=401)

                # Handle challenge (for URL verification)
                if "challenge" in body:
                    return web.json_response({"challenge": body["challenge"]})

                # Process message
                await self._process_message(body)

                return web.Response(status=200)
            except Exception as e:
                print(f"Error handling Feishu webhook: {e}")
                return web.Response(status=500)

        app = web.Application()
        app.router.add_post("/webhook/feishu", handle_webhook)

        runner = web.AppRunner(app)
        await runner.setup()

        # Parse webhook URL to get port
        from urllib.parse import urlparse
        parsed = urlparse(self.webhook_url)
        port = parsed.port or 8080

        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()

        print(f"Feishu webhook server started on port {port}")

        # Keep running
        while self._running:
            await asyncio.sleep(1)

        await runner.cleanup()

    def _verify_signature(self, request: Any) -> bool:
        """Verify webhook signature.

        Args:
            request: HTTP request

        Returns:
            True if signature is valid
        """
        # TODO: Implement signature verification
        return True

    async def _process_message(self, data: dict) -> None:
        """Process incoming message.

        Args:
            data: Message data
        """
        event = data.get("event", {})
        message = event.get("message", {})

        # Check if it's a text message
        if message.get("message_type") != "text":
            return

        # Get sender info
        sender = event.get("sender", {})
        sender_id = sender.get("sender_id", {}).get("open_id")

        # Check if sender is allowed
        if self.allow_users and sender_id not in self.allow_users:
            return

        # Get message content
        content = json.loads(message.get("content", "{}"))
        text = content.get("text", "")

        # Get chat ID
        chat_id = message.get("chat_id")

        # TODO: Send to agent for processing
        # For now, just echo back
        response = f"Echo: {text}"
        await self.send_message(chat_id, response)
