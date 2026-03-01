"""User confirmation mechanism for sensitive operations."""

from dataclasses import dataclass
from typing import Callable, Awaitable
import asyncio


@dataclass
class ConfirmationResult:
    """Result of a confirmation request."""

    approved: bool
    message: str = ""


ConfirmationCallback = Callable[[str, dict], Awaitable[ConfirmationResult]]


class ConfirmationManager:
    """Manages user confirmations for sensitive operations."""

    _instance = None
    _callback: ConfirmationCallback | None = None

    # Tools that require confirmation
    SENSITIVE_TOOLS = {
        "shell": True,
        "file_write": True,
        "file_edit": True,
        "browser_navigate": False,  # Can be enabled if needed
    }

    # Dangerous command patterns that always require confirmation
    DANGEROUS_PATTERNS = [
        "rm -rf",
        "rm -fr",
        "rm -r /",
        "rm -rf /",
        "mkfs",
        "dd if=",
        "> /dev/sda",
        ":(){ :|:& };:",  # Fork bomb
        "chmod -R 777 /",
        "chown -R",
        "mv /* ",
        "mv / ",
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set_callback(self, callback: ConfirmationCallback) -> None:
        """Set the confirmation callback.

        Args:
            callback: Async function that takes (tool_name, arguments) and returns ConfirmationResult
        """
        self._callback = callback

    def requires_confirmation(self, tool_name: str, arguments: dict) -> bool:
        """Check if a tool execution requires user confirmation.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            True if confirmation is required
        """
        # Check if tool is in sensitive list
        if tool_name not in self.SENSITIVE_TOOLS:
            return False

        # For shell commands, check for dangerous patterns
        if tool_name == "shell" and "command" in arguments:
            cmd = arguments["command"].strip().lower()
            for pattern in self.DANGEROUS_PATTERNS:
                if pattern.lower() in cmd:
                    return True

            # Check for rm commands (without -rf /)
            if cmd.startswith("rm ") and "-f" in cmd:
                return True

            # Check for sudo
            if cmd.startswith("sudo "):
                return True

        # For file operations, check if modifying existing files
        if tool_name in ("file_write", "file_edit") and "path" in arguments:
            import os
            path = arguments["path"]
            if os.path.exists(path):
                return True

        return False

    async def confirm(self, tool_name: str, arguments: dict) -> ConfirmationResult:
        """Request user confirmation.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Confirmation result
        """
        if not self.requires_confirmation(tool_name, arguments):
            return ConfirmationResult(approved=True)

        if self._callback is None:
            # No callback set, auto-approve for non-dangerous operations
            # But log a warning
            return ConfirmationResult(
                approved=True,
                message=f"Warning: {tool_name} executed without confirmation callback"
            )

        try:
            result = await self._callback(tool_name, arguments)
            return result
        except Exception as e:
            return ConfirmationResult(
                approved=False,
                message=f"Confirmation failed: {str(e)}"
            )


async def console_confirmation_callback(tool_name: str, arguments: dict) -> ConfirmationResult:
    """Default console-based confirmation callback.

    Args:
        tool_name: Name of the tool
        arguments: Tool arguments

    Returns:
        Confirmation result
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm

    console = Console()

    # Format the operation description
    if tool_name == "shell" and "command" in arguments:
        description = f"Execute command: {arguments['command']}"
    elif tool_name in ("file_write", "file_edit") and "path" in arguments:
        description = f"Modify file: {arguments['path']}"
    else:
        description = f"Execute {tool_name} with args: {arguments}"

    # Show confirmation prompt
    console.print(Panel(
        f"[bold yellow]⚠️  Sensitive Operation[/bold yellow]\n\n"
        f"{description}\n\n"
        f"Do you want to proceed?",
        border_style="yellow"
    ))

    try:
        approved = await asyncio.to_thread(Confirm.ask, "Confirm")
        return ConfirmationResult(
            approved=approved,
            message="Approved by user" if approved else "Rejected by user"
        )
    except Exception as e:
        return ConfirmationResult(
            approved=False,
            message=f"Confirmation error: {str(e)}"
        )
