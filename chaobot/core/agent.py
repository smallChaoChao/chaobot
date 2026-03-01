"""Agent core for processing messages.

This module implements the Agent that processes inbound messages
and generates responses using LLM.
"""

import asyncio
from typing import Any

from rich.console import Console

from chaobot.agent.loop import AgentLoop
from chaobot.config.schema import Config
from chaobot.core.bus import InboundMessage, OutboundMessage, get_bus

console = Console()


class MessageAgent:
    """Agent for processing messages from channels.
    
    This agent:
    1. Subscribes to inbound messages from the bus
    2. Processes messages using LLM
    3. Publishes responses to the bus
    """
    
    def __init__(self, config: Config) -> None:
        """Initialize the agent.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._running = False
        self._agent_loop: AgentLoop | None = None
        
    async def start(self) -> None:
        """Start the agent and subscribe to message bus."""
        self._running = True
        
        # Initialize agent loop
        self._agent_loop = AgentLoop(
            config=self.config,
            show_logs=False,
            use_markdown=True,
            stream=True
        )
        
        # Subscribe to inbound messages
        bus = get_bus()
        bus.on_inbound(self._handle_message)
        
        console.print("[green]✅ Message agent started[/green]")
        
    async def stop(self) -> None:
        """Stop the agent."""
        self._running = False
        console.print("[yellow]🛑 Message agent stopped[/yellow]")
        
    async def _handle_message(self, message: InboundMessage) -> None:
        """Handle incoming message from the bus.
        
        Args:
            message: Inbound message to process
        """
        console.print(f"[blue]🤖 Agent processing message from {message.channel}[/blue]")
        
        try:
            # Process message using agent loop
            response = await self._process_with_llm(message)
            
            if response:
                # Create outbound message
                outbound_msg = OutboundMessage(
                    id=message.id,
                    channel=message.channel,
                    recipient_id=message.chat_id,
                    content=response,
                    reply_to=message.id
                )
                
                # Publish to bus
                bus = get_bus()
                await bus.publish_outbound(outbound_msg)
                
        except Exception as e:
            console.print(f"[red]❌ Agent error: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            
            # Send error message
            error_msg = OutboundMessage(
                id=message.id,
                channel=message.channel,
                recipient_id=message.chat_id,
                content="抱歉，处理消息时出现错误。请稍后重试。",
                reply_to=message.id
            )
            bus = get_bus()
            await bus.publish_outbound(error_msg)
    
    async def _process_with_llm(self, message: InboundMessage) -> str:
        """Process message with LLM.
        
        Args:
            message: Inbound message
            
        Returns:
            LLM response text
        """
        if not self._agent_loop:
            return "Agent not initialized"
        
        # Clean message content (remove @ mentions for now)
        content = self._clean_content(message.content)
        
        # Run agent loop
        try:
            # Use run method which returns the full response
            response = await self._agent_loop.run(content, session_id=message.chat_id)
            return response
        except Exception as e:
            console.print(f"[red]❌ LLM error: {e}[/red]")
            return "抱歉，我无法处理您的请求。"
    
    def _clean_content(self, content: str) -> str:
        """Clean message content by removing @ mentions.
        
        Args:
            content: Raw message content
            
        Returns:
            Cleaned content
        """
        # Remove @_user_X patterns
        import re
        cleaned = re.sub(r'@_user_\w+\s*', '', content)
        return cleaned.strip()
