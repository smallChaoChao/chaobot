"""Context builder for agent prompts."""

from typing import Any

from chaobot.config.schema import Config


DEFAULT_SYSTEM_PROMPT = """You are chaobot, a helpful AI assistant.

You have access to tools that can help you accomplish tasks. Use them when appropriate.

Guidelines:
- Be concise but thorough
- Ask clarifying questions if needed
- Use tools to gather information or perform actions
- Always prioritize user safety and privacy
"""


class ContextBuilder:
    """Builds conversation context for LLM calls."""

    def __init__(self, config: Config) -> None:
        """Initialize context builder.

        Args:
            config: Application configuration
        """
        self.config = config

    def build(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        """Build message context.

        Args:
            user_message: Current user message
            history: Optional conversation history
            tools: Optional tool definitions

        Returns:
            List of messages for LLM
        """
        messages = []

        # System prompt with tools if provided
        system_prompt = (
            self.config.agents.defaults.system_prompt
            or DEFAULT_SYSTEM_PROMPT
        )

        # Build system message with tools
        system_msg = {"role": "system", "content": system_prompt}
        if tools:
            # Store tools in metadata for provider to extract
            system_msg["tools"] = tools

        messages.append(system_msg)

        # Add history
        if history:
            # Limit history to context window
            max_tokens = self.config.agents.context_window
            # Rough estimate: 4 chars per token
            max_chars = max_tokens * 4

            history_text = ""
            for msg in reversed(history):
                msg_text = str(msg)
                if len(history_text) + len(msg_text) > max_chars:
                    break
                history_text = msg_text + history_text
                messages.insert(1, msg)

        # Add user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def add_tool_result(
        self,
        messages: list[dict[str, Any]],
        tool_call_id: str,
        tool_name: str,
        result: str
    ) -> list[dict[str, Any]]:
        """Add tool result to messages.

        Args:
            messages: Current messages
            tool_call_id: Tool call ID
            tool_name: Tool name
            result: Tool execution result

        Returns:
            Updated messages
        """
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result
        })
        return messages
