"""Main agent loop for LLM interaction."""

from typing import Any, AsyncIterator, Callable, Awaitable

from chaobot.agent.context import ContextBuilder
from chaobot.agent.memory import MemoryManager
from chaobot.agent.tools import ToolRegistry
from chaobot.agent.tools.confirmation import ConfirmationManager
from chaobot.config.schema import Config
from chaobot.providers.base import BaseProvider
from chaobot.providers.registry import ProviderRegistry


# Progress callback type
ProgressCallback = Callable[[str, bool], Awaitable[None]]


class AgentLoop:
    """Main agent loop handling LLM interaction and tool execution."""

    # Provider priority order (first match wins)
    PROVIDER_PRIORITY = [
        "openrouter",
        "anthropic",
        "openai",
        "deepseek",
        "groq",
        "gemini",
        "custom",
    ]

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

        If a specific provider is configured in agents.defaults.provider,
        use that one. Otherwise, auto-select the first enabled provider
        based on priority order.

        Returns:
            Provider instance
        """
        registry = ProviderRegistry()
        configured_provider = self.config.agents.defaults.provider

        # If a specific provider is configured (not empty), try to use it
        if configured_provider and configured_provider != "custom":
            return registry.get_provider(configured_provider, self.config)

        # Auto-select: find first enabled provider with API key
        providers_config = self.config.providers

        for provider_name in self.PROVIDER_PRIORITY:
            provider_config = self._get_provider_config(provider_name)
            if provider_config and provider_config.enabled and provider_config.api_key:
                print(f"Auto-selected provider: {provider_name}")
                return registry.get_provider(provider_name, self.config)

        # Fallback: use the configured one even if not enabled, or default to openrouter
        if configured_provider:
            return registry.get_provider(configured_provider, self.config)

        return registry.get_provider("openrouter", self.config)

    def _get_provider_config(self, name: str) -> Any:
        """Get provider configuration by name.

        Args:
            name: Provider name

        Returns:
            Provider configuration or None
        """
        providers = self.config.providers

        if name == "openrouter":
            return providers.openrouter
        elif name == "anthropic":
            return providers.anthropic
        elif name == "openai":
            return providers.openai
        elif name == "deepseek":
            return providers.deepseek
        elif name == "groq":
            return providers.groq
        elif name == "gemini":
            return providers.gemini
        elif name == "custom":
            return providers.custom

        return None

    async def run(
        self,
        message: str,
        session_id: str | None = None,
        on_progress: ProgressCallback | None = None
    ) -> dict[str, Any]:
        """Run the agent loop.

        Args:
            message: User message
            session_id: Optional session ID for memory
            on_progress: Optional callback for progress updates (content, is_tool_hint)

        Returns:
            Response dictionary
        """
        self.iteration_count = 0
        logs: list[str] = []
        tools_used: list[str] = []

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

            # Notify progress - iteration start
            if on_progress:
                await on_progress(f"Iteration {self.iteration_count}/{self.max_iterations}", False)

            # Call LLM
            response = await self.provider.complete(messages)

            # Get assistant's content (thinking/reasoning)
            assistant_content = response.get("content", "")

            # Check if response contains tool calls
            if tool_calls := response.get("tool_calls"):
                tool_names = [tc['name'] for tc in tool_calls]
                logs.append(f"Tool calls: {tool_names}")
                tools_used.extend(tool_names)

                # Notify progress - assistant's thinking/reasoning (not tool execution)
                # Send the assistant's natural language response to user
                if on_progress and assistant_content.strip():
                    await on_progress(assistant_content.strip(), False)

                # Execute tools (internal, don't send to user)
                tool_results = await self._execute_tools(tool_calls, on_progress)

                # Add to messages
                messages.append({
                    "role": "assistant",
                    "content": assistant_content,
                    "tool_calls": tool_calls
                })

                for result in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "content": result["content"]
                    })

                # Continue to next iteration to get LLM's response with tool results
                continue
            else:
                # Final response
                content = response.get("content", "")

                # Save to memory - only keep user/assistant pairs, skip tool messages
                if session_id:
                    # Extract only user and final assistant messages
                    history_to_save = []
                    for msg in messages:
                        role = msg.get("role", "")
                        msg_content = msg.get("content", "")
                        tool_calls = msg.get("tool_calls")

                        # Skip system messages
                        if role == "system":
                            continue

                        # Skip tool messages
                        if role == "tool":
                            continue

                        # Skip assistant messages that only have tool_calls (no content)
                        if role == "assistant" and tool_calls and not msg_content:
                            continue

                        # Skip empty assistant messages (no content and no tool_calls)
                        if role == "assistant" and not msg_content:
                            continue

                        # Keep user messages and assistant messages with content
                        if role in ("user", "assistant"):
                            history_to_save.append({
                                "role": role,
                                "content": msg_content
                            })

                    # Add final assistant response (only if not empty)
                    if content:
                        history_to_save.append({
                            "role": "assistant",
                            "content": content
                        })

                    await self.memory.save_history(session_id, history_to_save)

                return {
                    "content": content,
                    "logs": logs,
                    "iterations": self.iteration_count,
                    "tools_used": tools_used
                }

        # Max iterations reached
        return {
            "content": "I apologize, but I reached the maximum number of iterations. Please try a simpler request.",
            "logs": logs,
            "iterations": self.iteration_count,
            "tools_used": tools_used,
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
        tool_calls: list[dict[str, Any]],
        on_progress: ProgressCallback | None = None
    ) -> list[dict[str, Any]]:
        """Execute tool calls.

        Args:
            tool_calls: List of tool call definitions
            on_progress: Optional callback for progress updates

        Returns:
            List of tool results
        """
        results = []

        for tool_call in tool_calls:
            name = tool_call.get("name", "")
            arguments = tool_call.get("arguments", {})
            tool_call_id = tool_call.get("id", "")

            # Notify progress - tool execution start
            if on_progress:
                # Format full arguments for display (no truncation)
                args_str = self._format_arguments_full(arguments)
                await on_progress(f"  ↳ tool -> {args_str}", True)

            try:
                # Check for user confirmation for sensitive operations
                confirmation_manager = ConfirmationManager()
                confirmation = await confirmation_manager.confirm(name, arguments)

                if not confirmation.approved:
                    result_content = f"[STATUS: CANCELLED] Operation cancelled: {confirmation.message}"
                    results.append({
                        "tool_call_id": tool_call_id,
                        "content": result_content
                    })
                    if on_progress:
                        await on_progress(f"    ✗ Cancelled: {confirmation.message}", True)
                    continue

                result = await self.tools.execute(name, arguments)
                # Extract content from ToolResult
                result_str = result.content if result else "(empty result)"

                # Format result with status prefix for better LLM understanding
                if not result or not result.success:
                    result_content = f"[STATUS: ERROR] {result_str}"
                else:
                    result_content = f"[STATUS: SUCCESS] {result_str}"

                results.append({
                    "tool_call_id": tool_call_id,
                    "content": result_content
                })

                # Notify progress - tool execution complete with full result
                if on_progress:
                    # Format the result for display
                    formatted_result = self._format_tool_result(name, result_content)
                    await on_progress(f"    {formatted_result}", True)

            except Exception as e:
                error_msg = str(e)
                result_content = f"[STATUS: EXCEPTION] Error: {error_msg}"
                results.append({
                    "tool_call_id": tool_call_id,
                    "content": result_content
                })

                # Notify progress - tool execution failed
                if on_progress:
                    await on_progress(f"    ✗ Exception: {error_msg}", True)

        return results

    @staticmethod
    def _format_tool_result(tool_name: str, result: str) -> str:
        """Format tool result for CLI display.

        Args:
            tool_name: Name of the tool
            result: Raw result string

        Returns:
            Formatted result string with proper indentation
        """
        if not result:
            return "    (empty result)"

        # Split result into lines and indent each line
        lines = result.split('\n')

        # For single line results, just indent
        if len(lines) == 1:
            return f"    {result}"

        # For multi-line results, format with proper indentation
        formatted_lines = []
        for line in lines:
            if line.strip():  # Only indent non-empty lines
                formatted_lines.append(f"    {line}")
            else:
                formatted_lines.append("")  # Keep empty lines as is

        return '\n'.join(formatted_lines)

    @staticmethod
    def _format_tool_hint(tool_calls: list[dict[str, Any]]) -> str:
        """Format tool calls as a concise hint.

        Args:
            tool_calls: List of tool call definitions

        Returns:
            Formatted hint string
        """
        hints = []
        for tc in tool_calls:
            name = tc.get("name", "")
            args = tc.get("arguments", {})
            if args:
                # Get first argument value for display
                first_val = next(iter(args.values()), None)
                if isinstance(first_val, str):
                    val_str = first_val[:40] + "..." if len(first_val) > 40 else first_val
                    hints.append(f'{name}("{val_str}")')
                else:
                    hints.append(name)
            else:
                hints.append(name)
        return ", ".join(hints)

    @staticmethod
    def _format_arguments(arguments: dict[str, Any]) -> str:
        """Format arguments for display (with truncation for concise output).

        Args:
            arguments: Tool arguments

        Returns:
            Formatted string
        """
        if not arguments:
            return ""

        parts = []
        for key, value in arguments.items():
            val_str = str(value)
            if len(val_str) > 30:
                val_str = val_str[:27] + "..."
            parts.append(f"{key}={val_str}")

        return ", ".join(parts)

    @staticmethod
    def _format_arguments_full(arguments: dict[str, Any]) -> str:
        """Format arguments for display (full version, no truncation).

        Args:
            arguments: Tool arguments

        Returns:
            Formatted string with full argument values
        """
        if not arguments:
            return ""

        parts = []
        for key, value in arguments.items():
            val_str = str(value)
            # Escape newlines for display
            val_str = val_str.replace("\n", "\\n").replace("\r", "\\r")
            parts.append(f"{key}={val_str}")

        return ", ".join(parts)
