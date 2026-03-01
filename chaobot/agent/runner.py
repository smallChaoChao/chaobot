"""Agent runner for CLI interaction."""

import asyncio
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from chaobot.agent.loop import AgentLoop
from chaobot.agent.memory import MemoryManager
from chaobot.agent.tools.confirmation import ConfirmationManager, console_confirmation_callback
from chaobot.config.manager import ConfigManager
from chaobot.utils.progress import ProgressTracker, SimpleProgressTracker

console = Console()


# Skill detection patterns (tool/command -> skill name)
SKILL_PATTERNS = {
    "weather": ["wttr.in", "weather"],
    "github": ["gh ", "github"],
    "memory": ["MEMORY.md", "HISTORY.md"],
    "summarize": ["summarize"],
    "tavily-search": ["tavily"],
    "skill-vetter": ["vetter"],
}


def detect_skill(tool_name: str, arguments: dict[str, Any]) -> str | None:
    """Detect which skill is being used based on tool and arguments.

    Args:
        tool_name: Name of the tool being called
        arguments: Tool arguments

    Returns:
        Skill name if detected, None otherwise
    """
    # Check command argument for shell tool
    if tool_name == "shell" and "command" in arguments:
        cmd = arguments["command"]
        for skill, patterns in SKILL_PATTERNS.items():
            for pattern in patterns:
                if pattern in cmd:
                    return skill

    # Check path argument for file_read tool
    if tool_name == "file_read" and "path" in arguments:
        path = arguments["path"]
        for skill, patterns in SKILL_PATTERNS.items():
            for pattern in patterns:
                if pattern in path:
                    return skill

    return None


