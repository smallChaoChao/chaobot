"""Context builder for agent prompts."""

from typing import Any

from chaobot.config.schema import Config
from chaobot.skills import get_skills_loader
from chaobot.skills.selector import get_skill_selector


DEFAULT_SYSTEM_PROMPT = """You are chaobot, a helpful AI assistant.

You have access to tools that can help you accomplish tasks. Use them when appropriate.

Guidelines:
- Be concise but thorough
- Ask clarifying questions if needed
- Use tools to gather information or perform actions
- Always prioritize user safety and privacy
- State intent before tool calls, but NEVER predict or claim results before receiving them
- Before modifying a file, read it first. Do not assume files or directories exist
- After writing or editing a file, re-read it if accuracy matters
- If a tool call fails, analyze the error before retrying with a different approach
"""

SKILLS_INSTRUCTION = """
# Skills System

You have access to skills that extend your capabilities. Each skill is documented in a SKILL.md file.

## How to Use Skills

1. **Check Available Skills**: Review the skills list below to find relevant ones
2. **Read Skill Documentation**: Use the `file_read` tool to read the SKILL.md file
3. **Follow Instructions**: Execute the commands or steps described in the skill
4. **Use Tools**: Skills use your available tools (shell, file operations, web search, etc.)

## Skill Status

- Skills with `available="true"` can be used immediately
- Skills with `available="false"` need dependencies installed first

## Available Skills

"""

# Maximum messages to keep in context (prevent too long context)
MAX_HISTORY_MESSAGES = 20
# Maximum characters per message to prevent huge tool outputs
MAX_MESSAGE_LENGTH = 8000


class ContextBuilder:
    """Builds conversation context for LLM calls."""

    def __init__(self, config: Config) -> None:
        """Initialize context builder.

        Args:
            config: Application configuration
        """
        self.config = config
        self.skills = get_skills_loader()

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

        # System prompt with skills and tools
        system_prompt = (
            self.config.agents.defaults.system_prompt
            or DEFAULT_SYSTEM_PROMPT
        )

        # Add always skills to system prompt (these are loaded automatically)
        always_skills = self.skills.get_always_skills()
        if always_skills:
            always_content = self.skills.load_skills_for_context(always_skills)
            if always_content:
                system_prompt += f"\n\n# Active Skills (Always Loaded)\n\n{always_content}"

        # Add skills summary with instructions
        skills_summary = self.skills.build_skills_summary()
        if skills_summary:
            system_prompt += f"\n\n{SKILLS_INSTRUCTION}{skills_summary}\n\n---\n\nWhen you need to perform a task, first check if there's a relevant skill above. If so, read its SKILL.md file using the file_read tool to learn how to use it."

        # Add smart skill recommendations based on user input
        selector = get_skill_selector(self.skills)
        recommendations = selector.build_skill_recommendation(user_message)
        if recommendations:
            system_prompt += recommendations

        # Build system message with tools
        system_msg = {"role": "system", "content": system_prompt}
        if tools:
            # Store tools in metadata for provider to extract
            system_msg["tools"] = tools

        messages.append(system_msg)

        # Add history - filter and limit
        if history:
            # Filter to only user/assistant/tool messages (no system)
            filtered_history = self._filter_history(history)
            # Limit to recent messages
            limited_history = filtered_history[-MAX_HISTORY_MESSAGES:]
            messages.extend(limited_history)

        # Add user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _filter_history(
        self,
        history: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Filter history to valid conversation messages.

        Args:
            history: Raw history from storage

        Returns:
            Filtered list of messages
        """
        filtered = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Skip system messages - they are regenerated each time
            if role == "system":
                continue

            # Skip empty messages
            if not content and role != "assistant":
                continue

            # Truncate very long messages (usually tool outputs)
            if len(content) > MAX_MESSAGE_LENGTH:
                content = content[:MAX_MESSAGE_LENGTH] + "\n... [content truncated]"

            # Create clean message with only necessary fields
            clean_msg: dict[str, Any] = {
                "role": role,
                "content": content
            }

            # Preserve tool call information for assistant messages
            if "tool_calls" in msg:
                clean_msg["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg:
                clean_msg["tool_call_id"] = msg["tool_call_id"]
            if "name" in msg:
                clean_msg["name"] = msg["name"]

            filtered.append(clean_msg)

        return filtered

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
