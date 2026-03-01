"""Main agent loop for LLM interaction."""

import asyncio
from typing import Any, AsyncIterator

from chaobot.agent.context import ContextBuilder
from chaobot.agent.memory import MemoryManager
from chaobot.agent.tools import ToolRegistry
from chaobot.config.schema import Config
from chaobot.providers.base import BaseProvider
from chaobot.providers.registry import ProviderRegistry


class AgentLoop:
    """Main agent loop handling LLM interaction and tool execution."""

    def __init__(self, config: Config) -> None:
        """Initialize agent loop.

        Args:
            config: Application configuration
        """
        self.config = config
        self.context_builder = ContextBuilder(config)
        self.memory = MemoryManager(config)
        self.tools = ToolRegistry(config)
        self.provider = self._get_provider()
        self.iteration_count = 0
        self.max_iterations = config.agents.max_iterations

    def _get_provider(self) -> BaseProvider:
        """Get the configured LLM provider.

        Returns:
            Provider instance
        """
        registry = ProviderRegistry()
        return registry.get_provider(
            self.config.agents.defaults.provider,
            self.config
        )

    async def run(self, message: str, session_id: str | None = None) -> dict[str, Any]:
        """Run the agent loop.

        Args:
            message: User message
            session_id: Optional session ID for memory

        Returns:
            Response dictionary
        """
        self.iteration_count = 0
        logs: list[str] = []

        # Load conversation history
        history = []
        if session_id:
            history = await self.memory.load_history(session_id)

        # Build initial context
        messages = self.context_builder.build(
            user_message=message,
            history=history,
            tools=self.tools.get_tool_definitions()
        )

        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            logs.append(f"Iteration {self.iteration_count}")

            # Call LLM
            response = await self.provider.complete(messages)

            # Check if response contains tool calls
            if tool_calls := response.get("tool_calls"):
                logs.append(f"Tool calls: {[tc['name'] for tc in tool_calls]}")

                # Execute tools
                tool_results = await self._execute_tools(tool_calls)

                # Add to messages
                messages.append({
                    "role": "assistant",
                    "content": response.get("content", ""),
                    "tool_calls": tool_calls
                })

                for result in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "content": result["content"]
                    })
            else:
                # Final response
                content = response.get("content", "")

                # Save to memory
                if session_id:
                    await self.memory.save_history(session_id, messages + [{
                        "role": "assistant",
                        "content": content
                    }])

                return {
                    "content": content,
                    "logs": logs,
                    "iterations": self.iteration_count
                }

        # Max iterations reached
        return {
            "content": "I apologize, but I reached the maximum number of iterations. Please try a simpler request.",
            "logs": logs,
            "iterations": self.iteration_count,
            "error": "max_iterations_reached"
        }

    async def run_stream(
        self,
        message: str,
        session_id: str | None = None
    ) -> AsyncIterator[str]:
        """Run the agent loop with streaming.

        Args:
            message: User message
            session_id: Optional session ID for memory

        Yields:
            Chunks of response content
        """
        # Load conversation history
        history = []
        if session_id:
            history = await self.memory.load_history(session_id)

        # Build initial context
        messages = self.context_builder.build(
            user_message=message,
            history=history,
            tools=self.tools.get_tool_definitions()
        )

        # For now, just stream the response without tool support
        async for chunk in self.provider.complete_stream(messages):
            yield chunk

    async def _execute_tools(
        self,
        tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Execute tool calls.

        Args:
            tool_calls: List of tool call definitions

        Returns:
            List of tool results
        """
        results = []

        for tool_call in tool_calls:
            name = tool_call.get("name", "")
            arguments = tool_call.get("arguments", {})
            tool_call_id = tool_call.get("id", "")

            try:
                result = await self.tools.execute(name, arguments)
                results.append({
                    "tool_call_id": tool_call_id,
                    "content": str(result)
                })
            except Exception as e:
                results.append({
                    "tool_call_id": tool_call_id,
                    "content": f"Error: {e}"
                })

        return results
