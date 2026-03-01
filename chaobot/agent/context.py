"""Context builder for agent prompts."""

import os
from pathlib import Path
from typing import Any

from chaobot.config.schema import Config
from chaobot.skills import get_skills_loader


DEFAULT_SYSTEM_PROMPT = """You are chaobot, a helpful AI assistant.

You have access to tools that can help you accomplish tasks. Use them when appropriate.

Guidelines:
- Be concise but thorough
- Ask clarifying questions if needed
- Use tools to gather information or perform actions
- Always prioritize user safety and privacy
- State intent before tool calls, but NEVER predict or claim results before receiving them
- Before modifying a file, read it first. Do not assume files or directories exist
- After writing or editing a file, re-read if accuracy matters
- If a tool call fails, analyze the error before retrying with a different approach

CRITICAL - Tool Execution Awareness:
- ALWAYS check the tool execution results in the conversation history before making new tool calls
- Tool results are prefixed with [STATUS: SUCCESS], [STATUS: ERROR], [STATUS: CANCELLED], or [STATUS: EXCEPTION]
- If a tool returned [STATUS: SUCCESS], DO NOT call the same tool with the same arguments again
- If you see a command succeeded (e.g., "mkdir -p ..." returned successfully), do not execute it again
- Use the information from successful tool results to inform your next steps
- Track what has been done vs what still needs to be done
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
        self.workspace_dir = Path.home() / ".chaobot" / "workspace"

    def _load_workspace_file(self, filename: str) -> str | None:
        """Load a workspace file if it exists.

        Args:
            filename: Name of the file (e.g., "SOUL.md")

        Returns:
            File content or None if not found
        """
        filepath = self.workspace_dir / filename
        if filepath.exists():
            try:
                return filepath.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

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

        # Inject workspace files (OpenClaw-style progressive disclosure)
        # These define behavior, personality, and tool knowledge

        # 1. SOUL.md - Behavioral guidelines and personality
        soul_content = self._load_workspace_file("SOUL.md")
        if soul_content:
            system_prompt += f"\n\n# Behavioral Guidelines\n\n{soul_content}"

        # 2. TOOLS.md - Tool capabilities and best practices
        tools_content = self._load_workspace_file("TOOLS.md")
        if tools_content:
            system_prompt += f"\n\n# Tool Guidelines\n\n{tools_content}"

        # 3. AGENTS.md - Multi-agent workflows and patterns
        agents_content = self._load_workspace_file("AGENTS.md")
        if agents_content:
            system_prompt += f"\n\n# Agent Coordination\n\n{agents_content}"

        # Add always skills to system prompt (these are loaded automatically)
        always_skills = self.skills.get_always_skills()
        if always_skills:
            always_content = self.skills.load_skills_for_context(always_skills)
            if always_content:
                system_prompt += f"\n\n# Active Skills (Always Loaded)\n\n{always_content}"

        # Add skills summary with instructions
        # This follows nanobot's progressive disclosure principle:
        # Only metadata (name + description) is loaded into context
        # Full skill content is loaded on-demand when LLM decides to use it
        skills_summary = self.skills.build_skills_summary()
        if skills_summary:
            system_prompt += f"\n\n{SKILLS_INSTRUCTION}{skills_summary}\n\n---\n\nWhen you need to perform a task, first check if there's a relevant skill above. If so, read its SKILL.md file using the file_read tool to learn how to use it."

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
