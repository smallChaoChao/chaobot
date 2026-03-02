"""Heartbeat monitor for keeping connections alive and periodic tasks."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from chaobot.config.schema import Config


class HeartbeatMonitor:
    """Monitors and maintains agent connections.

    Features:
    - Keep-alive signals for long-running connections
    - Periodic task execution from HEARTBEAT.md
    - Virtual tool calls to prevent timeout
    """

    def __init__(
        self,
        config: Config,
        interval: int = 1800,
        on_heartbeat: Optional[Callable[[], Any]] = None,
    ) -> None:
        """Initialize heartbeat monitor.

        Args:
            config: Application configuration
            interval: Heartbeat interval in seconds (default: 30 minutes)
            on_heartbeat: Optional callback for heartbeat events
        """
        self.config = config
        self.heartbeat_file = config.workspace_path / "HEARTBEAT.md"
        self.interval = interval
        self.on_heartbeat = on_heartbeat
        self._running = False
        self._last_heartbeat: Optional[datetime] = None

    async def start(self) -> None:
        """Start monitoring."""
        self._running = True
        console_print = self._get_print_func()

        console_print(f"[dim]Heartbeat started with interval {self.interval}s[/dim]")

        while self._running:
            try:
                await self._check_heartbeat()
                self._last_heartbeat = datetime.now()

                if self.on_heartbeat:
                    await self._safe_callback()

            except Exception as e:
                console_print(f"[red]Heartbeat error: {e}[/red]")

            await asyncio.sleep(self.interval)

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False

    async def _safe_callback(self) -> None:
        """Safely execute heartbeat callback."""
        try:
            if asyncio.iscoroutinefunction(self.on_heartbeat):
                await self.on_heartbeat()
            elif self.on_heartbeat:
                self.on_heartbeat()
        except Exception as e:
            print(f"Heartbeat callback error: {e}")

    async def _check_heartbeat(self) -> None:
        """Check heartbeat file for tasks."""
        if not self.heartbeat_file.exists():
            return

        content = self.heartbeat_file.read_text(encoding="utf-8")
        tasks = self._parse_tasks(content)

        for task in tasks:
            if not task.get("done", False):
                await self._execute_task(task)

    def _parse_tasks(self, content: str) -> list[dict[str, Any]]:
        """Parse tasks from markdown content.

        Args:
            content: Markdown content

        Returns:
            List of tasks
        """
        tasks = []

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("- [ ]") or line.startswith("- [x]"):
                done = line.startswith("- [x]")
                task_text = line[5:].strip()
                tasks.append({
                    "text": task_text,
                    "done": done,
                    "created_at": datetime.now().isoformat(),
                })

        return tasks

    async def _execute_task(self, task: dict[str, Any]) -> None:
        """Execute a task.

        Args:
            task: Task dictionary
        """
        console_print = self._get_print_func()
        console_print(f"[dim]Executing heartbeat task: {task.get('text', '')}[/dim]")

    def _get_print_func(self) -> Callable[[str], None]:
        """Get print function with rich support."""
        try:
            from rich.console import Console
            console = Console()
            return console.print
        except ImportError:
            return print

    @property
    def status(self) -> dict[str, Any]:
        """Get heartbeat status."""
        return {
            "running": self._running,
            "interval": self.interval,
            "last_heartbeat": self._last_heartbeat.isoformat() if self._last_heartbeat else None,
        }


class VirtualHeartbeat:
    """Virtual tool-call heartbeat for keeping connections alive.

    This sends periodic virtual tool calls to prevent connection timeouts
    during long-running agent operations.
    """

    def __init__(
        self,
        interval: int = 30,
        max_idle: int = 300,
    ) -> None:
        """Initialize virtual heartbeat.

        Args:
            interval: Check interval in seconds
            max_idle: Maximum idle time before sending heartbeat
        """
        self.interval = interval
        self.max_idle = max_idle
        self._last_activity: Optional[datetime] = None
        self._running = False

    def touch(self) -> None:
        """Update last activity timestamp."""
        self._last_activity = datetime.now()

    async def start(self) -> None:
        """Start virtual heartbeat monitoring."""
        self._running = True
        self.touch()

        while self._running:
            await asyncio.sleep(self.interval)

            if self._is_idle_too_long():
                await self._send_heartbeat()

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False

    def _is_idle_too_long(self) -> bool:
        """Check if idle time exceeds threshold."""
        if not self._last_activity:
            return False

        elapsed = (datetime.now() - self._last_activity).total_seconds()
        return elapsed > self.max_idle

    async def _send_heartbeat(self) -> None:
        """Send a virtual heartbeat signal."""
        self.touch()
