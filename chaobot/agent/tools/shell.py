"""Shell command execution tool."""

import asyncio
import shlex
from typing import Any

from chaobot.agent.tools.base import BaseTool, ToolResult


class ShellTool(BaseTool):
    """Execute shell commands."""

    name = "shell"
    description = "Execute a shell command and return the output"
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute"
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 60)",
                "default": 60
            }
        },
        "required": ["command"]
    }

    # Dangerous commands/patterns to block
    DANGEROUS_PATTERNS = [
        "rm -rf /", "rm -rf /*", "rm -rf ~", "rm -rf ~/*",
        "> /dev/sda", "> /dev/hda", "> /dev/null",
        "mkfs", "mkfs.ext", "mkfs.xfs", "mkfs.btrfs",
        "dd if=/dev/zero", "dd if=/dev/random",
        ":(){ :|:& };:",  # Fork bomb
        "curl | sh", "curl | bash", "wget | sh", "wget | bash",
        "python -m http.server & rm -rf", "python3 -m http.server & rm -rf",
    ]

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute shell command securely.

        Args:
            **kwargs: Must contain 'command', optionally 'timeout'

        Returns:
            Tool execution result
        """
        command = kwargs.get("command", "").strip()
        timeout = kwargs.get("timeout", 60)

        if not command:
            return ToolResult(
                success=False,
                content="No command provided"
            )

        # Security check: block dangerous patterns
        if self.config.security.confirm_destructive_actions:
            cmd_lower = command.lower()
            for pattern in self.DANGEROUS_PATTERNS:
                if pattern.lower() in cmd_lower:
                    return ToolResult(
                        success=False,
                        content=f"Security: Refused to execute potentially dangerous command containing '{pattern}'"
                    )

        try:
            # Parse command safely using shlex
            try:
                args = shlex.split(command)
            except ValueError as e:
                return ToolResult(
                    success=False,
                    content=f"Invalid command syntax: {e}"
                )

            if not args:
                return ToolResult(
                    success=False,
                    content="Empty command after parsing"
                )

            # Check blocked commands
            if self.config.security.blocked_commands:
                if args[0] in self.config.security.blocked_commands:
                    return ToolResult(
                        success=False,
                        content=f"Command '{args[0]}' is blocked by configuration"
                    )

            # Check allowed commands (if whitelist is configured)
            if self.config.security.allowed_commands:
                if args[0] not in self.config.security.allowed_commands:
                    return ToolResult(
                        success=False,
                        content=f"Command '{args[0]}' is not in the allowed commands list"
                    )

            # Execute command using exec (safer than shell)
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    content=f"Command timed out after {timeout} seconds"
                )

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            if process.returncode == 0:
                return ToolResult(
                    success=True,
                    content=output or "Command executed successfully (no output)"
                )
            else:
                return ToolResult(
                    success=False,
                    content=f"Exit code {process.returncode}:\n{error or output}"
                )

        except FileNotFoundError:
            return ToolResult(
                success=False,
                content=f"Command not found: {args[0] if 'args' in locals() else 'unknown'}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Error executing command: {e}"
            )
