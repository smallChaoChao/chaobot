"""Agent runner for CLI interaction."""

import asyncio
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner

from chaobot.agent.loop import AgentLoop
from chaobot.agent.memory import MemoryManager
from chaobot.config.manager import ConfigManager

console = Console()


class AgentRunner:
    """Runner for agent interactions."""

    def __init__(
        self,
        show_logs: bool = False,
        use_markdown: bool = True,
        stream: bool = True,
        session_id: str | None = None
    ) -> None:
        """Initialize runner.

        Args:
            show_logs: Whether to show runtime logs
            use_markdown: Whether to render markdown output
            stream: Whether to use streaming response
            session_id: Session ID for conversation history
        """
        self.show_logs = show_logs
        self.use_markdown = use_markdown
        self.stream = stream
        self.session_id = session_id or "default"
        self.config = ConfigManager().load()
        self.loop = AgentLoop(self.config)
        self.memory = MemoryManager(self.config)

    def run_single(self, message: str) -> None:
        """Run a single message and exit.

        Args:
            message: Message to send
        """
        if self.stream:
            asyncio.run(self._run_single_stream(message))
        else:
            response = asyncio.run(self.loop.run(message, session_id=self.session_id))
            self._display_response(response)

    async def _run_single_stream(self, message: str) -> None:
        """Run a single message with streaming.

        Args:
            message: Message to send
        """
        console.print("[bold blue]chaobot:[/bold blue] ", end="")
        content = ""
        async for chunk in self.loop.run_stream(message, session_id=self.session_id):
            content += chunk
            console.print(chunk, end="")
        console.print()  # New line at end
        
        # Save to memory
        await self.memory.save_history(self.session_id, [
            {"role": "user", "content": message},
            {"role": "assistant", "content": content}
        ])

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
                    asyncio.run(self._run_interactive_stream(user_input))
                else:
                    with console.status("[bold blue]Thinking...[/bold blue]"):
                        response = asyncio.run(self.loop.run(user_input, session_id=self.session_id))
                    self._display_response(response)

            except (EOFError, KeyboardInterrupt):
                console.print("\nGoodbye! 👋")
                break

    async def _run_interactive_stream(self, message: str) -> None:
        """Run interactive message with streaming.

        Args:
            message: Message to send
        """
        console.print("[bold blue]chaobot:[/bold blue] ", end="")
        content = ""
        async for chunk in self.loop.run_stream(message, session_id=self.session_id):
            console.print(chunk, end="")
            content += chunk
        console.print()  # New line at end
        
        # Save to memory
        await self.memory.save_history(self.session_id, [
            {"role": "user", "content": message},
            {"role": "assistant", "content": content}
        ])

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

        if self.show_logs and "logs" in response:
            for log in response["logs"]:
                console.print(f"[dim]{log}[/dim]")
