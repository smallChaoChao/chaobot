"""Memory management for conversation history.

This module follows nanobot's pattern for storing memory:
- ~/.chaobot/workspace/memory/MEMORY.md - Long-term memory (markdown)
- ~/.chaobot/workspace/sessions/<session_id>.jsonl - Session history (JSON Lines)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from chaobot.config.schema import Config


class MemoryManager:
    """Manages conversation memory and history."""

    def __init__(self, config: Config) -> None:
        """Initialize memory manager.

        Args:
            config: Application configuration
        """
        self.config = config
        # Follow nanobot's pattern: store in workspace/memory and workspace/sessions
        self.workspace_dir = config.workspace_path
        self.memory_dir = self.workspace_dir / "memory"
        self.sessions_dir = self.workspace_dir / "sessions"
        self._ensure_dirs()
        self._ensure_memory_files()

    def _ensure_dirs(self) -> None:
        """Ensure memory and sessions directories exist."""
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            self.sessions_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            import platform
            if platform.system() == "Darwin":
                raise PermissionError(
                    f"Cannot create memory directory: {self.memory_dir}\n"
                    f"This is likely due to macOS sandbox restrictions.\n"
                    f"Please run: mkdir -p {self.memory_dir} {self.sessions_dir}\n"
                    f"And remove quarantine attribute if needed: "
                    f"xattr -d com.apple.quarantine {self.workspace_dir}"
                ) from e
            raise

    def _ensure_memory_files(self) -> None:
        """Ensure MEMORY.md and HISTORY.md files exist."""
        memory_file = self.memory_dir / "MEMORY.md"
        history_file = self.memory_dir / "HISTORY.md"

        if not memory_file.exists():
            memory_file.write_text(self._get_default_memory_md())

        if not history_file.exists():
            history_file.write_text(self._get_default_history_md())

    def _get_default_memory_md(self) -> str:
        """Get default MEMORY.md content."""
        return """# Long-term Memory

This file stores important information that should persist across sessions.

## User Information

(Important facts about the user)

## Preferences

(User preferences learned over time)

## Project Context

(Information about ongoing projects)

## Important Notes

(Things to remember)

---

*This file is automatically updated by chaobot when important information should be remembered.*
"""

    def _get_default_history_md(self) -> str:
        """Get default HISTORY.md content."""
        return """# Conversation History

This file stores the history of conversations.

---

*This file is managed by chaobot.*
"""

    async def load_history(self, session_id: str) -> list[dict[str, Any]]:
        """Load conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of messages
        """
        session_file = self.sessions_dir / f"{session_id}.jsonl"

        if not session_file.exists():
            return []

        messages = []
        try:
            with open(session_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        # Skip metadata lines
                        if data.get("_type") == "metadata":
                            continue
                        # Extract message fields
                        if "role" in data and "content" in data:
                            msg: dict[str, Any] = {
                                "role": data["role"],
                                "content": data["content"]
                            }
                            # Preserve tool call fields for API compatibility
                            if "tool_calls" in data:
                                msg["tool_calls"] = data["tool_calls"]
                            if "tool_call_id" in data:
                                msg["tool_call_id"] = data["tool_call_id"]
                            if "name" in data:
                                msg["name"] = data["name"]
                            messages.append(msg)
                    except json.JSONDecodeError:
                        continue
        except IOError:
            return []

        return messages

    async def save_history(
        self,
        session_id: str,
        messages: list[dict[str, Any]]
    ) -> None:
        """Save conversation history for a session.

        Args:
            session_id: Session identifier
            messages: Messages to save
        """
        session_file = self.sessions_dir / f"{session_id}.jsonl"

        # Simplify messages for storage - only keep user/assistant pairs
        # Skip tool messages and intermediate assistant messages with tool_calls
        simplified_messages = self._simplify_messages(messages)

        # Filter out error messages
        filtered_messages = self._filter_error_messages(simplified_messages)

        # Limit history size (keep last 20 messages)
        filtered_messages = filtered_messages[-20:]

        # Write as JSON Lines format (similar to nanobot)
        lines = []

        # Add metadata line
        metadata = {
            "_type": "metadata",
            "key": f"cli:{session_id}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": len(filtered_messages)
        }
        lines.append(json.dumps(metadata, ensure_ascii=False))

        # Add message lines
        for msg in filtered_messages:
            line: dict[str, Any] = {
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "timestamp": datetime.now().isoformat()
            }
            # Preserve tool call fields
            if "tool_calls" in msg:
                line["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg:
                line["tool_call_id"] = msg["tool_call_id"]
            if "name" in msg:
                line["name"] = msg["name"]
            lines.append(json.dumps(line, ensure_ascii=False))

        with open(session_file, "w") as f:
            f.write("\n".join(lines) + "\n")

    def _simplify_messages(
        self,
        messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Simplify messages for storage.

        Keep only the final user/assistant conversation pairs,
        skipping tool calls and intermediate steps.

        Args:
            messages: Raw messages

        Returns:
            Simplified messages
        """
        simplified = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls")

            # Skip system messages
            if role == "system":
                continue

            # Skip tool messages - they're intermediate steps
            if role == "tool":
                continue

            # Skip assistant messages that only contain tool_calls (no content)
            # These are intermediate steps before tool execution
            if role == "assistant" and tool_calls and not content:
                continue

            # Keep user messages and final assistant responses
            if role in ("user", "assistant"):
                # For assistant messages, don't save tool_calls to history
                # They'll be reconstructed from context if needed
                clean_msg: dict[str, Any] = {
                    "role": role,
                    "content": content
                }
                simplified.append(clean_msg)

        return simplified

    def _filter_error_messages(
        self,
        messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Filter out error messages that shouldn't be saved to history.

        Args:
            messages: List of messages

        Returns:
            Filtered list of messages
        """
        filtered = []
        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "")

            # Skip error messages from assistant
            if role == "assistant" and content:
                # Skip HTTP error responses
                if content.startswith("HTTP error"):
                    continue
                # Skip "No API key configured" errors
                if content.startswith("Error: No API key configured"):
                    continue
                # Skip generic error prefix
                if content.startswith("Error: ") and len(content) < 200:
                    continue

            filtered.append(msg)

        return filtered

    async def clear_history(self, session_id: str) -> None:
        """Clear conversation history for a session.

        Args:
            session_id: Session identifier
        """
        session_file = self.sessions_dir / f"{session_id}.jsonl"

        if session_file.exists():
            session_file.unlink()

    def get_all_sessions(self) -> list[str]:
        """Get all session IDs.

        Returns:
            List of session IDs
        """
        sessions = []
        for file in self.sessions_dir.glob("*.jsonl"):
            sessions.append(file.stem)
        return sessions

    def get_memory_file_path(self) -> Path:
        """Get the path to MEMORY.md file.

        Returns:
            Path to MEMORY.md
        """
        return self.memory_dir / "MEMORY.md"

    def get_history_file_path(self) -> Path:
        """Get the path to HISTORY.md file.

        Returns:
            Path to HISTORY.md
        """
        return self.memory_dir / "HISTORY.md"