class AgentRunner:
    """Runner for agent interactions."""

    def __init__(
        self,
        show_logs: bool = False,
        use_markdown: bool = True,
        stream: bool = True,
        session_id: str | None = None,
        confirm_sensitive: bool = True
    ) -> None:
        """Initialize runner.

        Args:
            show_logs: Whether to show runtime logs
            use_markdown: Whether to render markdown output
            stream: Whether to use streaming response
            session_id: Session ID for conversation history
            confirm_sensitive: Whether to confirm sensitive operations
        """
        self.show_logs = show_logs
        self.use_markdown = use_markdown
        self.stream = stream
        self.session_id = session_id or "default"
        self.confirm_sensitive = confirm_sensitive
        self.config = ConfigManager().load()
        self.loop = AgentLoop(self.config)
        self.memory = MemoryManager(self.config)

        # Set up confirmation callback for CLI mode
        if confirm_sensitive:
            confirmation_manager = ConfirmationManager()
            confirmation_manager.set_callback(console_confirmation_callback)

    def run_single(self, message: str) -> None:
        """Run a single message and exit.

        Args:
            message: Message to send
        """
        if self.stream:
            # Streaming doesn't support tools yet, fallback to non-streaming
            asyncio.run(self._run_single_with_progress(message))
        else:
            asyncio.run(self._run_single_with_progress(message))

    async def _run_single_with_progress(self, message: str) -> None:
        """Run a single message with progress tracking.

        Args:
            message: Message to send
        """
        async def on_progress(content: str, is_tool_hint: bool) -> None:
            """Handle progress updates."""
            if is_tool_hint and self.show_logs:
                # Tool-related progress - show detailed format
                if content.startswith("Executing "):
                    match = content[len("Executing "):]
                    if "(" in match:
                        name = match.split("(")[0]
                        args_str = match[len(name)+1:-1] if match.endswith(")") else match[len(name)+1:]
                        arguments = {}
                        if args_str:
                            for part in args_str.split(", "):
                                if "=" in part:
                                    k, v = part.split("=", 1)
                                    arguments[k] = v
                        skill = detect_skill(name, arguments)
                        if skill:
                            # Show skill format with FULL arguments when show_logs is True
                            args_display = ", ".join([f"{k}={v}" for k, v in arguments.items()]) if arguments else ""
                            console.print(f"  [dim]↳ skill[{skill}]({name}) -> {args_display}[/dim]" if args_display else f"  [dim]↳ skill[{skill}]({name})[/dim]")
                        else:
                            # Show tool format with FULL arguments when show_logs is True
                            args_display = ", ".join([f"{k}={v}" for k, v in arguments.items()]) if arguments else ""
                            console.print(f"  [dim]↳ tool[{name}] -> {args_display}[/dim]" if args_display else f"  [dim]↳ tool[{name}][/dim]")
            elif self.show_logs:
                # General progress
                console.print(f"[dim]{content}[/dim]")

        response = await self.loop.run(
            message,
            session_id=self.session_id,
            on_progress=on_progress
        )

        # Display response
        self._display_response(response)

    def run_interactive(self) -> None:
        """Run in interactive mode."""
        console.print(Panel.fit(
            "🤖 chaobot interactive mode\n"
            "Type 'exit', 'quit', or press Ctrl+D to exit",
            border_style="blue"
        ))

        while True:
            try:
                user_input = console.input("[bold green]You:[/bold green] ")
                user_input = user_input.strip()

                if not user_input:
                    continue

                if user_input.lower() in ("exit", "quit", "/exit", "/quit", ":q"):
                    console.print("Goodbye! 👋")
                    break

                if self.stream:
                    # For now, use non-streaming with progress tracking
                    asyncio.run(self._run_interactive_with_progress(user_input))
                else:
                    asyncio.run(self._run_interactive_with_progress(user_input))

            except (EOFError, KeyboardInterrupt):
                console.print("\nGoodbye! 👋")
                break

    async def _run_interactive_with_progress(self, message: str) -> None:
        """Run interactive message with progress tracking.

        Args:
            message: User message
        """
        async def on_progress(content: str, is_tool_hint: bool) -> None:
            """Handle progress updates."""
            if is_tool_hint and self.show_logs:
                # Tool-related progress - show detailed format
                if content.startswith("Executing "):
                    match = content[len("Executing "):]
                    if "(" in match:
                        name = match.split("(")[0]
                        args_str = match[len(name)+1:-1] if match.endswith(")") else match[len(name)+1:]
                        arguments = {}
                        if args_str:
                            for part in args_str.split(", "):
                                if "=" in part:
                                    k, v = part.split("=", 1)
                                    arguments[k] = v
                        skill = detect_skill(name, arguments)
                        if skill:
                            # Show skill format with FULL arguments when show_logs is True
                            args_display = ", ".join([f"{k}={v}" for k, v in arguments.items()]) if arguments else ""
                            console.print(f"  [dim]↳ skill[{skill}]({name}) -> {args_display}[/dim]" if args_display else f"  [dim]↳ skill[{skill}]({name})[/dim]")
                        else:
                            # Show tool format with FULL arguments when show_logs is True
                            args_display = ", ".join([f"{k}={v}" for k, v in arguments.items()]) if arguments else ""
                            console.print(f"  [dim]↳ tool[{name}] -> {args_display}[/dim]" if args_display else f"  [dim]↳ tool[{name}][/dim]")
            elif self.show_logs:
                # General progress
                console.print(f"[dim]{content}[/dim]")

        response = await self.loop.run(
            message,
            session_id=self.session_id,
            on_progress=on_progress
        )

        # Display response
        self._display_response(response)

    def _display_response(self, response: dict[str, Any]) -> None:
        """Display agent response.

        Args:
            response: Response dictionary
        """
        content = response.get("content", "")

        if self.use_markdown:
            console.print("[bold blue]chaobot:[/bold blue]")
            console.print(Markdown(content))
        else:
            console.print(f"[bold blue]chaobot:[/bold blue] {content}")

        # Note: When show_logs is True, logs are already printed via on_progress callback
        # So we don't print them again here to avoid duplication

    async def run(
        self,
        message: str,
        on_progress: Any | None = None
    ) -> str:
        """Run the agent and return response text.

        This method is used by the gateway server to process messages.

        Args:
            message: User message
            on_progress: Optional callback for progress updates

        Returns:
            Response text
        """
        response = await self.loop.run(
            message,
            session_id=self.session_id,
            on_progress=on_progress
        )

        return response.get("content", "")
