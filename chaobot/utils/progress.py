"""Progress tracking and display utilities for CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.syntax import Syntax

console = Console()


@dataclass
class ToolCall:
    """Represents a single tool call."""
    id: str
    name: str
    arguments: dict[str, Any]
    status: str = "pending"  # pending, running, success, error
    result: str | None = None
    error: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    skill_name: str | None = None  # Associated skill name

    @property
    def duration_ms(self) -> float | None:
        """Get duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None

    @property
    def display_name(self) -> str:
        """Get display name (skill name if available, otherwise tool name)."""
        if self.skill_name:
            return self.skill_name
        return self.name


@dataclass
class ProgressState:
    """Tracks the current progress state."""
    message: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    current_iteration: int = 0
    max_iterations: int = 0
    is_thinking: bool = False


class ProgressTracker:
    """Tracks and displays agent progress with rich formatting."""

    # Emoji mapping for common tools
    TOOL_ICONS = {
        "web_search": "🔍",
        "search": "🔍",
        "weather": "🌤️",
        "exec": "⚡",
        "shell": "⚡",
        "read_file": "📄",
        "write_file": "📝",
        "edit_file": "✏️",
        "list_dir": "📁",
        "github": "🐙",
        "memory": "🧠",
        "summarize": "📋",
        "tavily_search": "🔎",
        "web_fetch": "🌐",
        "default": "🔧",
    }

    # Skill icons mapping
    SKILL_ICONS = {
        "weather": "🌤️",
        "github": "🐙",
        "memory": "🧠",
        "summarize": "📋",
        "tavily-search": "🔎",
        "skill-vetter": "🛡️",
        "default": "🛠️",
    }

    # Skill detection patterns (tool name -> skill name)
    SKILL_PATTERNS = {
        "weather": ["wttr.in", "weather"],
        "github": ["gh ", "github"],
        "memory": ["MEMORY.md", "HISTORY.md"],
        "summarize": ["summarize"],
        "tavily-search": ["tavily"],
        "skill-vetter": ["vetter"],
    }

    # Status icons
    STATUS_ICONS = {
        "pending": "⏳",
        "running": "🔄",
        "success": "✅",
        "error": "❌",
    }

    def __init__(self, show_details: bool = True, expand_all: bool = False) -> None:
        """Initialize progress tracker.

        Args:
            show_details: Whether to show detailed tool call information
            expand_all: Whether to expand all tool call details by default
        """
        self.show_details = show_details
        self.expand_all = expand_all
        self.state = ProgressState()
        self._live: Live | None = None
        self._spinner = Spinner("dots", text="Thinking...")
        self._expanded: set[str] = set()  # Track expanded tool calls

    def __enter__(self) -> ProgressTracker:
        """Start live display."""
        if self.show_details:
            self._live = Live(
                self._render(),
                console=console,
                refresh_per_second=10,
                transient=False,
            )
            self._live.start()
        return self

    def __exit__(self, *args) -> None:
        """Stop live display."""
        if self._live:
            self._live.stop()
            self._live = None

    def _get_tool_icon(self, name: str) -> str:
        """Get icon for a tool."""
        for key, icon in self.TOOL_ICONS.items():
            if key in name.lower():
                return icon
        return self.TOOL_ICONS["default"]

    def _get_skill_icon(self, skill_name: str | None) -> str:
        """Get icon for a skill."""
        if not skill_name:
            return self.SKILL_ICONS["default"]
        return self.SKILL_ICONS.get(skill_name, self.SKILL_ICONS["default"])

    def _detect_skill(self, tool_name: str, arguments: dict[str, Any]) -> str | None:
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
            for skill, patterns in self.SKILL_PATTERNS.items():
                for pattern in patterns:
                    if pattern in cmd:
                        return skill

        # Check path argument for file_read tool
        if tool_name == "file_read" and "path" in arguments:
            path = arguments["path"]
            for skill, patterns in self.SKILL_PATTERNS.items():
                for pattern in patterns:
                    if pattern in path:
                        return skill

        return None

    def _format_arguments(self, arguments: dict[str, Any]) -> str:
        """Format tool arguments for display."""
        if not arguments:
            return ""

        parts = []
        for key, value in arguments.items():
            val_str = str(value)
            if len(val_str) > 50:
                val_str = val_str[:47] + "..."
            parts.append(f"{key}={val_str}")

        return ", ".join(parts)

    def _format_arguments_json(self, arguments: dict[str, Any]) -> str:
        """Format tool arguments as JSON."""
        try:
            return json.dumps(arguments, ensure_ascii=False, indent=2)
        except Exception:
            return str(arguments)

    def _render_tool_call(self, tc: ToolCall, index: int) -> Panel:
        """Render a single tool call as a panel."""
        # Detect skill if not already set
        if not tc.skill_name:
            tc.skill_name = self._detect_skill(tc.name, tc.arguments)

        # Use skill icon if available, otherwise tool icon
        if tc.skill_name:
            icon = self._get_skill_icon(tc.skill_name)
            display_name = tc.skill_name
        else:
            icon = self._get_tool_icon(tc.name)
            display_name = tc.name

        status_icon = self.STATUS_ICONS.get(tc.status, "❓")

        # Build title
        title_text = Text()
        title_text.append(f"{status_icon} ")
        title_text.append(f"{icon} ")
        title_text.append(display_name, style="cyan bold")

        # Show underlying tool name if using a skill
        if tc.skill_name and tc.skill_name != tc.name:
            title_text.append(f" [{tc.name}]", style="dim")

        # Add arguments summary to title
        if tc.arguments:
            args_str = self._format_arguments(tc.arguments)
            title_text.append(f"({args_str})", style="dim")

        # Add duration
        if tc.duration_ms is not None:
            duration_color = "green" if tc.duration_ms < 1000 else "yellow" if tc.duration_ms < 5000 else "red"
            title_text.append(f" [{tc.duration_ms:.0f}ms]", style=f"dim {duration_color}")

        # Build content
        content_elements = []

        # Tool ID and status
        content_elements.append(Text(f"ID: {tc.id}", style="dim"))
        content_elements.append(Text(f"Status: {tc.status.upper()}", style=self._get_status_color(tc.status)))

        # Arguments section
        if tc.arguments:
            content_elements.append(Text())
            content_elements.append(Text("Arguments:", style="bold"))
            args_json = self._format_arguments_json(tc.arguments)
            content_elements.append(Syntax(args_json, "json", theme="monokai", line_numbers=False))

        # Result or error section
        if tc.status == "success" and tc.result:
            content_elements.append(Text())
            content_elements.append(Text("Result:", style="bold green"))
            # Truncate very long results
            result = tc.result
            if len(result) > 500:
                result = result[:500] + "\n... (truncated)"
            content_elements.append(Text(result, style="green"))
        elif tc.status == "error" and tc.error:
            content_elements.append(Text())
            content_elements.append(Text("Error:", style="bold red"))
            content_elements.append(Text(tc.error, style="red"))

        # Combine content
        content = Group(*content_elements)

        # Determine border style based on status
        border_styles = {
            "pending": "dim",
            "running": "blue",
            "success": "green",
            "error": "red",
        }
        border_style = border_styles.get(tc.status, "white")

        return Panel(
            content,
            title=title_text,
            border_style=border_style,
            padding=(0, 1),
        )

    def _get_status_color(self, status: str) -> str:
        """Get color for status."""
        colors = {
            "pending": "dim",
            "running": "blue",
            "success": "green",
            "error": "red",
        }
        return colors.get(status, "white")

    def _render(self) -> Group:
        """Render the current progress state."""
        elements = []

        # Header with iteration info
        header = Text()
        header.append("🤖 ", style="bold")
        header.append("Agent", style="bold blue")
        if self.state.current_iteration > 0:
            header.append(f" (iteration {self.state.current_iteration}", style="dim")
            if self.state.max_iterations > 0:
                header.append(f"/{self.state.max_iterations}", style="dim")
            header.append(")", style="dim")
        elements.append(header)
        elements.append(Text())

        # Thinking indicator
        if self.state.is_thinking:
            elements.append(Text(f"  {self._spinner}"))
            elements.append(Text())

        # Tool calls as panels
        if self.state.tool_calls:
            for i, tc in enumerate(self.state.tool_calls):
                elements.append(self._render_tool_call(tc, i))
                elements.append(Text())

        return Group(*elements)

    def update(self) -> None:
        """Update the live display."""
        if self._live:
            self._live.update(self._render())

    def start_thinking(self) -> None:
        """Mark agent as thinking."""
        self.state.is_thinking = True
        self.update()

    def stop_thinking(self) -> None:
        """Mark agent as done thinking."""
        self.state.is_thinking = False
        self.update()

    def set_iteration(self, current: int, max_iter: int) -> None:
        """Set current iteration info."""
        self.state.current_iteration = current
        self.state.max_iterations = max_iter
        self.update()

    def add_tool_call(self, tool_call_id: str, name: str, arguments: dict[str, Any]) -> ToolCall:
        """Add a new tool call."""
        import time

        tc = ToolCall(
            id=tool_call_id,
            name=name,
            arguments=arguments,
            status="running",
            start_time=time.time(),
        )
        self.state.tool_calls.append(tc)
        self.state.is_thinking = False
        self.update()
        return tc

    def complete_tool_call(self, tool_call_id: str, result: str | None = None, error: str | None = None) -> None:
        """Mark a tool call as complete."""
        import time

        for tc in self.state.tool_calls:
            if tc.id == tool_call_id:
                tc.end_time = time.time()
                if error:
                    tc.status = "error"
                    tc.error = error
                else:
                    tc.status = "success"
                    tc.result = result
                self.update()
                break

    def print_summary(self) -> None:
        """Print a summary of all tool calls."""
        if not self.state.tool_calls:
            return

        # Count by status
        success_count = sum(1 for tc in self.state.tool_calls if tc.status == "success")
        error_count = sum(1 for tc in self.state.tool_calls if tc.status == "error")
        running_count = sum(1 for tc in self.state.tool_calls if tc.status == "running")

        # Build summary table
        table = Table(title="📊 Skill Calls Summary", show_header=True, header_style="bold")
        table.add_column("Skill", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Duration", justify="right")
        table.add_column("Details", style="dim")

        for tc in self.state.tool_calls:
            # Detect skill if not already set
            if not tc.skill_name:
                tc.skill_name = self._detect_skill(tc.name, tc.arguments)

            status_str = f"{self.STATUS_ICONS.get(tc.status, '❓')} {tc.status.upper()}"
            status_style = self._get_status_color(tc.status)

            duration_str = f"{tc.duration_ms:.0f}ms" if tc.duration_ms else "-"

            details = ""
            if tc.status == "error" and tc.error:
                details = tc.error[:50] + "..." if len(tc.error) > 50 else tc.error
            elif tc.status == "success" and tc.result:
                preview = tc.result[:50].replace("\n", " ")
                details = preview + "..." if len(tc.result) > 50 else preview

            # Use skill name for display
            if tc.skill_name:
                display_icon = self._get_skill_icon(tc.skill_name)
                display_name = tc.skill_name
            else:
                display_icon = self._get_tool_icon(tc.name)
                display_name = tc.name

            table.add_row(
                f"{display_icon} {display_name}",
                Text(status_str, style=status_style),
                duration_str,
                details
            )

        console.print(table)

        # Overall summary
        summary = Text()
        summary.append(f"\nTotal: {len(self.state.tool_calls)} skills | ", style="bold")
        summary.append(f"✅ {success_count} success", style="green" if success_count > 0 else "dim")
        summary.append(" | ")
        summary.append(f"❌ {error_count} failed", style="red" if error_count > 0 else "dim")
        if running_count > 0:
            summary.append(" | ")
            summary.append(f"🔄 {running_count} running", style="blue")
        console.print(summary)
        console.print()


class SimpleProgressTracker:
    """Simple progress tracker for non-interactive mode."""

    # Tool icons
    TOOL_ICONS = {
        "web_search": "🔍",
        "search": "🔍",
        "weather": "🌤️",
        "exec": "⚡",
        "shell": "⚡",
        "read_file": "📄",
        "write_file": "📝",
        "edit_file": "✏️",
        "list_dir": "📁",
        "github": "🐙",
        "memory": "🧠",
        "summarize": "📋",
        "tavily_search": "🔎",
        "web_fetch": "🌐",
        "default": "🔧",
    }

    # Skill icons mapping
    SKILL_ICONS = {
        "weather": "🌤️",
        "github": "🐙",
        "memory": "🧠",
        "summarize": "📋",
        "tavily-search": "🔎",
        "skill-vetter": "🛡️",
        "default": "🛠️",
    }

    # Skill detection patterns
    SKILL_PATTERNS = {
        "weather": ["wttr.in", "weather"],
        "github": ["gh ", "github"],
        "memory": ["MEMORY.md", "HISTORY.md"],
        "summarize": ["summarize"],
        "tavily-search": ["tavily"],
        "skill-vetter": ["vetter"],
    }

    def __init__(self, verbose: bool = False) -> None:
        """Initialize simple tracker.

        Args:
            verbose: Whether to print tool call details
        """
        self.verbose = verbose
        self.tool_calls: list[ToolCall] = []

    def __enter__(self) -> SimpleProgressTracker:
        return self

    def __exit__(self, *args) -> None:
        pass

    def _get_tool_icon(self, name: str) -> str:
        """Get icon for a tool."""
        for key, icon in self.TOOL_ICONS.items():
            if key in name.lower():
                return icon
        return self.TOOL_ICONS["default"]

    def _get_skill_icon(self, skill_name: str | None) -> str:
        """Get icon for a skill."""
        if not skill_name:
            return self.SKILL_ICONS["default"]
        return self.SKILL_ICONS.get(skill_name, self.SKILL_ICONS["default"])

    def _detect_skill(self, tool_name: str, arguments: dict[str, Any]) -> str | None:
        """Detect which skill is being used based on tool and arguments."""
        if tool_name == "shell" and "command" in arguments:
            cmd = arguments["command"]
            for skill, patterns in self.SKILL_PATTERNS.items():
                for pattern in patterns:
                    if pattern in cmd:
                        return skill

        if tool_name == "file_read" and "path" in arguments:
            path = arguments["path"]
            for skill, patterns in self.SKILL_PATTERNS.items():
                for pattern in patterns:
                    if pattern in path:
                        return skill

        return None

    def start_thinking(self) -> None:
        """Mark agent as thinking."""
        if self.verbose:
            console.print("[dim]🤖 Thinking...[/dim]")

    def stop_thinking(self) -> None:
        """Mark agent as done thinking."""
        pass

    def set_iteration(self, current: int, max_iter: int) -> None:
        """Set current iteration info."""
        if self.verbose:
            console.print(f"[dim]Iteration {current}/{max_iter}[/dim]")

    def add_tool_call(self, tool_call_id: str, name: str, arguments: dict[str, Any]) -> ToolCall:
        """Add a new tool call."""
        import time

        # Detect skill
        skill_name = self._detect_skill(name, arguments)

        tc = ToolCall(
            id=tool_call_id,
            name=name,
            arguments=arguments,
            status="running",
            start_time=time.time(),
            skill_name=skill_name,
        )
        self.tool_calls.append(tc)

        if self.verbose:
            if skill_name:
                icon = self._get_skill_icon(skill_name)
                display_name = skill_name
            else:
                icon = self._get_tool_icon(name)
                display_name = name
            args_str = json.dumps(arguments, ensure_ascii=False)
            if len(args_str) > 60:
                args_str = args_str[:57] + "..."
            console.print(f"  [dim]→ {icon} {display_name}({args_str})[/dim]")

        return tc

    def complete_tool_call(self, tool_call_id: str, result: str | None = None, error: str | None = None) -> None:
        """Mark a tool call as complete."""
        import time

        for tc in self.tool_calls:
            if tc.id == tool_call_id:
                tc.end_time = time.time()
                # Determine display name
                if tc.skill_name:
                    icon = self._get_skill_icon(tc.skill_name)
                    display_name = tc.skill_name
                else:
                    icon = self._get_tool_icon(tc.name)
                    display_name = tc.name

                if error:
                    tc.status = "error"
                    tc.error = error
                    if self.verbose:
                        console.print(f"  [red]✗ {icon} {display_name} failed: {error[:100]}[/red]")
                else:
                    tc.status = "success"
                    tc.result = result
                    if self.verbose:
                        duration = tc.duration_ms
                        duration_str = f" ({duration:.0f}ms)" if duration else ""
                        result_preview = ""
                        if result:
                            preview = str(result)[:40].replace("\n", " ")
                            result_preview = f" → {preview}..." if len(str(result)) > 40 else f" → {preview}"
                        console.print(f"  [green]✓ {icon} {display_name} complete{duration_str}{result_preview}[/green]")
                break

    def print_summary(self) -> None:
        """Print a summary of all tool calls."""
        if not self.verbose or not self.tool_calls:
            return

        success_count = sum(1 for tc in self.tool_calls if tc.status == "success")
        error_count = sum(1 for tc in self.tool_calls if tc.status == "error")
        running_count = sum(1 for tc in self.tool_calls if tc.status == "running")

        summary = Text()
        summary.append("📊 ", style="bold")
        summary.append("Skill Calls Summary", style="bold")
        summary.append(f": {len(self.tool_calls)} total", style="dim")

        if success_count > 0:
            summary.append(f" | ✅ {success_count} success", style="green")
        if error_count > 0:
            summary.append(f" | ❌ {error_count} failed", style="red")
        if running_count > 0:
            summary.append(f" | 🔄 {running_count} running", style="blue")

        console.print(summary)
