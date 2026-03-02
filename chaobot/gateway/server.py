"""Gateway server for handling chat channels and agent processing."""

import asyncio
import signal
from typing import Any

from rich.console import Console

from chaobot.channels.manager import ChannelManager
from chaobot.config.manager import ConfigManager
from chaobot.bus import get_bus, InboundMessage, OutboundMessage
from chaobot.agent.runner import AgentRunner

console = Console()


# ASCII art banner for ChaoBot - Large and clear
CHAOBOT_BANNER = r"""
    ____   _                       ____            _
   / ___| | |__     __ _    ___   | __ )    ___   | |_
  | |     | '_ \   / _` |  / _ \  |  _ \   / _ \  | __|
  | |___  | | | | | (_| | | (_) | | |_) | | (_) | | |_
   \____| |_| |_|  \__,_|  \___/  |____/   \___/   \__|

           🤖  Your Personal AI Assistant
"""


class GatewayServer:
    """Server managing all chat channels and agent processing."""

    def __init__(self, show_logs: bool = True) -> None:
        """Initialize gateway server.

        Args:
            show_logs: Whether to show tool execution logs
        """
        self.config = ConfigManager().load()
        self.channel_manager = ChannelManager(self.config)
        self.show_logs = show_logs
        self.running = False
        self._stop_event = asyncio.Event()
        self._agent_task: asyncio.Task | None = None

    def start(self) -> None:
        """Start the gateway server."""
        # Print ASCII banner
        console.print(f"[cyan]{CHAOBOT_BANNER}[/cyan]")

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

        # Start channel manager (initializes and starts all channels)
        await self.channel_manager.start_all()

        if not self.channel_manager.channels:
            console.print("⚠️  No channels enabled. Enable channels in config.json")
            return

        # Start agent processing loop
        self._agent_task = asyncio.create_task(self._agent_processing_loop())

        # Print simplified status
        channels_str = ", ".join(self.channel_manager.channels.keys())
        console.print(f"[green]✓[/green] Server started | Channels: {channels_str}")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        # Keep running until stop signal
        try:
            await self._stop_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self._shutdown()

    async def _agent_processing_loop(self) -> None:
        """Process inbound messages from the bus using AgentRunner.

        This runs continuously, consuming messages from bus.inbound,
        processing them with LLM, and publishing responses to bus.outbound.
        """
        bus = get_bus()

        while self.running:
            try:
                # Get message from inbound queue
                msg: InboundMessage = await bus.inbound.get()

                # Clean message content
                content = self._clean_content(msg.content)

                # Process with LLM using AgentRunner (same as CLI)
                try:
                    await self._process_message_with_progress(
                        content,
                        session_id=msg.chat_id,
                        channel=msg.channel,
                        msg_id=msg.id
                    )
                except Exception as e:
                    console.print(f"[red]❌ Error: {e}[/red]")
                    # Send error message to user
                    outbound_msg = OutboundMessage(
                        id=msg.id,
                        channel=msg.channel,
                        recipient_id=msg.chat_id,
                        content=f"抱歉，处理消息时出现错误：{e}",
                        reply_to=msg.id
                    )
                    await bus.outbound.put(outbound_msg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                console.print(f"[red]❗ Error: {e}[/red]")

    async def _process_message_with_progress(
        self,
        message: str,
        session_id: str,
        channel: str,
        msg_id: str
    ) -> None:
        """Process a message with real-time progress updates sent to user.

        Args:
            message: Message content
            session_id: Session ID for conversation history
            channel: Channel name (e.g., "feishu", "telegram")
            msg_id: Original message ID for reply
        """
        bus = get_bus()

        # Create AgentRunner with streaming disabled and no confirmation prompts
        runner = AgentRunner(
            show_logs=self.show_logs,
            use_markdown=True,
            stream=False,  # Disable streaming for more reliable tool support
            session_id=session_id,
            confirm_sensitive=False  # Disable confirmation prompts in server mode
        )

        # Use non-streaming mode for reliable tool support
        await self._process_message_non_streaming(
            runner, message, session_id, channel, msg_id
        )

    async def _process_message_streaming(
        self,
        runner: AgentRunner,
        message: str,
        session_id: str,
        channel: str,
        msg_id: str
    ) -> None:
        """Process message with streaming output.

        Args:
            runner: AgentRunner instance
            message: Message content
            session_id: Session ID
            channel: Channel name
            msg_id: Message ID
        """
        bus = get_bus()
        full_content = ""
        buffer = ""
        tool_call_detected = False
        last_sent_content = ""

        # Stream the response
        async for chunk in runner.loop.run_stream(message, session_id=session_id):
            buffer += chunk
            full_content += chunk

            # Check for tool call patterns
            if not tool_call_detected:
                if '"tool_calls"' in buffer or '"function"' in buffer:
                    tool_call_detected = True
                    break

                # Send chunks periodically (every 20 chars or on punctuation)
                if len(buffer) >= 20 or any(c in chunk for c in '。！？.!?'):
                    if buffer != last_sent_content:
                        outbound_msg = OutboundMessage(
                            id=f"{msg_id}_stream_{hash(buffer) & 0xFFFFFFFF}",
                            channel=channel,
                            recipient_id=session_id,
                            content=buffer,
                            reply_to=msg_id
                        )
                        await bus.outbound.put(outbound_msg)
                        last_sent_content = buffer

        # If tool call detected, fall back to non-streaming
        if tool_call_detected:
            if self.show_logs:
                console.print("[dim]Detected tool call, switching to non-streaming mode...[/dim]")
            await self._process_message_non_streaming(
                runner, message, session_id, channel, msg_id
            )
        else:
            # Send any remaining content
            if buffer and buffer != last_sent_content:
                outbound_msg = OutboundMessage(
                    id=f"{msg_id}_final",
                    channel=channel,
                    recipient_id=session_id,
                    content=buffer,
                    reply_to=msg_id
                )
                await bus.outbound.put(outbound_msg)

    async def _process_message_non_streaming(
        self,
        runner: AgentRunner,
        message: str,
        session_id: str,
        channel: str,
        msg_id: str
    ) -> None:
        """Process message with non-streaming output (for tool calls).

        Args:
            runner: AgentRunner instance
            message: Message content
            session_id: Session ID
            channel: Channel name
            msg_id: Message ID
        """
        bus = get_bus()

        # Track if we've sent any progress message
        progress_sent = False
        last_progress_content = ""

        # Define progress callback that sends messages to user in real-time
        async def on_progress(content: str, is_tool_hint: bool) -> None:
            """Handle progress updates and send to user."""
            nonlocal progress_sent, last_progress_content

            # Skip iteration messages
            if content.startswith("Iteration"):
                return

            # Skip duplicate messages
            if content == last_progress_content:
                return
            last_progress_content = content

            # Log tool execution to console (for debugging)
            if is_tool_hint:
                if self.show_logs:
                    # Simplified tool log format
                    console.print(f"[cyan]  🔧 {content}[/cyan]")
                # Also send tool hints to user if show_logs is enabled
                if self.show_logs:
                    progress_sent = True
                    outbound_msg = OutboundMessage(
                        id=f"{msg_id}_tool_{hash(content) & 0xFFFFFFFF}",
                        channel=channel,
                        recipient_id=session_id,
                        content=f"🔧 {content}",
                        reply_to=msg_id
                    )
                    await bus.outbound.put(outbound_msg)

            # Send assistant's natural language output to user (not tool hints)
            if not is_tool_hint and content.strip():
                progress_sent = True
                outbound_msg = OutboundMessage(
                    id=f"{msg_id}_progress_{hash(content) & 0xFFFFFFFF}",
                    channel=channel,
                    recipient_id=session_id,
                    content=content.strip(),
                    reply_to=msg_id
                )
                await bus.outbound.put(outbound_msg)

        # Run the agent with progress callback
        response_text = await runner.run(message, on_progress=on_progress)

        # Send final response
        outbound_msg = OutboundMessage(
            id=msg_id,
            channel=channel,
            recipient_id=session_id,
            content=response_text,
            reply_to=msg_id
        )
        await bus.outbound.put(outbound_msg)

    def _clean_content(self, content: str) -> str:
        """Clean message content by removing bot mentions.

        Args:
            content: Raw message content

        Returns:
            Cleaned content
        """
        # Remove @_user_1 mentions (Feishu bot mention format)
        import re
        cleaned = re.sub(r'@_user_\d+\s*', '', content).strip()
        return cleaned

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        console.print("\n[yellow]Received signal {}[/yellow]".format(signum))
        self._stop_event.set()

    async def _shutdown(self) -> None:
        """Shutdown the gateway gracefully."""
        self.running = False

        # Stop channel manager
        await self.channel_manager.stop_all()

        # Stop message bus
        bus = get_bus()
        await bus.stop()

        console.print("[green]✓[/green] Server stopped")
